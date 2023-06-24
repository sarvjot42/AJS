import re
import os
import time
import signal
import traceback
import subprocess
import logging
import warnings

logging.basicConfig(filename='.ajs/warnings.log', level=logging.WARNING)
warnings.filterwarnings("ignore", message=".*Python 2 is no longer supported by the Python core team.*")

from ajs_data import Thread 
from prettytable import PrettyTable
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

class AJSInterface:
    @staticmethod
    def create_if_not_there(file_path):
        if not os.path.exists(file_path):
            os.makedirs(file_path)

    @staticmethod
    def remove_if_there(file_path):
        if os.path.exists(file_path):
            os.system("rm -rf " + file_path)

    @staticmethod
    def write_to_file(file_path, data):
        AJSInterface.create_if_not_there(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            f.write(data)

    @staticmethod
    def append_to_file(file_path, data):
        AJSInterface.create_if_not_there(os.path.dirname(file_path))
        with open(file_path, "a") as f:
            f.write(data)

    @staticmethod
    def subprocess_call(command_list):
        result = subprocess.Popen(command_list, stdout=subprocess.PIPE)
        output, _ = result.communicate()
        return output.strip()

    @staticmethod
    def setup_interrupt():
        def handle_interrupt(signal, thread):
            exit("\nReceived SIGINT, exiting")

        signal.signal(signal.SIGINT, handle_interrupt)

    @staticmethod
    def get_java_processes(ajs_db):
        output = AJSInterface.subprocess_call(["ps", "-e"])
        lines = output.split(b"\n")

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
        AJSInterface.remove_if_there(".ajs/analysis.txt")
        AJSInterface.remove_if_there(".ajs/jstacks.txt")

    @staticmethod
    def get_jstack_of_java_process(process_id):
        jstack = AJSInterface.subprocess_call(["jstack", str(process_id)])
        return jstack 

    @staticmethod 
    def handle_jstack_file_input(ajs_config, ajs_db):
        jstack_file_input_path = ajs_config.jstack_input_file_path

        if jstack_file_input_path is None:
            exit("\nNo jstack file path provided in config file")

        if not os.path.exists(jstack_file_input_path):
            exit("\nInvalid jstack file path provided in config file")

        ajs_db.add_process("unknown_process_id", "unknown_process")
        num_jstacks = AJSInterface.parse_jstack_file_input(ajs_config, jstack_file_input_path)
        return num_jstacks

    @staticmethod
    def parse_jstack_file_input(ajs_config, jstack_file_input_path):
        jstack_index = 0
        jstack_last_line_regex = r"(?m)(JNI global ref.*$)"
        buffered_jstacks = AJSInterface.file_buffer_reader(jstack_file_input_path, jstack_last_line_regex)

        for jstack in buffered_jstacks:
            AJSInterface.output_jstack(ajs_config, jstack_index, jstack, "unknown_process_id")
            jstack_index += 1

        num_jstacks = jstack_index
        return num_jstacks

    @staticmethod
    def file_buffer_reader(file_input_path, separator_regex):
        buffer = ""
        one_mb = 1024 * 1024

        with open(file_input_path) as file:
            while True:
                data_chunk = file.read(one_mb)
                if not data_chunk:
                    break
                buffer += data_chunk

                sep = re.search(separator_regex, buffer)
                if sep is not None:
                    sep_index = sep.end()
                    read_data = buffer[:sep_index + 1]
                    buffer = buffer[sep_index + 1:]
                    yield read_data 

    @staticmethod
    def output_jstack(ajs_config, jstack_index, jstack, process_id):
        jstack_file_path = AJSInterface.get_jstack_file_path(ajs_config, jstack_index, process_id)
        AJSInterface.write_to_file(jstack_file_path, jstack)

    @staticmethod 
    def handle_jstack_generation(ajs_config, ajs_db):
        num_jstacks = ajs_config.num_jstacks
        delay_bw_jstacks = ajs_config.delay_bw_jstacks

        AJSInterface.get_java_processes(ajs_db)

        for jstack_index in range(num_jstacks):
            for process_id in ajs_db.process_id_vs_name:
                jstack = AJSInterface.get_jstack_of_java_process(process_id)
                AJSInterface.output_jstack(ajs_config, jstack_index, jstack, process_id)

            if jstack_index != num_jstacks - 1:
                time.sleep(delay_bw_jstacks / 1000)

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
        if ajs_config.thread_state_frequency_table is False:
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
        blob_name = ajs_config.session_id
        AJSInterface.upload_to_azure(blob_name, "analysis", ".ajs/analysis.txt")
        AJSInterface.upload_to_azure(blob_name, "jstacks", ".ajs/jstacks.txt")

    @staticmethod
    def upload_to_azure(blob_name, container_name, upload_file_path):
        if os.path.exists(upload_file_path) is False:
            return

        account_url = "https://sarvjot.blob.core.windows.net"

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
