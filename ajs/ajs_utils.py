import json
import argparse
import datetime
from argparse import RawTextHelpFormatter

class AJSUtils:
    @staticmethod
    def generate_session_id():
        session_name = raw_input("Name your debugging session: ")
        time_stamp = AJSUtils.get_time_stamp()
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
            description="Analyze JStacks, a tool to analyze java thread dumps\nConfigure settings in 'ajs_config.json', Sample config file is given in 'ajs_config.sample.json'",
            formatter_class=RawTextHelpFormatter
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
        with open("ajs_config.json") as file:
            config_data = json.load(file)

        parsed_config_data = {}

        if config_data.get("tokens") is not None:
            tokens = []
            for token in config_data["tokens"]:
                token_text = str(token["text"])
                output_all_matches = str(token["output_all_matches"])
                if output_all_matches == "true":
                    output_all_matches = True
                else:
                    output_all_matches = False
                tokens.append({"text": token_text, "output_all_matches": output_all_matches})
            parsed_config_data["tokens"] = tokens
        else:
            parsed_config_data["tokens"] = []

        if config_data.get("filter_out") is not None:
            unwanted_tokens = []
            for unwanted_token in config_data["filter_out"]:
                unwanted_tokens.append(str(unwanted_token["regex"]))
            parsed_config_data["filter_out"] = unwanted_tokens 
        else:
            parsed_config_data["filter_out"] = []

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
