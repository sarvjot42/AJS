import re
from utils import Utils
from data import Config, Database
from prettytable import PrettyTable

class Connectors:
    @staticmethod
    def clear_existing_files():
        Utils.remove_if_there(Config.analysis_file_path)
        Utils.remove_if_there(Config.jstacks_file_path)

    @staticmethod
    def clear_auxilliary_folder():
        Utils.remove_if_there(Config.jstack_folder_path)

    @staticmethod
    def parse_jstack_file(jstack_file_path):
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
                    Connectors.output_jstack(jstack_index, buffer.decode("utf-8"), "unknown_process_id")

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
            Database.top_cpu_consuming_threads.extend(threads)
        else: 
            exit("Given top file is not in the correct format")

    @staticmethod
    def get_java_processes():
        output = Utils.subprocess_call([
            "kubectl", "exec", "-it", 
            '-n', Config.namespace, Config.pod_name, 
            "-c", Config.container_name, 
            "--", 
             "ps", "-ef"
        ])

        output = output["output"]
        lines = output.split("\n")

        for line in lines:
            if "java" in line:
                cols = line.split()
                process_id = cols[1]
                process_name = cols[7]
                Database.add_process(process_id, process_name)

    @staticmethod
    def get_jstack_of_java_process(process_id):
        jstack = Utils.subprocess_call([
            "kubectl", "exec", "-it", 
            '-n', Config.namespace, Config.pod_name, 
            "-c", Config.container_name, 
            "--", 
             "jstack", str(process_id)
        ])["output"]

        return jstack

    @staticmethod
    def output_jstack(jstack_index, jstack, process_id):
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
        classification_is_off = Config.classification_groups is None
        repetitive_stack_trace_is_off = Config.repetitive_stack_trace is False

        if classification_is_off and matching_is_off and repetitive_stack_trace_is_off:
            return

        new_jstack_header = "JSTACK " + str(jstack_index) + " FOR PROCESS " + str(process_id)
        new_jstack_header = Utils.borderify_text(new_jstack_header, 2, Config.analysis_file_path) + "\n\n"
        Utils.append_to_file(Config.analysis_file_path, new_jstack_header)

    @staticmethod
    def read_jstack(jstack_index, process_id):
        jstack_file_path = Connectors.get_jstack_file_path(jstack_index, process_id)

        with open(jstack_file_path, "r") as f:
            jstack = f.read()
            return jstack

    @staticmethod
    def add_jstack_time_stamp_to_db(jstack):
        jstack = jstack.strip()
        jstack_time_stamp = jstack.split("\n")[0]
        Database.jstack_time_stamps.append(jstack_time_stamp)

    @staticmethod
    def output_matching_threads(matching_threads_text):
        Utils.append_to_file(Config.analysis_file_path, matching_threads_text)

    @staticmethod
    def output_classified_threads(classified_threads):
        classified_threads = sorted(classified_threads, key=lambda thread: str(thread.tags))

        classified_threads_output = "THREADS SORTED BY CATEGORIES"
        classified_threads_output = Utils.borderify_text(classified_threads_output, 1, Config.analysis_file_path) + "\n\n"
        for thread in classified_threads:
            if (thread.tags == []):
                continue

            classified_threads_output += "Tags: " + str(thread.tags) + "\n"
            classified_threads_output += thread.text + "\n\n"

        Utils.append_to_file(Config.analysis_file_path, classified_threads_output)

    @staticmethod
    def output_repetitive_stack_trace(stack_trace_counter):
        repetitive_stack_trace_output = "REPEATED STACK TRACES"
        repetitive_stack_trace_output = Utils.borderify_text(repetitive_stack_trace_output, 1, Config.analysis_file_path) + "\n\n"
        for stack_trace in stack_trace_counter:
            if stack_trace[1] == 1:
                break
            
            repetitive_stack_trace_output += "Count: " + str(stack_trace[1]) + "\n"
            repetitive_stack_trace_output += stack_trace[0] + "\n\n"
        
        Utils.append_to_file(Config.analysis_file_path, repetitive_stack_trace_output)

    @staticmethod
    def store_threads_in_db(threads):
        state_frequency_dict = {}

        for thread in threads:
            if thread.nid not in Database.threads:
                Database.threads[thread.nid] = []

            # store only first and last occurence of a thread
            if len(Database.threads[thread.nid]) < 2:
                Database.threads[thread.nid].append(thread)
            else:
                Database.threads[thread.nid][1] = thread

            thread_state = thread.thread_state
            if thread_state == "unknown_state":
                continue
            if thread_state not in state_frequency_dict:
                state_frequency_dict[thread_state] = 0
            state_frequency_dict[thread_state] += 1

        Database.state_frequency_dicts.append(state_frequency_dict)

    @staticmethod
    def output_jstack_comparison_header():
        state_frequency_is_off = Config.thread_state_frequency_table is False
        cpu_consuming_threads_top_is_off = Config.cpu_consuming_threads_top is False
        cpu_consuming_threads_jstack_is_off = Config.cpu_consuming_threads_jstack is False

        if state_frequency_is_off and cpu_consuming_threads_top_is_off and cpu_consuming_threads_jstack_is_off:
            return

        new_jstack_header = "JSTACKS COMPARISON"
        new_jstack_header = Utils.borderify_text(new_jstack_header, 2, Config.analysis_file_path) + "\n\n"
        Utils.append_to_file(Config.analysis_file_path, new_jstack_header)

    @staticmethod
    def output_thread_state_frequency():
        thread_state_frequency = "THREAD STATE FREQUENCY"
        thread_state_frequency = Utils.borderify_text(thread_state_frequency, 1, Config.analysis_file_path) + "\n\n"

        possible_states = []
        for frequency_dict in Database.state_frequency_dicts:
            for state in frequency_dict:
                if state not in possible_states:
                    possible_states.append(state)
        possible_states = sorted(possible_states)

        table = PrettyTable()

        for jstack_index, frequency_dict in enumerate(Database.state_frequency_dicts):
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

            Utils.append_to_file(Config.analysis_file_path, thread_state_frequency + str(table) + "\n\n")

    @staticmethod
    def output_cpu_consuming_threads_jstack(cpu_wise_sorted_thread_indexes, cpu_field_not_present, time_between_jstacks):
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (JSTACK)"
        cpu_consuming_threads_header = Utils.borderify_text(cpu_consuming_threads_header, 1, Config.analysis_file_path) + "\n\n"

        cpu_consuming_threads_text = ""

        if cpu_field_not_present is True:
            cpu_consuming_threads_text += "'cpu' field not present in JStack\n\n"
        else:
            cpu_consuming_threads_header += "TOTAL TIME BETWEEN JSTACKS " + str(time_between_jstacks) + "s\n\n"

            for cpu_wise_sorted_thread_index in cpu_wise_sorted_thread_indexes:
                time = cpu_wise_sorted_thread_index["time"]

                if time / 1000 / time_between_jstacks * 100 <= Config.thread_cpu_threshold_limit:
                    break

                time_in_seconds = "{:.2f}s".format(time / 1000)
                nid = cpu_wise_sorted_thread_index["nid"]
                db_thread = Database.threads[nid]

                first_thread_instance = db_thread[0]
                last_thread_instance = db_thread[-1]

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
        cpu_consuming_threads_header = Utils.borderify_text(cpu_consuming_threads_header, 1, Config.analysis_file_path) + "\n\n"

        cpu_consuming_threads_text = ""

        if Database.system_compatible_with_top is True:
            for thread in Database.top_cpu_consuming_threads:
                nid = thread["nid"]
                cpu_usage = thread["cpu_usage"]

                if nid not in Database.threads or float(cpu_usage) <= Config.thread_cpu_threshold_limit:
                    continue

                db_thread = Database.threads[nid]

                cpu_consuming_threads_text += "Thread NID: {} CPU: {}%\n".format(nid, cpu_usage)
                if len(db_thread) == 1:
                    thread_instance = db_thread[0]
                    cpu_consuming_threads_text += thread_instance.text + "\n\n"
                else:
                    first_thread_instance = db_thread[0]
                    last_thread_instance = db_thread[-1]

                    cpu_consuming_threads_text += "First Occurrence:\n"
                    cpu_consuming_threads_text += first_thread_instance.text + "\n"
                    cpu_consuming_threads_text += "Last Occurrence:\n"
                    cpu_consuming_threads_text += last_thread_instance.text + "\n\n"
        else:
            cpu_consuming_threads_text += "System not compatible with top\n\n"

        if cpu_consuming_threads_text == "":
            cpu_consuming_threads_text += "No CPU consuming threads found\n\n"
        
        Utils.append_to_file(Config.analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    @Utils.benchmark_time("output jstacks in one file")
    def output_jstacks_in_one_file(num_jstacks):
        output_jstack_text = ""
        for jstack_index in range(num_jstacks):
            for process_id in Database.process_id_vs_name:
                jstack = Connectors.read_jstack(jstack_index, process_id)
                jstack_header = "JStack #{} Process ID: {}".format(jstack_index, process_id)
                jstack_header = Utils.borderify_text(jstack_header, 1, Config.jstacks_file_path) + "\n\n"
                output_jstack_text += jstack_header
                output_jstack_text += jstack + "\n\n"

        Utils.append_to_file(Config.jstacks_file_path, output_jstack_text)

    @staticmethod
    def prepend_contents():
        file_contents_dict = {}

        for content in Database.file_contents:
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
