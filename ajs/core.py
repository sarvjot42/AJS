import os
import re
import time
from utils import Utils
from schema import Thread
from collections import Counter
from connectors import Connectors

class Core:
    @staticmethod 
    @Utils.benchmark("jstack file input")
    def handle_jstack_file_input(config, db):
        jstack_file_path = config.jstack_file_path

        if jstack_file_path is None:
            exit("\nNo jstack file path provided in config file")

        if not os.path.exists(jstack_file_path):
            exit("\nInvalid jstack file path provided in config file")

        db.add_process("unknown_process_id", "unknown_process")
        num_jstacks = Connectors.parse_jstack_file(config, jstack_file_path)
        return num_jstacks

    @staticmethod 
    @Utils.benchmark("jstack generation")
    def handle_jstack_generation(config, db):
        num_jstacks = config.num_jstacks
        delay_bw_jstacks = config.delay_bw_jstacks

        Connectors.get_java_processes(db)

        for jstack_index in range(num_jstacks):
            for process_id in db.process_id_vs_name:
                jstack = Connectors.get_jstack_of_java_process(process_id)
                Connectors.output_jstack(config, jstack_index, jstack, process_id)

            if jstack_index != num_jstacks - 1:
                time.sleep(delay_bw_jstacks / 1000)

    @staticmethod
    @Utils.benchmark("analyse individual jstack")
    def analyse_jstacks(config, db, jstack_index):
        for process_id in db.process_id_vs_name:
            Connectors.output_new_jstack_header(config, jstack_index, process_id)

            threads = Core.read_and_filter_threads(config, jstack_index, process_id)
            Core.match_threads(config, db, threads)
            Core.classify_threads(config, threads)
            Core.repetitive_stack_trace(config, threads)

            Connectors.store_threads_in_db(db, threads)

    @staticmethod
    def read_and_filter_threads(config, jstack_index, process_id):
        jstack = Connectors.read_jstack(config, jstack_index, process_id)
        threads = Core.parse_threads_from_jstack(jstack, process_id)
        threads = Core.filter_threads(config, threads)
        return threads

    @staticmethod
    def parse_threads_from_jstack(jstack, process_id):
        split_by_empty_line = jstack.split("\n\n")
        remove_non_threads = [thread for thread in split_by_empty_line if "os_prio=" in thread]
        split_clubbed_threads = []

        for thread in remove_non_threads:
            thread_lines = thread.split("\n")
            thread_text = ""
            for line in thread_lines:
                if "os_prio=" in line:
                    if thread_text != "":
                        split_clubbed_threads.append(thread_text)
                        thread_text = ""
                thread_text += line + "\n"
            split_clubbed_threads.append(thread_text.strip("\n"))

        encapsulated_threads = [Thread(text, process_id) for text in split_clubbed_threads]
        id_containing_threads = [thread for thread in encapsulated_threads if thread.id is not -1]

        return id_containing_threads 

    @staticmethod
    def filter_threads(config, threads):
        if config.filter_out is None:
            return threads

        filtered_threads = []
        for thread in threads:
            to_include = True

            for unwanted_token in config.filter_out:
                if re.search(unwanted_token, thread.text):
                    to_include = False
                    break

            if to_include:
                filtered_threads.append(thread)

        return filtered_threads

    @staticmethod
    def match_threads(config, db, threads):
        if config.tokens is None:
            return

        matching_threads_text = Core.give_matching_threads(config, db, threads)
        Connectors.output_matching_threads(matching_threads_text)

    @staticmethod
    def give_matching_threads(config, db, threads):
        tokens = config.tokens

        matching_threads = "MATCHING THREADS"
        matching_threads = Utils.borderify_text(matching_threads, 1) + "\n\n"
        for thread in threads:
            for token in tokens:
                token_text = token["text"]
                output_all_token_matches = token["output_all_matches"]

                if output_all_token_matches is False and db.token_frequency[token_text] > 0:
                    break

                if token_text in thread.text:
                    process_id = thread.process_id
                    process_name = db.process_id_vs_name[process_id]
                    matching_threads += "Process Name: {}, Process Id: {}\n".format(process_name, process_id)
                    matching_threads += thread.text + "\n\n"
                    db.found_token(token)
        return str(matching_threads)

    @staticmethod
    def classify_threads(config, threads):
        if config.classification is None:
            return

        Core.thread_state_classification(config, threads)
        Core.user_config_classification(config, threads)

        Connectors.output_classified_threads(threads)

    @staticmethod
    def thread_state_classification(config, threads):
        for thread in threads:
            for state in config.thread_states:
                tag = state["tag"]
                regex = state["regex"]
                if re.search(regex, thread.text):
                    thread.tags.append(tag)
                    break

    @staticmethod
    def user_config_classification(config, threads):
        for thread in threads:
            found_tag = False

            for item in config.classification:
                tag = item["tag"]
                regex = item["regex"]
                if re.search(regex, thread.text):
                    thread.tags.append(tag)
                    found_tag = True
                    break

            if found_tag is False:
                thread.tags.append("UNCLASSIFIED")

    @staticmethod
    def repetitive_stack_trace(config, threads):
        if config.repetitive_stack_trace is False:
            return

        stack_traces = []
        for thread in threads:
            stack_trace = thread.text.split("\n", 1)[1]
            stack_traces.append(stack_trace)

        stack_trace_counter = Counter(stack_traces).most_common()

        Connectors.output_repetitive_stack_trace(stack_trace_counter)

    @staticmethod
    @Utils.benchmark("compare jstacks")
    def compare_jstacks(config, db, num_jstacks):
        Connectors.output_jstack_comparison_header(config)

        Core.thread_state_frequency(config, db)
        Core.cpu_consuming_threads(config, db)

        Connectors.output_jstacks_in_one_file(config, db, num_jstacks)

    @staticmethod
    def thread_state_frequency(config, db):
        if config.thread_state_frequency_table is False:
            return

        Connectors.output_thread_state_frequency(db)

    @staticmethod
    def cpu_consuming_threads(config, db):
        if config.cpu_intensive_threads is False:
            return

        cpu_wise_sorted_thread_indexes = [] 
        
        for thread_id in db.threads:
            threads_with_thread_id = db.threads[thread_id]

            if len(threads_with_thread_id) == 1:
                continue

            first_thread = threads_with_thread_id[0]
            last_thread = threads_with_thread_id[-1]

            time = last_thread.cpu - first_thread.cpu
            cpu_wise_sorted_thread_indexes.append({"id": thread_id, "time": time})

        cpu_wise_sorted_thread_indexes.sort(key=lambda thread: thread["time"], reverse=True)

        Connectors.output_cpu_consuming_threads(db, cpu_wise_sorted_thread_indexes)