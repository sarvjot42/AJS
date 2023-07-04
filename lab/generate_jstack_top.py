import os
import subprocess
from time import sleep

def subprocess_call(command_list):
    result = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = result.communicate()

    return { "output": output.strip(), "err": err }

def get_java_processes_id(application_name):
    output = subprocess_call(["ps", "-e"])["output"]
    lines = output.split(b"\n")

    for line in lines:
        if application_name in line:
            cols = line.split()
            process_id = cols[0]

            return process_id

def append_to_file(file_path, data):
    with open(file_path, "a") as f:
        f.write(data)

def reset_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("")

def store_jstacks(jstack_target_file_path):
    reset_file(jstack_target_file_path)
    process_id = get_java_processes_id("schoolApplication")

    for _ in range(0, 3):
        jstack = subprocess_call(["jstack", process_id])["output"]
        append_to_file(jstack_target_file_path, jstack.decode("utf-8") + "\n\n")
        sleep(10)

def concurrency_check():
    print("Concurrency check")

store_jstacks("/Users/sarvjotsingh/dev/AnalyseJStack/sample_data/jstack.txt")
concurrency_check()
