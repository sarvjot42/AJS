import re
import json
import time
import heapq
import argparse
from multipledispatch import dispatch

class QSTUtils:
    @staticmethod
    @dispatch(bool, int, int, int)
    def logger(log_stats, beg_newlines, cnt_lines, end_newlines):
        if not log_stats:
            return

        for _ in range(beg_newlines):
            print('')
        for _ in range(cnt_lines):
            print("---------------------------------------------------------------------------")
        for _ in range(end_newlines):
            print('')

    @staticmethod
    @dispatch(bool, str)
    def logger(log_stats, message):
        if not log_stats:
            return

        print(message)

    @staticmethod
    def benchmark(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            time_taken = "{:.3f}".format(end - start)

            label = kwargs.get('label', func.__name__)
            log_stats = kwargs.get('log_stats')

            QSTUtils.logger(log_stats, "{} took {} seconds".format(label, time_taken))
            return result
        return wrapper

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
        # log_stats is a boolean argument, which assumes value True if passed, else False
        parser.add_argument(
            "-l",
            "--log-stats",
            action="store_true",
            help="[L]og benchmarking stats for various stages",
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

        if config_data.get("storage_location") is not None and config_data["storage_location"].get("cpu_consuming") is not None:
            parsed_config_data["storage_location"]["cpu_consuming"] = str(config_data["storage_location"]["cpu_consuming"])
        else:
            parsed_config_data["storage_location"]["cpu_consuming"] = ".qst/cpu_consuming.txt"

        return parsed_config_data

    @staticmethod
    def convert_number_to_alphabet(number):
        alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return alphabets[number]

    @staticmethod
    def attach_cpu_time(stack_frames):
        for stack_frame in stack_frames:
            pattern = r'cpu=(\d+(\.\d+)?)ms'
            cpu_time_match = re.search(pattern, stack_frame.text)

            if cpu_time_match:
                cpu_time = float(cpu_time_match.group(1))
                stack_frame.cpu_time = cpu_time

    @staticmethod
    def get_cpu_consuming(k, stack_frames):
        slowest_frames = heapq.nlargest(k, stack_frames, key=lambda frame: frame.cpu_time)
        return slowest_frames

    @staticmethod
    def store_cpu_consuming(stack_frames, qst_data):
        qst_data.cpu_consuming_stack_frames.extend(stack_frames)
