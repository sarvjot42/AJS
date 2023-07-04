import os
import subprocess
import threading
from time import sleep

target_process_id = None

def subprocess_call(command_list):
    result = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = result.communicate()

    return { "output": output.strip(), "err": err }

def get_java_processes_id(application_name):
    global target_process_id

    output = subprocess_call(["ps", "-ef"])["output"]
    lines = output.split(b"\n")

    for line in lines:
        if application_name in line:
            cols = line.split()
            process_id = cols[1]

            target_process_id = process_id
            break

def append_to_file(file_path, data):
    with open(file_path, "a") as f:
        f.write(data)

def reset_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("")

def store_jstacks(jstack_target_file_path):
    reset_file(jstack_target_file_path)

    for i in range(0, 3):
        jstack = subprocess_call(["jstack", str(target_process_id)])["output"]
        append_to_file(jstack_target_file_path, jstack.decode("utf-8") + "\n\n")

        if(i < 2):
            sleep(10)

def store_top(top_target_file_path):
    reset_file(top_target_file_path)

    command_list = ["top", "-H", "-b", "-n", "2", "-d", "2", "-p", str(target_process_id)]
    result = subprocess_call(command_list)

    if result["err"] != "":
        print(result["err"])
    else:
        top_output = result["output"]
        append_to_file(top_target_file_path, top_output.decode("utf-8") + "\n\n")

sample_data_folder = "/home/sarvjot/workspace/programming/dev/AJS/sample_data"
index = "_without_index"
java_process_id_thread = threading.Thread(target=get_java_processes_id, args=("schoolApplication",))

java_process_id_thread.start()
java_process_id_thread.join()

jstack_thread = threading.Thread(target=store_jstacks, args=(sample_data_folder + "/jstack" + index + ".txt",))
top_thread = threading.Thread(target=store_top, args=(sample_data_folder + "/top" + index + ".txt",))

jstack_thread.start()
top_thread.start()

jstack_thread.join()
top_thread.join()
