import re
from collections import Counter
from ajs_interface import AJSInterface

class AJSEvaluator:
    @staticmethod
    def process_jstack(ajs_config, ajs_db, jstack_index):
        for process_id in ajs_db.process_id_vs_name:
            AJSEvaluator.output_new_jstack_header(ajs_config, jstack_index, process_id)
            threads = AJSEvaluator.read_and_filter_threads(ajs_config, jstack_index, process_id)
            AJSEvaluator.match_threads(ajs_config, ajs_db, threads)
            AJSEvaluator.classify_threads(ajs_config, threads)
            AJSEvaluator.repetitive_stack_trace(ajs_config, threads)
            AJSEvaluator.store_threads_in_db(ajs_db, threads)

    @staticmethod
    def output_new_jstack_header(ajs_config, jstack_index, process_id):
        matching_is_off = ajs_config.config["tokens"] is None
        classification_is_off = ajs_config.config["classification"] is None
        repetitive_stack_trace_is_off = ajs_config.config["repetitive_stack_trace"] is False

        if classification_is_off and matching_is_off and repetitive_stack_trace_is_off:
            return

        analysis_file_path = ".ajs/analysis.txt"
        new_jstack_header = "JSTACK " + str(jstack_index) + " FOR PROCESS " + str(process_id) + "\n\n\n"
        AJSInterface.append_to_file(analysis_file_path, new_jstack_header)

    @staticmethod
    def output_jstack_comparison_header(ajs_config):
        state_frequency_is_off = ajs_config.config["thread_state_frequency_table"] is False
        cpu_intensive_threads_is_off = ajs_config.config["cpu_intensive_threads"] is False

        if state_frequency_is_off and cpu_intensive_threads_is_off:
            return

        analysis_file_path = ".ajs/analysis.txt"
        new_jstack_header = "JSTACKS COMPARISON\n\n\n"
        AJSInterface.append_to_file(analysis_file_path, new_jstack_header)

    @staticmethod
    def store_threads_in_db(ajs_db, threads):
        state_frequency_dict = {}

        for thread in threads:
            if thread.id not in ajs_db.threads:
                ajs_db.threads[thread.id] = []
            ajs_db.threads[thread.id].append(thread)

            thread_state = thread.thread_state
            if thread_state not in state_frequency_dict:
                state_frequency_dict[thread_state] = 0
            state_frequency_dict[thread_state] += 1

        ajs_db.state_frequency_dicts.append(state_frequency_dict)

    @staticmethod
    def read_and_filter_threads(ajs_config, jstack_index, process_id):
        jstack = AJSInterface.read_jstack(ajs_config, jstack_index, process_id)
        threads = AJSInterface.parse_threads_from_jstack(jstack, process_id)
        threads = AJSEvaluator.filter_threads(ajs_config, threads)
        return list(threads)

    @staticmethod
    def match_threads(ajs_config, ajs_db, threads):
        if ajs_config.config["tokens"] is None:
            return

        matching_threads_text = AJSEvaluator.give_matching_threads(ajs_config, ajs_db, threads)
        AJSInterface.output_matching_threads(matching_threads_text)

    @staticmethod
    def classify_threads(ajs_config, threads):
        if ajs_config.config["classification"] is None:
            return

        AJSEvaluator.thread_state_classification(ajs_config, threads)
        AJSEvaluator.user_config_classification(ajs_config, threads)
        AJSInterface.output_classified_threads(threads)

    @staticmethod
    def repetitive_stack_trace(ajs_config, threads):
        if ajs_config.config["repetitive_stack_trace"] is False:
            return

        stack_traces = []
        for thread in threads:
            stack_trace = thread.text.split("\n", 1)[1]
            stack_traces.append(stack_trace)

        stack_trace_counter = Counter(stack_traces).most_common()

        AJSInterface.output_repetitive_stack_trace(stack_trace_counter)

    @staticmethod
    def filter_threads(ajs_config, threads):
        if ajs_config.config["filter_out"] is None:
            return threads

        filtered_threads = []
        for thread in threads:
            to_include = True

            for unwanted_token in ajs_config.config["filter_out"]:
                if re.search(unwanted_token, thread.text):
                    to_include = False
                    break

            if to_include:
                filtered_threads.append(thread)

        return filtered_threads

    @staticmethod
    def give_matching_threads(ajs_config, ajs_db, threads):
        tokens = ajs_config.config["tokens"]

        matching_threads = "MATCHING THREADS:\n\n"
        for thread in threads:
            for token in tokens:
                token_text = token["text"]
                output_all_token_matches = token["output_all_matches"]

                if output_all_token_matches is False and ajs_db.token_frequency[token_text] > 0:
                    break

                if token_text in thread.text:
                    process_id = thread.process_id
                    process_name = ajs_db.process_id_vs_name[process_id]
                    matching_threads += "Process Name: {}, Process Id: {}\n".format(process_name, process_id)
                    matching_threads += thread.text + "\n\n"
                    ajs_db.found_token(token)
        return str(matching_threads)

    @staticmethod
    def user_config_classification(ajs_config, threads):
        for thread in threads:
            found_tag = False

            for item in ajs_config.config["classification"]:
                tag = item["tag"]
                regex = item["regex"]
                if re.search(regex, thread.text):
                    thread.tags.append(tag)
                    found_tag = True
                    break

            if found_tag is False:
                thread.tags.append("UNCLASSIFIED")

    @staticmethod
    def thread_state_classification(ajs_config, threads):
        for thread in threads:
            for state in ajs_config.thread_states:
                tag = state["tag"]
                regex = state["regex"]
                if re.search(regex, thread.text):
                    thread.tags.append(tag)
                    break

    @staticmethod
    def process_cpu_consuming_threads(ajs_config, ajs_db):
        if ajs_config.config["cpu_intensive_threads"] is False:
            return

        cpu_wise_sorted_thread_indexes = [] 
        
        for thread_id in ajs_db.threads:
            threads_with_thread_id = ajs_db.threads[thread_id]

            if len(threads_with_thread_id) == 1:
                continue

            first_thread = threads_with_thread_id[0]
            last_thread = threads_with_thread_id[-1]

            time = last_thread.cpu - first_thread.cpu
            cpu_wise_sorted_thread_indexes.append({"id": thread_id, "time": time})

        cpu_wise_sorted_thread_indexes.sort(key=lambda thread: thread["time"], reverse=True)

        AJSInterface.output_cpu_consuming_threads(ajs_db, cpu_wise_sorted_thread_indexes)
