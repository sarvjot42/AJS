import re
from utils import Utils
from prettytable import PrettyTable

class Connectors:
    @staticmethod
    def reset_output_files():
        Utils.remove_if_there(".ajs/analysis.txt")
        Utils.remove_if_there(".ajs/jstacks.txt")

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
    def parse_top_file_and_store_nids(db, top):
        header_regex = r"(?m)(PID USER.*$)"
        header = re.search(header_regex, top)

        if header is not None:
            header_text = header.group(0)
            header_text_index = top.index(header_text)
            top_threads = top[header_text_index + len(header_text):]

            top_threads = top_threads.split("\n")
            top_threads = [{ "nid": hex(int(thread.split()[0])), "cpu_usage": thread.split()[8] } for thread in top_threads if thread != ""]
            db.top_cpu_intensive_threads.extend(top_threads)
        else: 
            exit("Given top file is not in the correct format")

    @staticmethod
    def get_java_processes(db):
        output = Utils.subprocess_call(["ps", "-e"])
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
        jstack = Utils.subprocess_call(["jstack", str(process_id)])
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
    def output_new_jstack_header(config, jstack_index, process_id):
        matching_is_off = config.tokens is None
        classification_is_off = config.classification is None
        repetitive_stack_trace_is_off = config.repetitive_stack_trace is False

        if classification_is_off and matching_is_off and repetitive_stack_trace_is_off:
            return

        analysis_file_path = ".ajs/analysis.txt"
        new_jstack_header = "JSTACK " + str(jstack_index) + " FOR PROCESS " + str(process_id)
        new_jstack_header = Utils.borderify_text(new_jstack_header, 2) + "\n\n"
        Utils.append_to_file(analysis_file_path, new_jstack_header)

    @staticmethod
    def read_jstack(config, jstack_index, process_id):
        jstack_file_path = Connectors.get_jstack_file_path(config, jstack_index, process_id)

        with open(jstack_file_path, "r") as f:
            jstack = f.read()
            return jstack

    @staticmethod
    def output_matching_threads(matching_threads_text):
        analysis_file_path = ".ajs/analysis.txt"
        Utils.append_to_file(analysis_file_path, matching_threads_text)

    @staticmethod
    def output_classified_threads(classified_threads):
        classified_threads = sorted(classified_threads, key=lambda thread: str(thread.tags))

        classified_threads_output = "THREADS SORTED BY CATEGORIES"
        classified_threads_output = Utils.borderify_text(classified_threads_output, 1) + "\n\n"
        for thread in classified_threads:
            classified_threads_output += "Tags: " + str(thread.tags) + "\n"
            classified_threads_output += thread.text + "\n\n"

        analysis_file_path = ".ajs/analysis.txt"
        Utils.append_to_file(analysis_file_path, classified_threads_output)

    @staticmethod
    def output_repetitive_stack_trace(stack_trace_counter):
        repetitive_stack_trace_output = "REPEATED STACK TRACES"
        repetitive_stack_trace_output = Utils.borderify_text(repetitive_stack_trace_output, 1) + "\n\n"
        for stack_trace in stack_trace_counter:
            if stack_trace[1] == 1:
                break
            
            repetitive_stack_trace_output += "Count: " + str(stack_trace[1]) + "\n"
            repetitive_stack_trace_output += stack_trace[0] + "\n\n"
        
        analysis_file_path = ".ajs/analysis.txt"
        Utils.append_to_file(analysis_file_path, repetitive_stack_trace_output)

    @staticmethod
    def store_threads_in_db(db, threads):
        state_frequency_dict = {}

        for thread in threads:
            if thread.nid not in db.threads:
                db.threads[thread.nid] = []
            db.threads[thread.nid].append(thread)

            thread_state = thread.thread_state
            if thread_state not in state_frequency_dict:
                state_frequency_dict[thread_state] = 0
            state_frequency_dict[thread_state] += 1

        db.state_frequency_dicts.append(state_frequency_dict)

    @staticmethod
    def output_jstack_comparison_header(config):
        state_frequency_is_off = config.thread_state_frequency_table is False
        cpu_intensive_threads_jstack_is_off = config.cpu_intensive_threads_jstack is False
        cpu_intensive_threads_top_is_off = config.cpu_intensive_threads_top is False

        if state_frequency_is_off and cpu_intensive_threads_jstack_is_off and cpu_intensive_threads_top_is_off:
            return

        analysis_file_path = ".ajs/analysis.txt"
        new_jstack_header = "JSTACKS COMPARISON"
        new_jstack_header = Utils.borderify_text(new_jstack_header, 2) + "\n\n"
        Utils.append_to_file(analysis_file_path, new_jstack_header)

    @staticmethod
    def output_thread_state_frequency(db):
        thread_state_frequency = "THREAD STATE FREQUENCY"
        thread_state_frequency = Utils.borderify_text(thread_state_frequency, 1) + "\n\n"

        possible_states = []
        for frequency_dict in db.state_frequency_dicts:
            for state in frequency_dict:
                if state not in possible_states:
                    possible_states.append(state)
        possible_states = sorted(possible_states)

        table = PrettyTable()

        for index, frequency_dict in enumerate(db.state_frequency_dicts):
            row = []
            row.append(index)
            for state in possible_states:
                if state in frequency_dict:
                    row.append(frequency_dict[state])
                else:
                    row.append(0)
            table.add_row(row)
            
        possible_states.insert(0, "JStack #")
        table.field_names = possible_states

        analysis_file_path = ".ajs/analysis.txt"
        Utils.append_to_file(analysis_file_path, thread_state_frequency + str(table) + "\n\n")

    @staticmethod
    def output_cpu_consuming_threads_jstack(db, cpu_wise_sorted_thread_indexes):
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (JSTACK)"
        cpu_consuming_threads_header = Utils.borderify_text(cpu_consuming_threads_header, 1) + "\n\n"

        cpu_consuming_threads_text = ""
        for cpu_wise_sorted_thread_index in cpu_wise_sorted_thread_indexes:
            nid = cpu_wise_sorted_thread_index["nid"]
            time = cpu_wise_sorted_thread_index["time"]
            db_thread = db.threads[nid]

            first_thread_instance = db_thread[0]
            last_thread_instance = db_thread[-1]

            cpu_consuming_threads_text += "Thread NID: {} CPU: {}\n".format(int(first_thread_instance.nid), time)
            cpu_consuming_threads_text += "First Occurrence:\n" 
            cpu_consuming_threads_text += first_thread_instance.text + "\n"
            cpu_consuming_threads_text += "Last Occurrence:\n"
            cpu_consuming_threads_text += last_thread_instance.text + "\n\n"

        analysis_file_path = ".ajs/analysis.txt"
        Utils.append_to_file(analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    def output_cpu_consuming_threads_top(db):
        cpu_consuming_threads_header = "CPU CONSUMING THREADS (TOP)"
        cpu_consuming_threads_header = Utils.borderify_text(cpu_consuming_threads_header, 1) + "\n\n"

        cpu_consuming_threads_text = ""
        for thread in db.top_cpu_intensive_threads:
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

        analysis_file_path = ".ajs/analysis.txt"
        Utils.append_to_file(analysis_file_path, cpu_consuming_threads_header + cpu_consuming_threads_text)

    @staticmethod
    def output_jstacks_in_one_file(config, db, num_jstacks):
        output_jstack_file_path = ".ajs/jstacks.txt"
        output_jstack_text = ""
        for jstack_index in range(num_jstacks):
            for process_id in db.process_id_vs_name:
                jstack = Connectors.read_jstack(config, jstack_index, process_id)
                jstack_header = "JStack #{} Process ID: {}".format(jstack_index, process_id)
                jstack_header = Utils.borderify_text(jstack_header, 1) + "\n\n"
                output_jstack_text += jstack_header
                output_jstack_text += jstack + "\n\n"

        Utils.append_to_file(output_jstack_file_path, output_jstack_text)

    @staticmethod
    @Utils.benchmark("upload data to azure")
    def upload_output_files(config):
        blob_name = config.session_id
        Utils.upload_to_azure(blob_name, "analysis", ".ajs/analysis.txt")
        Utils.upload_to_azure(blob_name, "jstacks", ".ajs/jstacks.txt")
