import re
import os
import time
import signal
import logging
import warnings
import traceback
import subprocess
from sys import platform
from resource import getrusage, RUSAGE_SELF
from schema import Config

# send logs to a particular file and ignore Python2 warnings
# do this before importing the problem-causing libraries
logging.basicConfig(filename='.ajs/warnings.log', level=logging.WARNING)
warnings.filterwarnings("ignore", message=".*Python 2 is no longer supported by the Python core team.*")

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

class Utils:
    @staticmethod
    def benchmark(label):
        def decorator_function(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = func(*args, **kwargs)
                end = time.time()

                time_taken = "{:.3f}".format(end - start)

                if Config.do_benchmark is True:
                    print("TIME BENCHMARKING:\t" + label + " took " + time_taken + "s")
                return result
            return wrapper
        return decorator_function

    @staticmethod
    def memory_benchmarking(stage):
        rusage = getrusage(RUSAGE_SELF)
        max_memory_usage_mb = 0

        if platform == "darwin":
            max_memory_usage_mb = rusage.ru_maxrss / 1024 / 1024
        else:
            max_memory_usage_mb = rusage.ru_maxrss / 1024 

        print("MEMORY BENCHMARKING:\t" + stage + " Max RAM usage: " + str(max_memory_usage_mb) + " MB")


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
    def file_buffer_reader(file_path, separator_regex):
        buffer = ""
        one_mb = 1024 * 1024

        with open(file_path) as file:
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
