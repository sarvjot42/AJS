import os
import json
import signal
import argparse
import subprocess

# Schema class for StackFrame
class StackFrame:
    def __init__(self, text, process_id):
        self.text = text
        self.process_id = process_id
        self.tags = []

class QSTUtils:
    @staticmethod
    def reset_files():
        # remove .qst folder
        if os.path.exists(".qst"): 
            os.system("rm -rf .qst")

    @staticmethod
    def store_jstacks(it, qst_data):
        jstack_loc = ".qst/" + qst_data.config["storage_location"]["jstacks"]
        folder_loc = jstack_loc + "/" + QSTUtils.convert_number_to_alphabet(it)
        for process_id in qst_data.process_id_vs_name:
            stack_trace = QSTUtils.get_stack_trace(process_id)
            file_loc = folder_loc + "/" + process_id + ".txt"
            if not os.path.exists(os.path.dirname(file_loc)):
                os.makedirs(os.path.dirname(file_loc))
            with open(file_loc, "w") as f:
                f.write(stack_trace)

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
    def store_matching_frames(matching_frames, qst_data):
        matching_loc = ".qst/" + qst_data.config["storage_location"]["matching"]
        if not os.path.exists(os.path.dirname(matching_loc)):
            os.makedirs(os.path.dirname(matching_loc))
        with open(matching_loc, "a") as f:
            f.write(str(matching_frames))

    @staticmethod
    def store_categorized_frames(categorized_frames):
        for state in categorized_frames:
            category_loc = ".qst/" + state
            
            frames = categorized_frames[state]
            for frame in frames:
                for tag in frame.tags:
                    file_loc = category_loc + "/" + tag + ".txt"
                    if not os.path.exists(os.path.dirname(file_loc)):
                        os.makedirs(os.path.dirname(file_loc))
                    with open(file_loc, "a") as f:
                        f.write(frame.text + "\n\n")

    @staticmethod
    def convert_number_to_alphabet(number):
        alphabets = "abcdefghijklmnopqrstuvwxyz"
        return alphabets[number]

    @staticmethod
    def setup_interrupt():
        def handle_interrupt(signal, frame):
            print("\nReceived SIGINT, exiting")
            exit(0)

        # allow exiting the script with Ctrl + C 
        # register the signal handler
        signal.signal(signal.SIGINT, handle_interrupt)

    @staticmethod
    def setup_parser():
        parser = argparse.ArgumentParser(
            description="Search for tokens in stack traces of all running Java processes"
        )

        # tokens is a positional argument which accepts one or more values
        parser.add_argument(
            "tokens", nargs="+", help="Enter tokens to search in stack traces"
        )
        # print-all is a boolean argument, which assumes value True if passed, else False
        parser.add_argument(
            "-a",
            "--print-all",
            action="store_true",
            help="Print [a]ll stack frames for tokens",
        )
        # delay is an optional argument with default value of 1000 milliseconds
        parser.add_argument(
            "-d",
            "--delay",
            metavar="",
            type=int,
            default=1000,
            help="[D]elay between two consecutive JStacks in milliseconds, default is 1000",
        )
        # num-jstacks is an optional argument with default value of 5 cycles
        parser.add_argument(
            "-n",
            "--num-jstacks",
            metavar="",
            type=int,
            default=5,
            help="[N]umber of JStacks to be processed, default is 5",
        )

        return parser

    @staticmethod
    def load_and_parse_config():
        with open("qst_config.json") as file:
            config_data = json.load(file)

        parsed_config_data = {}

        if config_data.get("not_include") is not None:
            not_include_items = []
            for not_include in config_data["not_include"]:
                not_include_items.append(str(not_include["regex"]))
            parsed_config_data["not_include"] = not_include_items
        else:
            parsed_config_data["not_include"] = []

        if config_data.get("include") is not None:
            include_items = []
            for include in config_data["include"]:
                include_items.append(str(include["regex"]))
            parsed_config_data["include"] = include_items
        else:
            parsed_config_data["include"] = None 

        if config_data.get("classification") is not None:
            classification_items = []
            for items in config_data["classification"]:
                classification_items.append({"regex": str(items["regex"]), "tag": str(items["tag"])})
            parsed_config_data["classification"] = classification_items
        else:
            parsed_config_data["classification"] = []

        parsed_config_data["storage_location"] = {}

        if config_data.get("storage_location") is not None and config_data["storage_location"].get("jstacks") is not None:
            parsed_config_data["storage_location"]["jstacks"] = str(config_data["storage_location"]["jstacks"])
        else:
            parsed_config_data["storage_location"]["jstacks"] = ".qst/jstacks"

        if config_data.get("storage_location") is not None and config_data["storage_location"].get("matching") is not None:
            parsed_config_data["storage_location"]["matching"] = str(config_data["storage_location"]["matching"])
        else:
            parsed_config_data["storage_location"]["matching"] = ".qst/matching.txt"

        return parsed_config_data

    # Get all active java processes and store them in qst_data.process_id_vs_name
    # Use "ps -e" to get all active processes
    @staticmethod
    def get_active_java_processes(qst_data):
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

    # Get stack frames for a process using jstack, using process_id
    @staticmethod
    def get_stack_trace(process_id):
        result = subprocess.Popen(["jstack", str(process_id)], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        stack_trace = output.strip()
        return stack_trace
