import os
import re
import time
from utils import Utils
from schema import Thread
from collections import Counter
from connectors import Connectors

class Core:
    @staticmethod 
    @Utils.benchmark_time("jstack file input")
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
    @Utils.benchmark_time("top file input")
    def handle_top_file_input(config, db):
        top_file_path = config.top_file_path

        if top_file_path is None:
            exit("\nNo top file path provided in config file")

        if not os.path.exists(top_file_path):
            exit("\nInvalid top file path provided in config file")

        with open(top_file_path, "r") as f:
            top_output = f.read()

        Connectors.parse_top_file_and_store_nids(db, top_output)

    @staticmethod 
    @Utils.benchmark_time("jstack generation")
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
    @Utils.benchmark_time("top generation")
    def handle_top_generation(config, db):
        if config.cpu_consuming_threads_top is False:
            return

        command_list = ["top", "-H", "-b", "-n", "1"]
        for process_id in db.process_id_vs_name: 
            command_list.append("-p")
            command_list.append(process_id)

        result = Utils.subprocess_call(command_list)

        if result["err"] != "":
            db.system_compatible_with_top = False  
        else:
            top_output = result["output"]
            Connectors.parse_top_file_and_store_nids(db, top_output)

    @staticmethod
    @Utils.benchmark_time("analyse individual jstack")
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
        nid_containing_threads = [thread for thread in encapsulated_threads if thread.nid is not -1]

        return nid_containing_threads 

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
        Connectors.output_matching_threads(config, matching_threads_text)

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
        if config.classification_groups is None:
            return

        for thread in threads:
            for group in config.classification_groups:
                for item in group:
                    tag = item["tag"]
                    regex = item["regex"]
                    if re.search(regex, thread.text):
                        thread.tags.append(tag)
                        break

        Connectors.output_classified_threads(config, threads)

    @staticmethod
    def repetitive_stack_trace(config, threads):
        if config.repetitive_stack_trace is False:
            return

        stack_traces = []
        for thread in threads:
            header_and_trace = thread.text.split("\n", 1)

            if len(header_and_trace) < 2:
                continue

            stack_trace = header_and_trace[1]
            stack_traces.append(stack_trace)

        stack_trace_counter = Counter(stack_traces).most_common()

        Connectors.output_repetitive_stack_trace(config, stack_trace_counter)

    @staticmethod
    @Utils.benchmark_time("compare jstacks")
    def compare_jstacks(config, db, num_jstacks):
        Connectors.output_jstack_comparison_header(config)

        Core.thread_state_frequency(config, db)
        Core.cpu_consuming_threads_jstack(config, db)
        Core.cpu_consuming_threads_top(config, db)

        Connectors.output_jstacks_in_one_file(config, db, num_jstacks)

    @staticmethod
    def thread_state_frequency(config, db):
        if config.thread_state_frequency_table is False:
            return

        Connectors.output_thread_state_frequency(config, db)

    @staticmethod
    def cpu_consuming_threads_jstack(config, db):
        if config.cpu_consuming_threads_jstack is False:
            return

        cpu_field_not_present = False
        cpu_wise_sorted_thread_indexes = [] 
        
        for thread_nid in db.threads:
            threads_with_thread_nid = db.threads[thread_nid]

            if len(threads_with_thread_nid) == 1:
                continue

            first_thread = threads_with_thread_nid[0]
            last_thread = threads_with_thread_nid[-1]

            if first_thread.cpu is -1:
                cpu_field_not_present = True
                break

            time = last_thread.cpu - first_thread.cpu
            cpu_wise_sorted_thread_indexes.append({"nid": thread_nid, "time": time})

        cpu_wise_sorted_thread_indexes.sort(key=lambda thread: thread["time"], reverse=True)

        Connectors.output_cpu_consuming_threads_jstack(config, db, cpu_wise_sorted_thread_indexes, cpu_field_not_present)

    @staticmethod
    def cpu_consuming_threads_top(config, db):
        if config.cpu_consuming_threads_top is False:
            return

        Connectors.output_cpu_consuming_threads_top(config, db)
