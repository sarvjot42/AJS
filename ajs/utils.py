import os
import time
import signal
# import traceback
import subprocess
from sys import platform
from datetime import datetime
from resource import getrusage, RUSAGE_SELF

# Uncomment for cleaner output in python2
# import logging
# import warnings
# logging.basicConfig(filename='.ajs/warnings.log', level=logging.WARNING)
# warnings.filterwarnings("ignore", message=".*Python 2 is no longer supported by the Python core team.*")

# from azure.identity import DefaultAzureCredential
# from azure.storage.blob import BlobServiceClient

from context import Context 
from legacy_configuration import Config

class Utils:
    @staticmethod
    def diff_between_time_stamps(time_stamp_a, time_stamp_b):
        datetime_a = datetime.strptime(time_stamp_a, "%Y-%m-%d %H:%M:%S")
        datetime_b = datetime.strptime(time_stamp_b, "%Y-%m-%d %H:%M:%S")

        time_difference = datetime_b - datetime_a
        return time_difference

    @staticmethod
    def borderify_text_and_update_contents(text, current_layer, output_file, max_layer=0, sep='*'):
        if current_layer == 0:
            if max_layer != 0:
                Context.file_contents.append([text, max_layer, output_file])
            text = text.center(80, sep)
            return text

        max_layer = max(max_layer, current_layer)
        inner_text = Utils.borderify_text_and_update_contents(text, current_layer - 1, output_file, max_layer, sep)

        lines = inner_text.split("\n")
        column_width = len(lines[0]) + 2
        horizontal_border = sep * column_width

        new_text = horizontal_border
        for line in lines:
            new_text += "\n" + sep + line + sep
        new_text += "\n" + horizontal_border

        return new_text

    @staticmethod
    def benchmark_time(label):
        def decorator_function(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()

                time_taken = "{:.3f}".format(end - start)

                if Config.do_benchmark is True:
                    print("SCRIPT TIME BENCHMARKING:\t" + time_taken + "s '" + label + "'")
                return result
            return wrapper
        return decorator_function

    @staticmethod
    def benchmark_memory():
        if Config.do_benchmark is False:
            return

        rusage = getrusage(RUSAGE_SELF)
        max_memory_usage_mb = 0

        if platform == "darwin":
            max_memory_usage_mb = rusage.ru_maxrss / 1024 / 1024
        else:
            max_memory_usage_mb = rusage.ru_maxrss / 1024 

        max_memory_usage_mb = "{:.3f}".format(max_memory_usage_mb)
        print("\nSCRIPT MEMORY FOOTPRINT:\t" + str(max_memory_usage_mb) + "MB 'max memory usage'")

    @staticmethod
    def benchmark_cpu():
        if Config.do_benchmark is False:
            return

        rusage = getrusage(RUSAGE_SELF)
        cpu_time = rusage.ru_utime + rusage.ru_stime

        cpu_time = "{:.3f}".format(cpu_time)
        print("SCRIPT CPU UTILISATION:\t\t" + str(cpu_time) + "s '[user + system] cpu time'")

    @staticmethod
    def benchmark_pod_cpu():
        if Config.do_benchmark is False or Config.file_input is True:
            return

        pod_cpu_time = "{:.3f}".format(Context.system_calls_total_cpu_time)
        print("\nPOD CPU UTILISATION:\t" + str(pod_cpu_time) + "s '[user + system] cpu time'")

    @staticmethod
    def convert_number_to_alphabet(number):
        alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return alphabets[number]

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
        Utils.create_if_not_there(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            f.write(data)

    @staticmethod
    def append_to_file(file_path, data):
        Utils.create_if_not_there(os.path.dirname(file_path))
        with open(file_path, "a") as f:
            f.write(data)

    @staticmethod
    def prepend_to_file(file_path, data):
        Utils.create_if_not_there(os.path.dirname(file_path))
        with open(file_path, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(data + content)

    @staticmethod
    def parse_time_from_row(row):
        row = row.replace("s", " ").replace("m", " ")
        time_min = float(row.split(" ")[0])
        time_sec = float(row.split(" ")[1])
        return time_min * 60 + time_sec

    @staticmethod
    def subprocess_call(command_list):
        result = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = result.communicate()

        if result.returncode != 0:
            err_string = "Error in subprocess call: "
            err_string += " ".join(command_list) + "\n"
            err_string += err.decode("utf-8")
            raise Exception(err_string)

        output = output.decode("utf-8")

        output = output.strip().replace("\r", "")
        time_output = output.split("\n\n")[-1]
        output = output.replace(time_output, "")

        sys_time = time_output.split("\n")[-1].split("\t")[-1]
        sys_time = Utils.parse_time_from_row(sys_time)

        user_time = time_output.split("\n")[-2].split("\t")[-1]
        user_time = Utils.parse_time_from_row(user_time)

        Context.system_calls_total_cpu_time += sys_time + user_time

        return output

    @staticmethod
    def setup_interrupt():
        def handle_interrupt(signal, thread):
            exit("\nReceived SIGINT, exiting\n")

        signal.signal(signal.SIGINT, handle_interrupt)

    # @staticmethod
    # def upload_to_azure(blob_name, container_name, upload_file_path):
    #     if os.path.exists(upload_file_path) is False:
    #         return
    #
    #     account_url = "https://sarvjot.blob.core.windows.net"
    #
    #     try:
    #         default_credential = DefaultAzureCredential()
    #         blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    #         blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    #
    #         with open(upload_file_path, "rb") as f:
    #             data = f.read()
    #             blob_client.upload_blob(data)
    #
    #         Context.files_uploaded_to_azure.append(blob_client.url)
    #
    #     except Exception as ex:
    #         print(traceback.format_exc())
