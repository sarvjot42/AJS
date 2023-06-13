import re
from qst_utils import QSTUtils
from qst_interface import QSTInterface

# Business logic for qst is stored here
class QSTEvaluator:
    # Match stack frames for tokens
    @staticmethod
    @QSTUtils.benchmark
    def process_cycle(it, tokens, print_all, qst_data, **kwargs):
        log_stats = kwargs["log_stats"]
        for process_id in qst_data.process_id_vs_name:
            QSTUtils.logger(log_stats, "PROCESS {}".format(qst_data.process_id_vs_name[process_id]))
            stack_frames = QSTEvaluator.read_and_filter_stack_frames(it, process_id, qst_data, log_stats=log_stats, label="READ AND FILTER STACK FRAMES")
            QSTEvaluator.find_cpu_consuming_threads(stack_frames, qst_data, log_stats=log_stats, label="FIND CPU CONSUMING THREADS")
            QSTEvaluator.match_stack_frames(stack_frames, tokens, print_all, qst_data, log_stats=log_stats, label="MATCH STACK FRAMES")
            QSTEvaluator.categorize_stack_frames(stack_frames, qst_data, log_stats=log_stats, label="CATEGORIZE STACK FRAMES")

    @staticmethod
    @QSTUtils.benchmark
    def read_and_filter_stack_frames(it, process_id, qst_data, **kwargs):
        stack_frames = QSTInterface.read_jstacks(it, process_id, qst_data)
        stack_frames = QSTEvaluator.filter_stack_frames(stack_frames, qst_data)
        return stack_frames

    @staticmethod
    @QSTUtils.benchmark
    def find_cpu_consuming_threads(stack_frames, qst_data, **kwargs):
        QSTUtils.attach_cpu_time(stack_frames)
        cpu_consuming = QSTUtils.get_cpu_consuming(10, stack_frames)
        QSTUtils.store_cpu_consuming(cpu_consuming, qst_data)

    @staticmethod
    @QSTUtils.benchmark
    def match_stack_frames(stack_frames, tokens, print_all, qst_data, **kwargs):
        matching_frames_text = QSTEvaluator.give_matching_frames(stack_frames, tokens, print_all, qst_data)
        QSTInterface.store_matching_frames(matching_frames_text, qst_data)

    @staticmethod
    @QSTUtils.benchmark
    def categorize_stack_frames(stack_frames, qst_data, **kwargs):
        QSTEvaluator.user_config_categorization(stack_frames, qst_data)
        QSTEvaluator.thread_state_categorization(stack_frames)

    @staticmethod
    def filter_stack_frames(stack_frames, qst_data):
        filtered_stack_frames = []
        for stack_frame in stack_frames:
            to_include = False

            if qst_data.config["include"] is not None:
                for include in qst_data.config["include"]:
                    if re.search(include, stack_frame.text):
                        to_include = True
                        break
            else:
                to_include = True

            for not_include in qst_data.config["not_include"]:
                if re.search(not_include, stack_frame.text):
                    to_include = False
                    break

            if to_include:
                filtered_stack_frames.append(stack_frame)

        return filtered_stack_frames

    @staticmethod
    def give_matching_frames(stack_frames, tokens, print_all, qst_data):
        matching_frames = ""
        for stack_frame in stack_frames:
            for token in tokens:
                if print_all is False and qst_data.found_tokens[token] > 0:
                    break
                if token in stack_frame.text:
                    process_id = stack_frame.process_id
                    process_name = qst_data.process_id_vs_name[process_id]
                    matching_frames += "Process Name: {}, Process Id: {}\n".format(
                        process_name, process_id
                    )
                    matching_frames += stack_frame.text + "\n\n"
                    qst_data.found_token(token)
        return matching_frames

    @staticmethod
    def user_config_categorization(stack_frames, qst_data):
        for stack_frame in stack_frames:
            has_tag = False
            for item in qst_data.config["classification"]:
                if re.search(item["regex"], stack_frame.text):
                    stack_frame.tags.append(item["tag"])
                    has_tag = True
                    break
            if has_tag is False:
                stack_frame.tags.append("UNCLASSIFIED")
        return stack_frames

    @staticmethod
    def thread_state_categorization(stack_frames):
        states = [
            { "regex": ".*RUNNABLE.*", "tag": "RUNNABLE" }, 
            { "regex": ".*TIMED_WAITING.*", "tag": "TIMED_WAITING" },
            { "regex": ".*WAITING.*", "tag": "WAITING" },
            { "regex": ".*BLOCKED.*", "tag": "BLOCKED" }
        ]

        categorized_stack_frames = {}

        for stack_frame in stack_frames:
            for state in states:
                if re.search(state["regex"], stack_frame.text):
                    if state["tag"] not in categorized_stack_frames:
                        categorized_stack_frames[state["tag"]] = []
                    categorized_stack_frames[state["tag"]].append(stack_frame)
                    break

        QSTInterface.store_categorized_frames(categorized_stack_frames)
