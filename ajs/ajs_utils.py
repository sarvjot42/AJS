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
    def setup_cli():
        cli = argparse.ArgumentParser(description="Analyze JStacks, a tool to analyze java thread dumps\nConfigure settings in 'ajs_config.json', Sample config file is given in 'ajs_config.sample.json'", formatter_class=RawTextHelpFormatter)

        cli.add_argument("-f", "--jstack-file-input", action="store_true", help="Use configured JStack [f]iles as input")
        cli.add_argument("-n", "--num-jstacks", type=int, metavar="", default=5, help="[n]umber of JStacks, default is 5 (applicable when -f is not used)")
        cli.add_argument("-d", "--delay-bw-jstacks", type=int, metavar="", default=1000, help="[d]elay between two JStacks in ms, default is 1000 (applicable when -f is not used)")

        cli.add_argument("-F", "--filter-out", action="store_true", help="[F]ilter out configured threads from the jstack")
        cli.add_argument("-S", "--search-tokens", action="store_true", help="[S]earch for configured tokens in the jstack")
        cli.add_argument("-C", "--classify-threads", action="store_true", help="[C]lassify threads based on configured regexes")
        cli.add_argument("-I", "--cpu-intensive-threads", action="store_true", help="Output most CPU [I]ntensive threads, in descending order of CPU time")
        cli.add_argument("-R", "--repetitive-stack-trace", action="store_true", help="Detect [R]epetitive stack traces in threads")
        cli.add_argument("-T", "--thread-state-frequency-table", action="store_true", help="Output [T]hread state frequency table for all jstacks")

        return cli 

    @staticmethod
    def setup_config(config, args):
        with open("ajs_config.json") as file:
            config_file = json.load(file)

        try:
            AJSUtils.setup_input_config(config, args, config_file)
            AJSUtils.setup_token_config(config, args, config_file)
            AJSUtils.setup_filter_config(config, args, config_file)
            AJSUtils.setup_classification_config(config, args, config_file)

            config.thread_state_frequency_table = args.thread_state_frequency_table
            config.cpu_intensive_threads = args.cpu_intensive_threads
            config.repetitive_stack_trace = args.repetitive_stack_trace

        except KeyError as e:
            exit("\nKey " + str(e) + " not found in config file, please refer to the sample config file")

    @staticmethod
    def setup_input_config(config, args, config_file):
        if args.jstack_file_input is True:
            config.jstack_input_file_path = str(config_file["jstack_input_file_path"])
        else:
            config.jstack_input_file_path = None
            config.num_jstacks = args.num_jstacks
            config.delay_bw_jstacks = args.delay_bw_jstacks

    @staticmethod
    def setup_token_config(config, args, config_file):
        if args.search_tokens is True:
            tokens = []
            for token in config_file["tokens"]:
                token_text = str(token["text"])
                output_all_matches = token["output_all_matches"]
                tokens.append({"text": token_text, "output_all_matches": output_all_matches})
            config.tokens = tokens
        else:
            config.tokens = None

    @staticmethod
    def setup_filter_config(config, args, config_file):
        if args.filter_out is True:
            unwanted_tokens = []
            for unwanted_token in config_file["filter_out"]:
                unwanted_tokens.append(str(unwanted_token["regex"]))
            config.filter_out = unwanted_tokens
        else:
            config.filter_out = None

    @staticmethod
    def setup_classification_config(config, args, config_file):
        if args.classify_threads is True:
            classification_items = []
            for items in config_file["classification"]:
                classification_items.append({"regex": str(items["regex"]), "tag": str(items["tag"])})
            config.classification = classification_items
        else:
            config.classification = None
