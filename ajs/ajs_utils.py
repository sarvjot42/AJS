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
            "-f",
            "--jstack-file-input",
            action="store_true",
            help="Use configured JStack [f]iles as input",
        )
        parser.add_argument(
            "-n",
            "--num-jstacks",
            metavar="",
            type=int,
            default=5,
            help="[N]umber of JStacks to be processed, default is 5",
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
            "-S",
            "--search-tokens",
            action="store_true",
            help="[S]earch for configured tokens in the jstack",
        )
        parser.add_argument(
            "-F",
            "--filter-out",
            action="store_true",
            help="[F]ilter out configured threads from the jstack",
        )
        parser.add_argument(
            "-C",
            "--classify-threads",
            action="store_true",
            help="[C]lassify threads based on configured regexes",
        )
        parser.add_argument(
            "-I",
            "--cpu-intensive-threads",
            action="store_true",
            help="Output most CPU [I]ntensive threads, in descending order of CPU time",
        )

        return parser

    @staticmethod
    def load_config(args):
        filter_out = args.filter_out
        num_jstacks = args.num_jstacks
        search_tokens = args.search_tokens
        delay_bw_jstacks = args.delay_bw_jstacks
        classify_threads = args.classify_threads
        jstack_file_input = args.jstack_file_input 
        cpu_intensive_threads = args.cpu_intensive_threads

        with open("ajs_config.json") as file:
            config_data = json.load(file)

        parsed_config_data = {}

        if jstack_file_input is True and config_data.get("jstack_input_file_path") is not None:
            parsed_config_data["jstack_input_file_path"] = str(config_data["jstack_input_file_path"])
        else:
            parsed_config_data["jstack_input_file_path"] = None
            parsed_config_data["num_jstacks"] = num_jstacks
            parsed_config_data["delay_bw_jstacks"] = delay_bw_jstacks

        if search_tokens is True and config_data.get("tokens") is not None:
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
            parsed_config_data["tokens"] = None 

        if filter_out is True and config_data.get("filter_out") is not None:
            unwanted_tokens = []
            for unwanted_token in config_data["filter_out"]:
                unwanted_tokens.append(str(unwanted_token["regex"]))
            parsed_config_data["filter_out"] = unwanted_tokens 
        else:
            parsed_config_data["filter_out"] = None 

        if classify_threads is True and config_data.get("classification") is not None:
            classification_items = []
            for items in config_data["classification"]:
                classification_items.append({"regex": str(items["regex"]), "tag": str(items["tag"])})
            parsed_config_data["classification"] = classification_items
        else:
            parsed_config_data["classification"] = None 

        parsed_config_data["cpu_intensive_threads"] = cpu_intensive_threads

        return parsed_config_data
