import re
import os
import time
import signal
import traceback
import subprocess
from ajs_data import Thread 
from prettytable import PrettyTable
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

class AJSInterface:
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
    def get_java_processes(ajs_db):
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
                ajs_db.add_process(process_id, process_name)

    @staticmethod
    def reset_output_files():
        if os.path.exists(".ajs/analysis.txt"):
            os.system("rm -rf .ajs/analysis.txt")
        if os.path.exists(".ajs/jstacks.txt"):
            os.system("rm -rf .ajs/jstacks.txt")

    @staticmethod
    def get_jstack_of_java_process(process_id):
        result = subprocess.Popen(["jstack", str(process_id)], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        jstack = output.strip()
        return jstack 

    @staticmethod 
    def handle_jstack_file_input(ajs_config, ajs_db):
        jstack_file_input_path = ajs_config.config["jstack_input_file_path"]

        if jstack_file_input_path is None:
            print("No jstack file path provided in config file")
            exit(0)
        else:
            if not os.path.exists(jstack_file_input_path):
                print("Invalid jstack file path provided in config file")
                exit(0)
            else:
                ajs_db.add_process("unknown_process_id", "unknown_process")
                num_jstacks = AJSInterface.parse_jstack_file_input(ajs_config, jstack_file_input_path)
                return num_jstacks

    @staticmethod
    def parse_jstack_file_input(ajs_config, jstack_file_input_path):
        jstack_index = 0
        buffered_jstacks = AJSInterface.buffered_reader_jstacks(jstack_file_input_path)

        for jstack in buffered_jstacks:
            AJSInterface.output_parsed_jstack(ajs_config, jstack_index, jstack)
            jstack_index += 1

        num_jstacks = jstack_index
        return num_jstacks

    @staticmethod
    def buffered_reader_jstacks(jstack_file_input_path):
        jstack_last_line_regex = r"(?m)(JNI global ref.*$)"
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
    def output_parsed_jstack(ajs_config, jstack_index, jstack):
        jstack_file_path = AJSInterface.get_jstack_file_path(ajs_config, jstack_index, "unknown_process_id")
        AJSInterface.write_to_file(jstack_file_path, jstack)

    @staticmethod 
    def handle_jstack_generation(ajs_config, ajs_db):
        num_jstacks = ajs_config.config["num_jstacks"]
        delay_bw_jstacks = ajs_config.config["delay_bw_jstacks"]

        AJSInterface.get_java_processes(ajs_db)

        for jstack_index in range(num_jstacks):
            AJSInterface.output_generated_jstacks(ajs_config, ajs_db, jstack_index)
            if jstack_index != num_jstacks - 1:
                time.sleep(delay_bw_jstacks / 1000)

    @staticmethod
    def output_generated_jstacks(ajs_config, ajs_db, jstack_index):
        for process_id in ajs_db.process_id_vs_name:
            jstack = AJSInterface.get_jstack_of_java_process(process_id)
            jstack_file_path = AJSInterface.get_jstack_file_path(ajs_config, jstack_index, process_id)

            AJSInterface.write_to_file(jstack_file_path, jstack.decode("utf-8"))

    @staticmethod
    def read_jstack(ajs_config, jstack_index, process_id):
        jstack_file_path = AJSInterface.get_jstack_file_path(ajs_config, jstack_index, process_id)

        with open(jstack_file_path, "r") as f:
            jstack = f.read()
            return jstack

    @staticmethod
    def get_jstack_file_path(ajs_config, jstack_index, process_id):
        jstack_output_path = ".ajs/jstacks/" + ajs_config.session_id
        jstack_file_path = jstack_output_path + "/Cycle-" + str(jstack_index) + "/" + process_id + ".txt"
        return jstack_file_path

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
    def output_matching_threads(matching_threads_text):
        analysis_file_path = ".ajs/analysis.txt"
        AJSInterface.append_to_file(analysis_file_path, str(matching_threads_text))

    @staticmethod
    def output_classified_threads(classified_threads):
        classified_threads = sorted(classified_threads, key=lambda thread: str(thread.tags))

        classified_threads_output = "THREADS SORTED BY CATEGORIES\n\n"
        for thread in classified_threads:
            classified_threads_output += "Tags: " + str(thread.tags) + "\n"
            classified_threads_output += thread.text + "\n\n"

        analysis_file_path = ".ajs/analysis.txt"
        AJSInterface.append_to_file(analysis_file_path, classified_threads_output)

    @staticmethod
    def output_repetitive_stack_trace(stack_trace_counter):
        repetitive_stack_trace_output = "REPEATED STACK TRACES:\n\n"
        for stack_trace in stack_trace_counter:
            if stack_trace[1] == 1:
                break
            
            repetitive_stack_trace_output += "Count: " + str(stack_trace[1]) + "\n"
            repetitive_stack_trace_output += stack_trace[0] + "\n\n"
        
        analysis_file_path = ".ajs/analysis.txt"
        AJSInterface.append_to_file(analysis_file_path, repetitive_stack_trace_output)

    @staticmethod
    def output_thread_state_frequency(ajs_config, ajs_db):
        if ajs_config.config["thread_state_frequency_table"] is False:
            return

        thread_state_frequency = "THREAD STATE FREQUENCY:\n\n"

        possible_states = []
        for frequency_dict in ajs_db.state_frequency_dicts:
            for state in frequency_dict:
                if state not in possible_states:
                    possible_states.append(state)
        possible_states = sorted(possible_states)

        table = PrettyTable()

        for index, frequency_dict in enumerate(ajs_db.state_frequency_dicts):
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
        AJSInterface.append_to_file(analysis_file_path, thread_state_frequency + str(table) + "\n\n")

    @staticmethod
    def output_cpu_consuming_threads(ajs_db, cpu_wise_sorted_thread_indexes):
        cpu_consuming_threads_text = "CPU CONSUMING THREADS:\n\n"
        for cpu_wise_sorted_thread_index in cpu_wise_sorted_thread_indexes:
            id = cpu_wise_sorted_thread_index["id"]
            time = cpu_wise_sorted_thread_index["time"]
            db_thread = ajs_db.threads[id]

            first_thread_instance = db_thread[0]
            last_thread_instance = db_thread[-1]

            cpu_consuming_threads_text += "Thread ID: {} CPU: {}\n".format(int(first_thread_instance.id), time)
            cpu_consuming_threads_text += "First Occurrence:\n" 
            cpu_consuming_threads_text += first_thread_instance.text + "\n"
            cpu_consuming_threads_text += "Last Occurrence:\n"
            cpu_consuming_threads_text += last_thread_instance.text + "\n\n"

        analysis_file_path = ".ajs/analysis.txt"
        AJSInterface.append_to_file(analysis_file_path, cpu_consuming_threads_text)

    @staticmethod
    def output_jstacks_in_one_file(ajs_config, ajs_db, num_jstacks):
        output_jstack_file_path = ".ajs/jstacks.txt"
        output_jstack_text = ""
        for jstack_index in range(num_jstacks):
            for process_id in ajs_db.process_id_vs_name:
                jstack = AJSInterface.read_jstack(ajs_config, jstack_index, process_id)
                output_jstack_text += "JStack #{} Process ID: {}\n\n".format(jstack_index, process_id)
                output_jstack_text += jstack + "\n\n"

        AJSInterface.append_to_file(output_jstack_file_path, output_jstack_text)

    @staticmethod
    def upload_output_files(ajs_config):
        AJSInterface.upload_to_azure(ajs_config, "analysis", ".ajs/analysis.txt")
        AJSInterface.upload_to_azure(ajs_config, "jstacks", ".ajs/jstacks.txt")

    @staticmethod
    def upload_to_azure(ajs_config, container_name, upload_file_path):
        account_url = "https://sarvjot.blob.core.windows.net"
        blob_name = ajs_config.session_id

        try:
            default_credential = DefaultAzureCredential()
            blob_service_client = BlobServiceClient(account_url, credential=default_credential)

            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            with open(upload_file_path, "rb") as f:
                data = f.read()
                blob_client.upload_blob(data)

            print(blob_client.url)

        except Exception as ex:
            print(traceback.format_exc())
