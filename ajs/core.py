import os
import re
import time
from utils import Utils
from data import Config, Database
from schema import Thread
from collections import Counter
from connectors import Connectors

class Core:
    @staticmethod 
    @Utils.benchmark_time("jstack file input")
    def handle_jstack_file_input():
        jstack_file_path = Config.jstack_file_path

        if jstack_file_path is None:
            exit("\nNo jstack file path provided in config file")

        if not os.path.exists(jstack_file_path):
            exit("\nInvalid jstack file path provided in config file")

        Database.add_process("unknown_process_id", "unknown_process")
        num_jstacks = Connectors.parse_jstack_file(jstack_file_path)
        return num_jstacks

    @staticmethod
    @Utils.benchmark_time("top file input")
    def handle_top_file_input():
        if Config.cpu_consuming_threads_top is False:
            return

        top_file_path = Config.top_file_path

        if top_file_path is None:
            exit("\nNo top file path provided in config file")

        if not os.path.exists(top_file_path):
            exit("\nInvalid top file path provided in config file")

        with open(top_file_path, "r") as f:
            top_output = f.read()

        Connectors.parse_top_file_and_store_nids(top_output)

    @staticmethod 
    @Utils.benchmark_time("jstack generation")
    def handle_jstack_generation():
        num_jstacks = Config.num_jstacks
        delay_bw_jstacks = Config.delay_bw_jstacks

        Connectors.get_java_processes()

        for jstack_index in range(num_jstacks):
            for process_id in Database.process_id_vs_name:
                jstack = Connectors.get_jstack_of_java_process(process_id)
                Connectors.output_jstack(jstack_index, jstack, process_id)

            if jstack_index != num_jstacks - 1:
                time.sleep(delay_bw_jstacks / 1000)

    @staticmethod
    @Utils.benchmark_time("top generation [parallel to jstack generation]")
    def handle_top_generation():
        if Config.cpu_consuming_threads_top is False:
            return

        num_top = 2
        delay_bw_tops = Config.delay_bw_jstacks * (Config.num_jstacks - 1) / 1000

        command_list = [
            "kubectl", "exec", "-it", 
            '-n', Config.namespace, Config.pod_name, 
            "-c", Config.container_name, 
            "--", 
            "bash", "-c",
            "time top -H -b -n " + str(num_top) + " -d " + str(delay_bw_tops)
        ]

        for process_id in Database.process_id_vs_name: 
            command_list.append("-p")
            command_list.append(process_id)

        result = Utils.subprocess_call(command_list)

        if result["err"] != "":
            Database.system_compatible_with_top = False  
        else:
            top_output = result["output"]
            Connectors.parse_top_file_and_store_nids(top_output)

    @staticmethod
    @Utils.benchmark_time("individual jstack analysis")
    def analyse_jstacks(jstack_index):
        for process_id in Database.process_id_vs_name:
            Connectors.output_new_jstack_header(jstack_index, process_id)

            threads = Core.read_and_filter_threads(jstack_index, process_id)
            Core.match_threads(threads)
            Core.classify_threads(threads)
            Core.repetitive_stack_trace(threads)

            Connectors.store_threads_in_db(threads)

    @staticmethod
    def read_and_filter_threads(jstack_index, process_id):
        jstack = Connectors.read_jstack(jstack_index, process_id)
        Connectors.add_jstack_time_stamp_to_db(jstack)
        threads = Core.parse_threads_from_jstack(jstack, process_id)
        threads = Core.filter_threads(threads)
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
        nid_containing_threads = [thread for thread in encapsulated_threads if thread.nid != -1]

        return nid_containing_threads 

    @staticmethod
    def filter_threads(threads):
        filtered_threads = []

        # giving preference to include_only
        if Config.include_only is not None:
            for thread in threads:
                for wanted_token in Config.include_only:
                    if re.search(wanted_token, thread.text):
                        filtered_threads.append(thread)
                        break
        elif Config.filter_out is not None:
            for thread in threads:
                to_include = True

                for unwanted_token in Config.filter_out:
                    if re.search(unwanted_token, thread.text):
                        to_include = False
                        break

                if to_include:
                    filtered_threads.append(thread)
        else:
            return threads

        return filtered_threads

    @staticmethod
    def match_threads(threads):
        if Config.tokens is None:
            return

        matching_threads_text = Core.give_matching_threads(threads)
        Connectors.output_matching_threads(matching_threads_text)

    @staticmethod
    def give_matching_threads(threads):
        tokens = Config.tokens

        matching_threads = "MATCHING THREADS"
        matching_threads = Utils.borderify_text(matching_threads, 1, Config.analysis_file_path) + "\n\n"
        for thread in threads:
            for token in tokens:
                token_text = token["text"]
                output_all_token_matches = token["output_all_matches"]

                if output_all_token_matches is False and Database.token_frequency[token_text] > 0:
                    break

                if token_text in thread.text:
                    process_id = thread.process_id
                    process_name = Database.process_id_vs_name[process_id]
                    matching_threads += "Process Name: {}, Process Id: {}\n".format(process_name, process_id)
                    matching_threads += thread.text + "\n\n"
                    Database.found_token(token)
        return str(matching_threads)

    @staticmethod
    def classify_threads(threads):
        if Config.classification_groups is None:
            return

        for thread in threads:
            for group in Config.classification_groups:
                for item in group:
                    tag = item["tag"]
                    regex = item["regex"]
                    if re.search(regex, thread.text):
                        thread.tags.append(tag)
                        break

        Connectors.output_classified_threads(threads)

    @staticmethod
    def repetitive_stack_trace(threads):
        if Config.repetitive_stack_trace is False:
            return

        stack_traces = []
        for thread in threads:
            header_and_trace = thread.text.split("\n", 1)

            if len(header_and_trace) < 2:
                continue

            stack_trace = header_and_trace[1]
            stack_traces.append(stack_trace)

        stack_trace_counter = Counter(stack_traces).most_common()

        Connectors.output_repetitive_stack_trace(stack_trace_counter)

    @staticmethod
    @Utils.benchmark_time("jstacks comparison")
    def compare_jstacks():
        Connectors.output_jstack_comparison_header()

        Core.thread_state_frequency()
        Core.cpu_consuming_threads_jstack()
        Core.cpu_consuming_threads_top()
        Core.most_blocked_threads()

    @staticmethod
    def thread_state_frequency():
        if Config.thread_state_frequency_table is False:
            return

        Connectors.output_thread_state_frequency()

    @staticmethod
    def cpu_consuming_threads_jstack():
        if Config.cpu_consuming_threads_jstack is False:
            return

        first_jstack_time_stamp = Database.jstack_time_stamps[0]
        last_jstack_time_stamp = Database.jstack_time_stamps[-1]

        time_between_jstacks = Utils.diff_between_time_stamps(first_jstack_time_stamp, last_jstack_time_stamp).total_seconds()

        cpu_field_not_present = False
        cpu_wise_sorted_thread_indexes = [] 
        
        for thread_nid in Database.threads:
            threads_with_thread_nid = Database.threads[thread_nid]

            if len(threads_with_thread_nid) == 1:
                continue

            first_thread = threads_with_thread_nid[0]
            last_thread = threads_with_thread_nid[-1]

            if first_thread.cpu == -1:
                cpu_field_not_present = True
                break

            time = last_thread.cpu - first_thread.cpu
            cpu_wise_sorted_thread_indexes.append({"nid": thread_nid, "time": time})

        cpu_wise_sorted_thread_indexes.sort(key=lambda thread: thread["time"], reverse=True)

        Connectors.output_cpu_consuming_threads_jstack(cpu_wise_sorted_thread_indexes, cpu_field_not_present, time_between_jstacks)

    @staticmethod
    def cpu_consuming_threads_top():
        if Config.cpu_consuming_threads_top is False:
            return

        Connectors.output_cpu_consuming_threads_top()

    @staticmethod
    def most_blocked_threads():
        if Config.most_blocked_threads is False:
            return

        elapsed_field_not_present = False
        time_wise_sorted_blocked_thread_indexes = []
        
        for thread_nid in Database.threads:
            threads_with_thread_nid = Database.threads[thread_nid]

            if len(threads_with_thread_nid) == 1:
                continue

            first_thread = threads_with_thread_nid[0]
            last_thread = threads_with_thread_nid[-1]

            if first_thread.thread_state != "BLOCKED" or last_thread.thread_state != "BLOCKED": 
                continue

            if first_thread.elapsed == -1:
                elapsed_field_not_present = True
                break

            time = last_thread.elapsed - first_thread.elapsed
            time_wise_sorted_blocked_thread_indexes.append({"nid": thread_nid, "time": time})

        time_wise_sorted_blocked_thread_indexes.sort(key=lambda thread: thread["time"], reverse=True)

        Connectors.output_most_blocked_threads_jstack(time_wise_sorted_blocked_thread_indexes, elapsed_field_not_present)
