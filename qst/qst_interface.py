import os
import signal
import subprocess
from qst_utils import QSTUtils
from qst_data import StackFrame

class QSTInterface:
    @staticmethod
    def setup_interrupt():
        def handle_interrupt(signal, frame):
            print("\nReceived SIGINT, exiting")
            exit(0)

        # allow exiting the script with Ctrl + C 
        # register the signal handler
        signal.signal(signal.SIGINT, handle_interrupt)

    # Get all active java processes and store them in qst_data.process_id_vs_name
    # Use "ps -e" to get all active processes
    @staticmethod
    @QSTUtils.benchmark
    def get_active_java_processes(qst_data, **kwargs):
        result = subprocess.Popen(["ps", "-e"], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        lines = output.strip().split("\n")

        for line in lines:
            if "java" in line:
                cols = line.split()
                process_id = cols[0]
                process_name = ""
                for i in range(3, len(cols)):
                    process_name = process_name + cols[i] + " "
                qst_data.add_process(process_id, process_name)

    @staticmethod
    def reset_files():
        # remove .qst folder
        if os.path.exists(".qst"): 
            os.system("rm -rf .qst")

    @staticmethod
    @QSTUtils.benchmark
    def store_jstacks(it, qst_data, **kwargs):
        jstack_loc = ".qst/" + qst_data.config["storage_location"]["jstacks"]
        folder_loc = jstack_loc + "/" + QSTUtils.convert_number_to_alphabet(it)
        for process_id in qst_data.process_id_vs_name:
            stack_trace = QSTInterface.get_stack_trace(process_id)
            file_loc = folder_loc + "/" + process_id + ".txt"
            if not os.path.exists(os.path.dirname(file_loc)):
                os.makedirs(os.path.dirname(file_loc))
            with open(file_loc, "w") as f:
                f.write(stack_trace)

    # Get stack frames for a process using jstack, using process_id
    @staticmethod
    def get_stack_trace(process_id):
        result = subprocess.Popen(["jstack", str(process_id)], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        stack_trace = output.strip()
        return stack_trace

    @staticmethod
    def read_jstacks(it, process_id, qst_data):
        jstack_loc = ".qst/" + qst_data.config["storage_location"]["jstacks"]
        folder_loc = jstack_loc + "/" + QSTUtils.convert_number_to_alphabet(it)
        file_loc = folder_loc + "/" + process_id + ".txt"

        with open(file_loc, "r") as f:
            stack_trace = f.read()
            stack_frames_text = stack_trace.split("\n\n")
            stack_frames = map(lambda text: StackFrame(text, process_id), stack_frames_text)
            return stack_frames

    @staticmethod
    def store_matching_frames(matching_frames_text, qst_data):
        matching_loc = ".qst/" + qst_data.config["storage_location"]["matching"]
        if not os.path.exists(os.path.dirname(matching_loc)):
            os.makedirs(os.path.dirname(matching_loc))
        with open(matching_loc, "a") as f:
            f.write(str(matching_frames_text))

    @staticmethod
    def store_categorized_frames(categorized_frames):
        for state in categorized_frames:
            category_loc = ".qst/categories/" + state 
            
            frames = categorized_frames[state]
            for frame in frames:
                for tag in frame.tags:
                    file_loc = category_loc + "/" + tag + ".txt"
                    if not os.path.exists(os.path.dirname(file_loc)):
                        os.makedirs(os.path.dirname(file_loc))
                    with open(file_loc, "a") as f:
                        f.write(frame.text + "\n\n")

    @staticmethod
    @QSTUtils.benchmark
    def store_cpu_consuming_all(qst_data, **kwargs):
        qst_data.cpu_consuming_stack_frames.sort(key=lambda frame: frame.cpu_time, reverse=True)
        text = "" 
        for frame in qst_data.cpu_consuming_stack_frames:
            text += frame.text + "\n\n"

        cpu_consuming_loc = ".qst/" + qst_data.config["storage_location"]["cpu_consuming"]
        if not os.path.exists(os.path.dirname(cpu_consuming_loc)):
            os.makedirs(os.path.dirname(cpu_consuming_loc))
        with open(cpu_consuming_loc, "w") as f:
            f.write(text)
