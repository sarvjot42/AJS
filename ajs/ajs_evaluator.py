import re
from ajs_interface import AJSInterface

class AJSEvaluator:
    @staticmethod
    def process_jstack(ajs_config, ajs_db, jstack_index):
        for process_id in ajs_db.process_id_vs_name:
            threads = AJSEvaluator.read_and_filter_threads(ajs_config, jstack_index, process_id)
            AJSEvaluator.match_threads(ajs_config, ajs_db, threads)
            final_threads = AJSEvaluator.categorize_threads(ajs_config, threads)
            AJSEvaluator.store_threads_in_db(ajs_db, final_threads)

    @staticmethod
    def store_threads_in_db(ajs_db, threads):
        for thread in threads:
            if thread.id not in ajs_db.threads:
                ajs_db.threads[thread.id] = []
            ajs_db.threads[thread.id].append(thread)

    @staticmethod
    def read_and_filter_threads(ajs_config, jstack_index, process_id):
        jstack = AJSInterface.read_jstack(ajs_config, jstack_index, process_id)
        threads = AJSInterface.parse_threads_from_jstack(jstack, process_id)
        threads = AJSEvaluator.filter_threads(ajs_config, threads)
        return threads

    @staticmethod
    def match_threads(ajs_config, ajs_db, threads):
        if ajs_config.config["tokens"] is None:
            return

        matching_threads_text = AJSEvaluator.give_matching_threads(ajs_config, ajs_db, threads)
        AJSInterface.output_matching_threads(matching_threads_text)

    @staticmethod
    def categorize_threads(ajs_config, threads):
        if ajs_config.config["classification"] is None:
            return threads

        user_categorized_threads = AJSEvaluator.user_config_categorization(ajs_config, threads)
        state_categorized_threads = AJSEvaluator.thread_state_categorization(user_categorized_threads)
        AJSInterface.output_categorized_threads(state_categorized_threads)
        return state_categorized_threads

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

        matching_threads = ""
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
        return matching_threads

    @staticmethod
    def user_config_categorization(ajs_config, threads):
        threads_to_return = threads
        
        for thread in threads_to_return:
            for item in ajs_config.config["classification"]:
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
