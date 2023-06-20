import re
import heapq
from ajs_interface import AJSInterface

class AJSEvaluator:
    @staticmethod
    def process_jstack(ajs_data, jstack_index):
        for process_id in ajs_data.process_id_vs_name:
            threads = AJSEvaluator.read_and_filter_threads(ajs_data, jstack_index, process_id)
            AJSEvaluator.process_cpu_consuming_threads(ajs_data, threads)
            AJSEvaluator.match_threads(ajs_data, threads)
            AJSEvaluator.categorize_threads(ajs_data, threads)

    @staticmethod
    def read_and_filter_threads(ajs_data, jstack_index, process_id):
        jstack = AJSInterface.read_jstack(ajs_data, jstack_index, process_id)
        threads = AJSInterface.parse_threads_from_jstack(jstack, process_id)
        threads = AJSEvaluator.filter_threads(ajs_data, threads)
        return threads

    @staticmethod
    def process_cpu_consuming_threads(ajs_data, threads):
        threads_with_cpu_time = AJSEvaluator.attach_cpu_time(threads)
        cpu_consuming_threads = AJSEvaluator.get_cpu_consuming_threads(ajs_data.CPU_CONSUMING_THREADS_PER_JSTACK, threads_with_cpu_time)
        AJSEvaluator.store_cpu_consuming_threads(cpu_consuming_threads, ajs_data)

    @staticmethod
    def match_threads(ajs_data, threads):
        matching_threads_text = AJSEvaluator.give_matching_threads(ajs_data, threads)
        AJSInterface.output_matching_threads(matching_threads_text)

    @staticmethod
    def categorize_threads(ajs_data, threads):
        user_categorized_threads = AJSEvaluator.user_config_categorization(ajs_data, threads)
        state_categorized_threads = AJSEvaluator.thread_state_categorization(user_categorized_threads)
        AJSInterface.output_categorized_threads(state_categorized_threads)

    @staticmethod
    def filter_threads(ajs_data, threads):
        filtered_threads = []
        for thread in threads:
            to_include = True

            for unwanted_token in ajs_data.config["filter_out"]:
                if re.search(unwanted_token, thread.text):
                    to_include = False
                    break

            if to_include:
                filtered_threads.append(thread)

        return filtered_threads

    @staticmethod
    def give_matching_threads(ajs_data, threads):
        tokens = ajs_data.config["tokens"]

        matching_threads = ""
        for thread in threads:
            for token in tokens:
                token_text = token["text"]
                output_all_token_matches = token["output_all_matches"]

                if output_all_token_matches is False and ajs_data.token_frequency[token_text] > 0:
                    break

                if token_text in thread.text:
                    process_id = thread.process_id
                    process_name = ajs_data.process_id_vs_name[process_id]
                    matching_threads += "Process Name: {}, Process Id: {}\n".format(process_name, process_id)
                    matching_threads += thread.text + "\n\n"
                    ajs_data.found_token(token)
        return matching_threads

    @staticmethod
    def user_config_categorization(ajs_data, threads):
        threads_to_return = threads
        
        for thread in threads_to_return:
            for item in ajs_data.config["classification"]:
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
    def store_cpu_consuming_threads(threads, ajs_data):
        ajs_data.cpu_consuming_threads.extend(threads)
