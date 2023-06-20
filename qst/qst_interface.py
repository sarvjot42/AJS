import re
import os
import time
import signal
import subprocess
from qst_data import StackFrame

class QSTInterface:
    @staticmethod
    def write_to_file(file_path, data):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            f.write(data)

    @staticmethod
    def append_to_file(file_path, data):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "a") as f:
            f.write(data)

    @staticmethod
    def setup_interrupt():
        def handle_interrupt(signal, thread):
            print("\nReceived SIGINT, exiting")
            exit(0)

        signal.signal(signal.SIGINT, handle_interrupt)

    @staticmethod
    def get_java_processes(qst_data):
        result = subprocess.Popen(["ps", "-e"], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        lines = output.strip().split(b"\n")

        for line in lines:
            if b"java" in line:
                cols = line.split()
                process_id = cols[0]
                process_name = ""
                for i in range(3, len(cols)):
                    process_name = process_name + cols[i].decode("utf-8") + " "
                qst_data.add_process(process_id, process_name)

    @staticmethod
    def reset_output_directory():
        if os.path.exists(".qst/latest_jstack_categories"): 
            os.system("rm -rf .qst/latest_jstack_categories")
        if os.path.exists(".qst/matching.txt"): 
            os.system("rm -rf .qst/matching.txt")
        if os.path.exists(".qst/cpu_consuming.txt"): 
            os.system("rm -rf .qst/cpu_consuming.txt")

    @staticmethod
    def get_stack_trace_of_java_process(process_id):
        result = subprocess.Popen(["jstack", str(process_id)], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        stack_trace = output.strip()
        return stack_trace

    @staticmethod 
    def handle_jstack_file_input(qst_data):
        jstack_file_input_path = qst_data.config["jstack_input_file_path"]

        if jstack_file_input_path is None:
            print("No jstack file path provided in config file")
            exit(0)
        else:
            if not os.path.exists(jstack_file_input_path):
                print("Invalid jstack file path provided in config file")
                exit(0)
            else:
                qst_data.add_process("unknown_process_id", "unknown_process")
                num_jstacks = QSTInterface.parse_jstack_file_input(qst_data, jstack_file_input_path)
                return num_jstacks

    @staticmethod
    def parse_jstack_file_input(qst_data, jstack_file_input_path):
        jstack_index = 0
        buffered_jstacks = QSTInterface.buffered_reader_jstacks(jstack_file_input_path)

        for jstack in buffered_jstacks:
            QSTInterface.output_parsed_jstack(qst_data, jstack_index, jstack)
            jstack_index += 1

        num_jstacks = jstack_index
        return num_jstacks

    @staticmethod
    def buffered_reader_jstacks(jstack_file_input_path):
        jstack_last_line_regex = r"(?m)(JNI global refs.*$)"
        current_jstack_text = ""

        one_mb = 1024 * 1024

        with open(jstack_file_input_path) as file:
            while True:
                chunk = file.read(one_mb)
                if not chunk:
                    break
                current_jstack_text += chunk

                jstack_last_line = re.search(jstack_last_line_regex, current_jstack_text)
                if jstack_last_line is not None:
                    jstack_last_line_index = jstack_last_line.end()
                    jstack = current_jstack_text[:jstack_last_line_index + 1]
                    current_jstack_text = current_jstack_text[jstack_last_line_index + 1:]
                    yield jstack

    @staticmethod
    def output_parsed_jstack(qst_data, jstack_index, jstack):
        jstack_file_path = QSTInterface.get_jstack_file_path(qst_data, jstack_index, "unknown_process_id")
        QSTInterface.write_to_file(jstack_file_path, jstack)

    @staticmethod 
    def handle_jstack_generation(qst_data, delay_bw_jstacks, num_jstacks):
        QSTInterface.get_java_processes(qst_data)

        for jstack_index in range(num_jstacks):
            QSTInterface.output_generated_jstacks(qst_data, jstack_index)
            time.sleep(delay_bw_jstacks / 1000)

    @staticmethod
    def output_generated_jstacks(qst_data, jstack_index):
        for process_id in qst_data.process_id_vs_name:
            stack_trace = QSTInterface.get_stack_trace_of_java_process(process_id)
            jstack_file_path = QSTInterface.get_jstack_file_path(qst_data, jstack_index, process_id)

            QSTInterface.write_to_file(jstack_file_path, stack_trace.decode("utf-8"))

    @staticmethod
    def read_jstack(qst_data, jstack_index, process_id):
        jstack_file_path = QSTInterface.get_jstack_file_path(qst_data, jstack_index, process_id)

        with open(jstack_file_path, "r") as f:
            jstack = f.read()
            return jstack

    @staticmethod
    def get_jstack_file_path(qst_data, jstack_index, process_id):
        jstack_output_path = ".qst/jstacks/" + qst_data.session_id
        jstack_file_path = jstack_output_path + "/Cycle-" + str(jstack_index) + "/" + process_id + ".txt"
        return jstack_file_path

    @staticmethod
    def parse_threads_from_jstack(jstack, process_id):
        jstack_text = jstack.split("\n\n")
        threads = map(lambda text: StackFrame(text, process_id), jstack_text)
        return threads

    @staticmethod
    def output_matching_threads(matching_threads_text):
        matching_threads_path = ".qst/matching.txt"
        QSTInterface.append_to_file(matching_threads_path, str(matching_threads_text))

    @staticmethod
    def output_categorized_threads(categorized_threads):
        for state in categorized_threads:
            category_path = ".qst/latest_jstack_categories/" + state 
            
            threads = categorized_threads[state]
            for thread in threads:
                for tag in thread.tags:
                    file_path = category_path + "/" + tag + ".txt"
                    QSTInterface.append_to_file(file_path, thread.text + "\n\n")

    @staticmethod
    def output_cpu_consuming_threads(qst_data):
        qst_data.cpu_consuming_threads.sort(key=lambda thread: thread.cpu_time, reverse=True)

        cpu_consuming_threads_text = "" 
        for thread in qst_data.cpu_consuming_threads:
            cpu_consuming_threads_text += thread.text + "\n\n"

        cpu_consuming_threads_path = ".qst/cpu_consuming.txt"
        QSTInterface.write_to_file(cpu_consuming_threads_path, cpu_consuming_threads_text)
