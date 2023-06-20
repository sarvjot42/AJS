import re
import heapq
from qst_interface import QSTInterface

class QSTEvaluator:
    @staticmethod
    def process_jstack(qst_data, tokens, print_all_matches, jstack_index):
        for process_id in qst_data.process_id_vs_name:
            threads = QSTEvaluator.read_and_filter_threads(qst_data, jstack_index, process_id)
            QSTEvaluator.process_cpu_consuming_threads(qst_data, threads)
            QSTEvaluator.match_threads(qst_data, threads, tokens, print_all_matches)
            QSTEvaluator.categorize_threads(qst_data, threads)

    @staticmethod
    def read_and_filter_threads(qst_data, jstack_index, process_id):
        jstack = QSTInterface.read_jstack(qst_data, jstack_index, process_id)
        threads = QSTInterface.parse_threads_from_jstack(jstack, process_id)
        threads = QSTEvaluator.filter_threads(qst_data, threads)
        return threads

    @staticmethod
    def process_cpu_consuming_threads(qst_data, threads):
        threads_with_cpu_time = QSTEvaluator.attach_cpu_time(threads)
        cpu_consuming_threads = QSTEvaluator.get_cpu_consuming_threads(qst_data.CPU_CONSUMING_THREADS_PER_JSTACK, threads_with_cpu_time)
        QSTEvaluator.store_cpu_consuming_threads(cpu_consuming_threads, qst_data)

    @staticmethod
    def match_threads(qst_data, threads, tokens, print_all_matches):
        matching_threads_text = QSTEvaluator.give_matching_threads(qst_data, threads, tokens, print_all_matches)
        QSTInterface.output_matching_threads(matching_threads_text)

    @staticmethod
    def categorize_threads(qst_data, threads):
        user_categorized_threads = QSTEvaluator.user_config_categorization(qst_data, threads)
        state_categorized_threads = QSTEvaluator.thread_state_categorization(user_categorized_threads)
        QSTInterface.output_categorized_threads(state_categorized_threads)

    @staticmethod
    def filter_threads(qst_data, threads):
        filtered_threads = []
        for thread in threads:
            to_include = False

            if qst_data.config["include"] is not None:
                for include in qst_data.config["include"]:
                    if re.search(include, thread.text):
                        to_include = True
                        break
            else:
                to_include = True

            for not_include in qst_data.config["not_include"]:
                if re.search(not_include, thread.text):
                    to_include = False
                    break

            if to_include:
                filtered_threads.append(thread)

        return filtered_threads

    @staticmethod
    def give_matching_threads(qst_data, threads, tokens, print_all_matches):
        matching_threads = ""
        for thread in threads:
            for token in tokens:
                if print_all_matches is False and qst_data.token_frequency[token] > 0:
                    break
                if token in thread.text:
                    process_id = thread.process_id
                    process_name = qst_data.process_id_vs_name[process_id]
                    matching_threads += "Process Name: {}, Process Id: {}\n".format(
                        process_name, process_id
                    )
                    matching_threads += thread.text + "\n\n"
                    qst_data.found_token(token)
        return matching_threads

    @staticmethod
    def user_config_categorization(qst_data, threads):
        threads_to_return = threads
        
        for thread in threads_to_return:
            for item in qst_data.config["classification"]:
                tag = item["tag"]
                regex = item["regex"]
                if re.search(regex, thread.text):
                    thread.tags.append(tag)
                    break

            if len(thread.tags) == 0:
                thread.tags.append("UNCLASSIFIED")

        return threads_to_return

    @staticmethod
    def thread_state_categorization(threads):
        states = [
            { "regex": ".*RUNNABLE.*", "tag": "RUNNABLE" }, 
            { "regex": ".*TIMED_WAITING.*", "tag": "TIMED_WAITING" },
            { "regex": ".*WAITING.*", "tag": "WAITING" },
            { "regex": ".*BLOCKED.*", "tag": "BLOCKED" }
        ]

        categorized_threads = {}

        for thread in threads:
            for state in states:
                tag = state["tag"]
                regex = state["regex"]
                if re.search(regex, thread.text):
                    if tag not in categorized_threads:
                        categorized_threads[tag] = []
                    categorized_threads[tag].append(thread)
                    break

        return categorized_threads

    @staticmethod
    def attach_cpu_time(threads):
        threads_to_return = threads

        for thread in threads_to_return:
            pattern = r'cpu=(\d+(\.\d+)?)ms'
            cpu_time_match = re.search(pattern, thread.text)

            if cpu_time_match:
                cpu_time = float(cpu_time_match.group(1))
                thread.cpu_time = cpu_time

        return threads_to_return

    @staticmethod
    def get_cpu_consuming_threads(number_of_threads_required, threads):
        slowest_threads = heapq.nlargest(number_of_threads_required, threads, key=lambda thread: thread.cpu_time)
        return slowest_threads

    @staticmethod
    def store_cpu_consuming_threads(threads, qst_data):
        qst_data.cpu_consuming_threads.extend(threads)
