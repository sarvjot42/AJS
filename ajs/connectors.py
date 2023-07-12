import os
import re
from context import Context 
from utils import Utils
from configuration import Config
from prettytable import PrettyTable

class Connectors:
    @staticmethod
    def delete_existing_files():
        Utils.remove_if_there(Config.analysis_file_path)
        Utils.remove_if_there(Config.jstacks_file_path)

    @staticmethod
    def delete_auxilliary_folder():
        Utils.remove_if_there(Config.jstack_folder_path)

    @staticmethod
    def parse_and_store_jstacks_in_disk(jstack_file_path):
        jstack_index = 0
        jstack_last_line_regex = r"(?m)(JNI global ref.*$)"

        buffer = bytearray()

        with open(jstack_file_path, "rb") as file:
            while True:
                line = file.readline()

                if not line:
                    break

                buffer.extend(line)

                if re.search(jstack_last_line_regex, line.decode("utf-8")):
                    Connectors.store_jstack_in_disk(jstack_index, buffer.decode("utf-8"), "unknown_process_id")

                    jstack_index += 1
                    buffer = bytearray()

        num_jstacks = jstack_index
        return num_jstacks

    @staticmethod
    def parse_top_file_and_store_nids(top_output):
        header_regex = r"(?m)(PID USER.*$)"
        headers = re.finditer(header_regex, top_output)

        if headers is not None:
            last_top_header = list(headers)[-1]
            threads = top_output[last_top_header.end(0) + 1:]

            threads = threads.split("\n")
            threads = [{ "nid": hex(int(thread.split()[0])), "cpu_usage": thread.split()[8] } for thread in threads if thread != ""]
            Context.top_cpu_consuming_threads.extend(threads)
        else: 
            exit("Given top file is not in the correct format")

    @staticmethod
    def find_java_processes():
        try:
            output = Utils.subprocess_call([
                "kubectl", "exec", "-it", 
                '-n', Config.namespace, Config.pod_name, 
                "-c", Config.container_name, 
                "--", 
                "bash", "-c",
                "time ps -ef"
            ])
        except Exception as e:
            print("\nError in getting java processes")
            print(e)
            os._exit(1)

        lines = output.split("\n")

        for line in lines:
            if "java" in line:
                cols = line.split()
                process_id = cols[1]
                process_name = cols[7]
                Context.add_process(process_id, process_name)

    @staticmethod
    def get_jstack_of_java_process(process_id):
        try:
            jstack = Utils.subprocess_call([
                "kubectl", "exec", "-it", 
                '-n', Config.namespace, Config.pod_name, 
                "-c", Config.container_name, 
                "--", 
                "bash", "-c",
                "time jstack " + str(process_id)
            ])
        except Exception as e:
            print("\nError in getting jstack of process " + str(process_id))
            print(e)
            os._exit(1)

        return jstack

    @staticmethod
    def store_jstack_in_disk(jstack_index, jstack, process_id):
        jstack_file_path = Connectors.get_jstack_file_path(jstack_index, process_id)
        Utils.write_to_file(jstack_file_path, jstack)

    @staticmethod
    def get_jstack_file_path(jstack_index, process_id):
        jstack_output_path = Config.jstack_folder_path + Config.session_id
        jstack_file_path = jstack_output_path + "/Cycle-" + str(jstack_index) + "/" + process_id + ".txt"
        return jstack_file_path

    @staticmethod
    def output_new_jstack_header(jstack_index, process_id):
        matching_is_off = Config.tokens is None
        classification_is_off = Config.thread_classes is None
        repetitive_stack_trace_is_off = Config.repetitive_stack_trace is False

        if classification_is_off and matching_is_off and repetitive_stack_trace_is_off:
            return

        new_jstack_header = "JSTACK " + str(jstack_index) + " FOR PROCESS " + str(process_id)
        new_jstack_header = Utils.borderify_text_and_update_contents(new_jstack_header, 2, Config.analysis_file_path) + "\n\n"
        Utils.append_to_file(Config.analysis_file_path, new_jstack_header)

    @staticmethod
    def read_jstack_from_disk(jstack_index, process_id):
        jstack_file_path = Connectors.get_jstack_file_path(jstack_index, process_id)

        with open(jstack_file_path, "r") as f:
            jstack = f.read()
            return jstack

    @staticmethod
    def update_jstack_time_stamp_context(jstack):
        jstack = jstack.strip()
        jstack_time_stamp = jstack.split("\n")[0]
        Context.jstack_time_stamps.append(jstack_time_stamp)

    @staticmethod
    def output_matching_threads(matching_threads_text):
        Utils.append_to_file(Config.analysis_file_path, matching_threads_text)

    @staticmethod
    def output_classified_threads(classified_threads):
        classified_threads_header = "THREAD CATEGORIES"
        classified_threads_header = Utils.borderify_text_and_update_contents(classified_threads_header, 1, Config.analysis_file_path) + "\n\n"

        classified_threads_text = ""

        for tag in classified_threads:
            thread_class_sorted_by_state = classified_threads[tag]
            num_threads_in_class = len(thread_class_sorted_by_state) 

            classified_threads_text += "{} {} threads found\n\n".format(num_threads_in_class, tag)

            for it in range(num_threads_in_class):
                current_thread = thread_class_sorted_by_state[it]
                if it == 0 or current_thread.thread_state != thread_class_sorted_by_state[it - 1].thread_state:
                    state_header = "{} threads".format(current_thread.thread_state)
                    classified_threads_text += Utils.borderify_text_and_update_contents(state_header, 0, Config.analysis_file_path) + "\n\n"

                if Config.classification_print_trace is False:
                    header_and_trace = current_thread.text.split("\n", 1)
                    header = header_and_trace[0]
                    classified_threads_text += header + "\n\n"
                else:
                    classified_threads_text += current_thread.text + "\n\n"

        if classified_threads_text == "":
            classified_threads_text = "No threads found for configured classes\n\n"

        Utils.append_to_file(Config.analysis_file_path, classified_threads_header + classified_threads_text)

    @staticmethod
    def output_repetitive_stack_trace(stack_trace_counter):
        repetitive_stack_trace_header = "REPEATED STACK TRACES"
        repetitive_stack_trace_header = Utils.borderify_text_and_update_contents(repetitive_stack_trace_header, 1, Config.analysis_file_path) + "\n\n"

        repetitive_stack_trace_text = ""
        for stack_trace in stack_trace_counter:
            if stack_trace[1] == 1:
                break
            
            repetitive_stack_trace_text += "Count: " + str(stack_trace[1]) + "\n"
            repetitive_stack_trace_text += stack_trace[0] + "\n\n"
        
        if repetitive_stack_trace_text == "":
            repetitive_stack_trace_text = "No repetitive stack traces found\n\n"

        Utils.append_to_file(Config.analysis_file_path, repetitive_stack_trace_header + repetitive_stack_trace_text)

    @staticmethod
    def update_threads_context(threads):
        state_frequency_dict = {}

        for thread in threads:
            if thread.nid not in Context.threads:
                Context.threads[thread.nid] = []

            # store only first and last occurence of a thread
            if len(Context.threads[thread.nid]) < 2:
                Context.threads[thread.nid].append(thread)
            else:
                Context.threads[thread.nid][1] = thread

            thread_state = thread.thread_state
            if thread_state == "unknown_state":
                continue
            if thread_state not in state_frequency_dict:
                state_frequency_dict[thread_state] = 0
            state_frequency_dict[thread_state] += 1

        Context.state_frequency_dicts.append(state_frequency_dict)

    @staticmethod
    def output_jstack_comparison_header():
        state_frequency_is_off = Config.thread_state_frequency is False
        cpu_consuming_threads_top_is_off = Config.cpu_consuming_threads_top is False
        cpu_consuming_threads_jstack_is_off = Config.cpu_consuming_threads_jstack is False

        if state_frequency_is_off and cpu_consuming_threads_top_is_off and cpu_consuming_threads_jstack_is_off:
            return

        new_jstack_header = "JSTACKS COMPARISON"
        new_jstack_header = Utils.borderify_text_and_update_contents(new_jstack_header, 2, Config.analysis_file_path) + "\n\n"
        Utils.append_to_file(Config.analysis_file_path, new_jstack_header)

    @staticmethod
    def output_thread_state_frequency():
        thread_state_frequency_header = "THREAD STATE FREQUENCY"
        thread_state_frequency_header = Utils.borderify_text_and_update_contents(thread_state_frequency_header, 1, Config.analysis_file_path) + "\n\n"

        thread_state_frequency_text = ""

        possible_states = []
        for frequency_dict in Context.state_frequency_dicts:
            for state in frequency_dict:
                if state not in possible_states:
                    possible_states.append(state)
        possible_states = sorted(possible_states)

        table = PrettyTable()

        for jstack_index, frequency_dict in enumerate(Context.state_frequency_dicts):
            row = []
            row.append(jstack_index)
            for state in possible_states:
                if state in frequency_dict:
                    row.append(frequency_dict[state])
                else:
                    row.append(0)
            table.add_row(row)

        if len(possible_states) > 0:
            possible_states.insert(0, "JStack #")
            table.field_names = possible_states

            thread_state_frequency_text += str(table) + "\n\n"

        if thread_state_frequency_text == "":
            thread_state_frequency_text = "No thread states to display\n\n"

        Utils.append_to_file(Config.analysis_file_path, thread_state_frequency_header + thread_state_frequency_text)

    @staticmethod
    def output_cpu_consuming_threads_jstack(cpu_wise_sorted_thread_indexes, cpu_field_not_present, time_between_jstacks):
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (JSTACK)"
        cpu_consuming_threads_header = Utils.borderify_text_and_update_contents(cpu_consuming_threads_header, 1, Config.analysis_file_path) + "\n\n"

        cpu_consuming_threads_text = ""

        if cpu_field_not_present is True:
            cpu_consuming_threads_text += "'cpu' field not present in JStack\n\n"
        else:
            cpu_consuming_threads_header += "TOTAL TIME BETWEEN JSTACKS " + str(time_between_jstacks) + "s\n\n"

            for cpu_wise_sorted_thread_index in cpu_wise_sorted_thread_indexes:
                time = cpu_wise_sorted_thread_index["time"]

                if time / 1000 / time_between_jstacks * 100 <= Config.cpu_threshold_percentage:
                    break

                time_in_seconds = "{:.2f}s".format(time / 1000)
                nid = cpu_wise_sorted_thread_index["nid"]
                thread = Context.threads[nid]

                first_thread_instance = thread[0]
                last_thread_instance = thread[-1]

                cpu_consuming_threads_text += "Thread NID: {} CPU: {}\n".format(first_thread_instance.nid, time_in_seconds)
                cpu_consuming_threads_text += "First Occurrence:\n" 
                cpu_consuming_threads_text += first_thread_instance.text + "\n"
                cpu_consuming_threads_text += "Last Occurrence:\n"
                cpu_consuming_threads_text += last_thread_instance.text + "\n\n"

        if cpu_consuming_threads_text == "":
            cpu_consuming_threads_text = "No CPU consuming threads found\n\n"
        
        Utils.append_to_file(Config.analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    def output_cpu_consuming_threads_top():
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (TOP)"
        cpu_consuming_threads_header = Utils.borderify_text_and_update_contents(cpu_consuming_threads_header, 1, Config.analysis_file_path) + "\n\n"

        cpu_consuming_threads_text = ""

        for top_thread in Context.top_cpu_consuming_threads:
            nid = top_thread["nid"]
            cpu_usage = top_thread["cpu_usage"]

            if nid not in Context.threads or float(cpu_usage) <= Config.cpu_threshold_percentage:
                continue

            thread = Context.threads[nid]

            cpu_consuming_threads_text += "Thread NID: {} CPU: {}%\n".format(nid, cpu_usage)
            if len(thread) == 1:
                thread_instance = thread[0]
                cpu_consuming_threads_text += thread_instance.text + "\n\n"
            else:
                first_thread_instance = thread[0]
                last_thread_instance = thread[-1]

                cpu_consuming_threads_text += "First Occurrence:\n"
                cpu_consuming_threads_text += first_thread_instance.text + "\n"
                cpu_consuming_threads_text += "Last Occurrence:\n"
                cpu_consuming_threads_text += last_thread_instance.text + "\n\n"

        if cpu_consuming_threads_text == "":
            cpu_consuming_threads_text += "No CPU consuming threads found\n\n"
        
        Utils.append_to_file(Config.analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    @Utils.benchmark_time("output jstacks in one file")
    def store_jstacks_in_one_file(num_jstacks):
        output_jstack_text = ""
        for jstack_index in range(num_jstacks):
            for process_id in Context.process_id_vs_name:
                jstack = Connectors.read_jstack_from_disk(jstack_index, process_id)
                jstack_header = "JStack #{} Process ID: {}".format(jstack_index, process_id)
                jstack_header = Utils.borderify_text_and_update_contents(jstack_header, 1, Config.jstacks_file_path) + "\n\n"
                output_jstack_text += jstack_header
                output_jstack_text += jstack + "\n\n"

        Utils.append_to_file(Config.jstacks_file_path, output_jstack_text)

    @staticmethod
    def prepend_contents():
        file_contents_dict = {}

        for content in Context.file_contents:
            file = content[2]
            if file not in file_contents_dict:
                file_contents_dict[file] = []
            file_contents_dict[file].append(content)

        for file in file_contents_dict:
            Connectors.write_contents_to_file(file, file_contents_dict[file])

    @staticmethod
    def write_contents_to_file(file, contents):
        if len(contents) == 0:
            Utils.prepend_to_file(file, "No output for this file\n\n")
            return

        # printing with proper indentation
        max_level = 0
        for content in contents:
            max_level = max(max_level, content[1])

        contents_text = "FILE CONTENTS [Use this for navigating to the relevant sections]\n\n"
        for content in contents:
            text = content[0]
            level = content[1]

            for _ in range(max_level - level):
                contents_text += '\t'

            contents_text += text + "\n"
        contents_text += "\n"

        Utils.prepend_to_file(file, contents_text)

    @staticmethod
    @Utils.benchmark_time("azure data upload")
    def upload_output_files():
        blob_name = Config.session_id
        Utils.upload_to_azure(blob_name, "analysis", Config.analysis_file_path)
        Utils.upload_to_azure(blob_name, "jstacks", Config.jstacks_file_path)
