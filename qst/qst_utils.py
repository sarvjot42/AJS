import json
import argparse
import datetime

class QSTUtils:
    @staticmethod
    def generate_session_id():
        session_name = raw_input("Name your debugging session: ")
        time_stamp = QSTUtils.get_time_stamp()
        session_id = session_name + "_" + time_stamp
        return session_id

    @staticmethod
    def get_time_stamp():
        time_stamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        return time_stamp

    @staticmethod
    def convert_number_to_alphabet(number):
        alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return alphabets[number]

    @staticmethod
    def setup_parser():
        parser = argparse.ArgumentParser(
            description="Search for tokens in stack traces of all running Java processes"
        )

        parser.add_argument(
            "tokens", nargs="+", help="Enter tokens to search in stack traces"
        )
        parser.add_argument(
            "-a",
            "--print-all-matches",
            action="store_true",
            help="Print [a]ll stack threads for tokens",
        )
        parser.add_argument(
            "-f",
            "--jstack-file-input",
            action="store_true",
            help="Read JStacks from [f]ile instead of running JStack command",
        )
        parser.add_argument(
            "-d",
            "--delay-bw-jstacks",
            metavar="",
            type=int,
            default=1000,
            help="[D]elay between two consecutive JStacks in milliseconds, default is 1000",
        )
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

        if config_data.get("jstack_input_file_path") is not None:
            parsed_config_data["jstack_input_file_path"] = str(config_data["jstack_input_file_path"])
        else:
            parsed_config_data["jstack_input_file_path"] = None

        return parsed_config_data
