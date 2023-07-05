import re
from utils import Utils
from prettytable import PrettyTable

class Connectors:
    @staticmethod
    def reset_output_files(config):
        Utils.remove_if_there(config.analysis_file_path)
        Utils.remove_if_there(config.jstacks_file_path)

    @staticmethod
    def parse_jstack_file(config, jstack_file_path):
        jstack_index = 0
        jstack_last_line_regex = r"(?m)(JNI global ref.*$)"
        buffered_jstacks = Utils.file_buffer_reader(jstack_file_path, jstack_last_line_regex)

        for jstack in buffered_jstacks:
            Connectors.output_jstack(config, jstack_index, jstack, "unknown_process_id")
            jstack_index += 1

        num_jstacks = jstack_index
        return num_jstacks

    @staticmethod
    def parse_top_file_and_store_nids(db, top_output):
        header_regex = r"(?m)(PID USER.*$)"
        headers = re.finditer(header_regex, top_output)

        if headers is not None:
            last_top_header = list(headers)[-1]
            threads = top_output[last_top_header.end(0) + 1:]

            threads = threads.split("\n")
            threads = [{ "nid": hex(int(thread.split()[0])), "cpu_usage": thread.split()[8] } for thread in threads if thread != ""]
            db.top_cpu_consuming_threads.extend(threads)
        else: 
            exit("Given top file is not in the correct format")

    @staticmethod
    def get_java_processes(db):
        output = Utils.subprocess_call(["ps", "-ef"])["output"]
        lines = output.split(b"\n")

        for line in lines:
            if b"java" in line:
                cols = line.split()
                process_id = cols[0]
                process_name = ""
                for i in range(3, len(cols)):
                    process_name = process_name + cols[i].decode("utf-8") + " "
                db.add_process(process_id, process_name)

    @staticmethod
    def get_jstack_of_java_process(process_id):
        jstack = Utils.subprocess_call(["jstack", str(process_id)])["output"]
        return jstack 

    @staticmethod
    def output_jstack(config, jstack_index, jstack, process_id):
        jstack_file_path = Connectors.get_jstack_file_path(config, jstack_index, process_id)
        Utils.write_to_file(jstack_file_path, jstack)

    @staticmethod
    def get_jstack_file_path(config, jstack_index, process_id):
        jstack_output_path = ".ajs/jstacks/" + config.session_id
        jstack_file_path = jstack_output_path + "/Cycle-" + str(jstack_index) + "/" + process_id + ".txt"
        return jstack_file_path

    @staticmethod
    def output_new_jstack_header(config, db, jstack_index, process_id):
        matching_is_off = config.tokens is None
        classification_is_off = config.classification_groups is None
        repetitive_stack_trace_is_off = config.repetitive_stack_trace is False

        if classification_is_off and matching_is_off and repetitive_stack_trace_is_off:
            return

        new_jstack_header = "JSTACK " + str(jstack_index) + " FOR PROCESS " + str(process_id)
        new_jstack_header = Utils.borderify_text(db, new_jstack_header, 2) + "\n\n"
        Utils.append_to_file(config.analysis_file_path, new_jstack_header)

    @staticmethod
    def read_jstack(config, jstack_index, process_id):
        jstack_file_path = Connectors.get_jstack_file_path(config, jstack_index, process_id)

        with open(jstack_file_path, "r") as f:
            jstack = f.read()
            return jstack

    @staticmethod
    def add_jstack_time_stamp_to_db(db, jstack):
        jstack = jstack.strip()
        jstack_time_stamp = jstack.split("\n")[0]
        db.jstack_time_stamps.append(jstack_time_stamp)

    @staticmethod
    def output_matching_threads(config, matching_threads_text):
        Utils.append_to_file(config.analysis_file_path, matching_threads_text)

    @staticmethod
    def output_classified_threads(config, db, classified_threads):
        classified_threads = sorted(classified_threads, key=lambda thread: str(thread.tags))

        classified_threads_output = "THREADS SORTED BY CATEGORIES"
        classified_threads_output = Utils.borderify_text(db, classified_threads_output, 1) + "\n\n"
        for thread in classified_threads:
            if (thread.tags == []):
                continue

            classified_threads_output += "Tags: " + str(thread.tags) + "\n"
            classified_threads_output += thread.text + "\n\n"

        Utils.append_to_file(config.analysis_file_path, classified_threads_output)

    @staticmethod
    def output_repetitive_stack_trace(config, db, stack_trace_counter):
        repetitive_stack_trace_output = "REPEATED STACK TRACES"
        repetitive_stack_trace_output = Utils.borderify_text(db, repetitive_stack_trace_output, 1) + "\n\n"
        for stack_trace in stack_trace_counter:
            if stack_trace[1] == 1:
                break
            
            repetitive_stack_trace_output += "Count: " + str(stack_trace[1]) + "\n"
            repetitive_stack_trace_output += stack_trace[0] + "\n\n"
        
        Utils.append_to_file(config.analysis_file_path, repetitive_stack_trace_output)

    @staticmethod
    def store_threads_in_db(db, threads):
        state_frequency_dict = {}

        for thread in threads:
            if thread.nid not in db.threads:
                db.threads[thread.nid] = []
            db.threads[thread.nid].append(thread)

            thread_state = thread.thread_state
            if thread_state == "unknown_state":
                continue
            if thread_state not in state_frequency_dict:
                state_frequency_dict[thread_state] = 0
            state_frequency_dict[thread_state] += 1

        db.state_frequency_dicts.append(state_frequency_dict)

    @staticmethod
    def output_jstack_comparison_header(config, db):
        state_frequency_is_off = config.thread_state_frequency_table is False
        cpu_consuming_threads_top_is_off = config.cpu_consuming_threads_top is False
        cpu_consuming_threads_jstack_is_off = config.cpu_consuming_threads_jstack is False

        if state_frequency_is_off and cpu_consuming_threads_top_is_off and cpu_consuming_threads_jstack_is_off:
            return

        new_jstack_header = "JSTACKS COMPARISON"
        new_jstack_header = Utils.borderify_text(db, new_jstack_header, 2) + "\n\n"
        Utils.append_to_file(config.analysis_file_path, new_jstack_header)

    @staticmethod
    def output_thread_state_frequency(config, db):
        thread_state_frequency = "THREAD STATE FREQUENCY"
        thread_state_frequency = Utils.borderify_text(db, thread_state_frequency, 1) + "\n\n"

        possible_states = []
        for frequency_dict in db.state_frequency_dicts:
            for state in frequency_dict:
                if state not in possible_states:
                    possible_states.append(state)
        possible_states = sorted(possible_states)

        table = PrettyTable()

        for jstack_index, frequency_dict in enumerate(db.state_frequency_dicts):
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

            Utils.append_to_file(config.analysis_file_path, thread_state_frequency + str(table) + "\n\n")

    @staticmethod
    def output_cpu_consuming_threads_jstack(config, db, cpu_wise_sorted_thread_indexes, cpu_field_not_present, time_between_jstacks):
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (JSTACK)"
        cpu_consuming_threads_header = Utils.borderify_text(db, cpu_consuming_threads_header, 1) + "\n\n"
        cpu_consuming_threads_header += "TOTAL TIME BETWEEN JSTACKS " + str(time_between_jstacks.total_seconds()) + "s\n\n"

        cpu_consuming_threads_text = ""

        if cpu_field_not_present is True:
            cpu_consuming_threads_text += "'cpu' field not present in JStack\n\n"
        else:
            for cpu_wise_sorted_thread_index in cpu_wise_sorted_thread_indexes:
                nid = cpu_wise_sorted_thread_index["nid"]
                time = cpu_wise_sorted_thread_index["time"]
                time_in_seconds = "{:.2f}s".format(time / 1000)
                db_thread = db.threads[nid]

                first_thread_instance = db_thread[0]
                last_thread_instance = db_thread[-1]

                cpu_consuming_threads_text += "Thread NID: {} CPU: {}\n".format(first_thread_instance.nid, time_in_seconds)
                cpu_consuming_threads_text += "First Occurrence:\n" 
                cpu_consuming_threads_text += first_thread_instance.text + "\n"
                cpu_consuming_threads_text += "Last Occurrence:\n"
                cpu_consuming_threads_text += last_thread_instance.text + "\n\n"

        if cpu_consuming_threads_text != "":
            Utils.append_to_file(config.analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    def output_cpu_consuming_threads_top(config, db):
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (TOP)"
        cpu_consuming_threads_header = Utils.borderify_text(db, cpu_consuming_threads_header, 1) + "\n\n"

        cpu_consuming_threads_text = ""

        if db.system_compatible_with_top is True:
            for thread in db.top_cpu_consuming_threads:
                nid = thread["nid"]
                cpu_usage = thread["cpu_usage"]

                if nid not in db.threads:
                    continue

                db_thread = db.threads[nid]

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

        if cpu_consuming_threads_text != "":
            Utils.append_to_file(config.analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    def output_jstacks_in_one_file(config, db, num_jstacks):
        output_jstack_text = ""
        for jstack_index in range(num_jstacks):
            for process_id in db.process_id_vs_name:
                jstack = Connectors.read_jstack(config, jstack_index, process_id)
                jstack_header = "JStack #{} Process ID: {}".format(jstack_index, process_id)
                jstack_header = Utils.borderify_text(db, jstack_header, 1, False) + "\n\n"
                output_jstack_text += jstack_header
                output_jstack_text += jstack + "\n\n"

        Utils.append_to_file(config.jstacks_file_path, output_jstack_text)

    @staticmethod
    def prepend_contents(config, db):
        max_level = 0
        for line in db.analysis_file_contents:
            max_level = max(max_level, line[1])

        contents = "ANALYSIS FILE CONTENTS [Use this for navigating to the relevant sections]\n\n"
        for line in db.analysis_file_contents:
            text = line[0]
            level = line[1]

            for _ in range(max_level - level):
                contents += '\t'

            contents += text + "\n"
        contents += "\n"

        Utils.prepend_to_file(config.analysis_file_path, contents)

    @staticmethod
    @Utils.benchmark_time("azure data upload")
    def upload_output_files(config, db):
        blob_name = config.session_id
        Utils.upload_to_azure(db, blob_name, "analysis", config.analysis_file_path)
        Utils.upload_to_azure(db, blob_name, "jstacks", config.jstacks_file_path)
