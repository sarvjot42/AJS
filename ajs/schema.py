import re
import json
import argparse
import datetime
from argparse import RawTextHelpFormatter

class Config:
    do_benchmark = None 

    def __init__(self):
        args = Config.setup_cli()

        self.session_id = Config.generate_session_id()
        self.thread_states = [
            { "regex": ".*RUNNABLE.*", "tag": "RUNNABLE" }, 
            { "regex": ".*BLOCKED.*", "tag": "BLOCKED" },
            { "regex": ".*WAITING.*", "tag": "WAITING" },
            { "regex": ".*TIMED_WAITING.*", "tag": "TIMED_WAITING" }
        ]

        Config.setup_config(self, args)

    @staticmethod
    def setup_cli():
        cli = argparse.ArgumentParser(description="Analyse JStacks, a tool to analyze java thread dumps\nConfigure settings in 'config.json', Sample config file is given in 'config.sample.json'", formatter_class=RawTextHelpFormatter)

        cli.add_argument("-f", "--jstack-file-input", action="store_true", help="Use configured JStack [f]iles as input")
        cli.add_argument("-n", "--num-jstacks", type=int, metavar="", default=5, help="[n]umber of JStacks, default is 5 (applicable when -f is not used)")
        cli.add_argument("-d", "--delay-bw-jstacks", type=int, metavar="", default=1000, help="[d]elay between two JStacks in ms, default is 1000 (applicable when -f is not used)")

        cli.add_argument("-F", "--filter-out", action="store_true", help="[F]ilter out configured threads from the jstack")
        cli.add_argument("-S", "--search-tokens", action="store_true", help="[S]earch for configured tokens in the jstack")
        cli.add_argument("-C", "--classify-threads", action="store_true", help="[C]lassify threads based on configured regexes")
        cli.add_argument("-R", "--repetitive-stack-trace", action="store_true", help="Detect [R]epetitive stack traces in threads")
        cli.add_argument("-I", "--cpu-intensive-threads", action="store_true", help="Output most CPU [I]ntensive threads, in descending order of CPU time")
        cli.add_argument("-T", "--thread-state-frequency-table", action="store_true", help="Output [T]hread state frequency table for all jstacks")
        cli.add_argument("-B", "--benchmark", action="store_true", help="Run in [B]enchmark mode")

        args = cli.parse_args()
        return args

    @staticmethod
    def generate_session_id():
        session_name = raw_input("Name your debugging session: ")
        time_stamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        session_id = session_name + "_" + time_stamp
        return session_id

    @staticmethod
    def setup_config(config, args):
        with open("config.json") as file:
            config_file = json.load(file)

        try:
            Config.setup_token_config(config, args, config_file)
            Config.setup_filter_config(config, args, config_file)
            Config.setup_classification_config(config, args, config_file)
            Config.setup_jstack_file_input_config(config, args, config_file)

            config.thread_state_frequency_table = args.thread_state_frequency_table
            config.cpu_intensive_threads = args.cpu_intensive_threads
            config.repetitive_stack_trace = args.repetitive_stack_trace

            Config.do_benchmark = args.benchmark

        except KeyError as e:
            exit("\nKey " + str(e) + " not found in config file, please refer to the sample config file")

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

    @staticmethod
    def setup_jstack_file_input_config(config, args, config_file):
        if args.jstack_file_input is True:
            config.jstack_file_path = str(config_file["jstack_file_path"])
        else:
            config.jstack_file_path = None
            config.num_jstacks = args.num_jstacks
            config.delay_bw_jstacks = args.delay_bw_jstacks

class Database:
    def __init__(self, config):
        self.threads = {}
        self.token_frequency = {}
        self.process_id_vs_name = {}
        self.state_frequency_dicts = [] 

        tokens = config.tokens
        if tokens is not None:
            for token in tokens:
                self.token_frequency[token["text"]] = 0

    def found_token(self, token):
        self.token_frequency[token["text"]] += 1

    def add_process(self, process_id, process_name):
        self.process_id_vs_name[process_id] = process_name

class Thread:
    def __init__(self, text, process_id):
        id_regex = r"\#(\d+)\s"
        cpu_regex = r"cpu\s*=\s*(\d+.\d+)ms"
        elapsed_regex = r"elapsed\s*=\s*(\d+\.\d+)s"
        thread_state_regex = r"java\.lang\.Thread\.State\:\s*(.*)"
        thread_name_regex = r"^\s*(.*)\s+\#\d+\s+daemon\s+prio\=5\s+os_prio\=0"

        id = re.search(id_regex, text)
        cpu = re.search(cpu_regex, text)
        elapsed = re.search(elapsed_regex, text)
        thread_state = re.search(thread_state_regex, text)
        thread_name = re.search(thread_name_regex, text)

        self.tags = []
        self.text = text
        self.process_id = process_id
        self.id = float(id.group(1)) if id is not None else -1
        self.cpu = float(cpu.group(1)) if cpu is not None else -1
        self.elapsed = float(elapsed.group(1)) if elapsed is not None else -1
        self.thread_state = thread_state.group(1) if thread_state is not None else "unknown_state"
        self.thread_name = thread_name.group(1) if thread_name is not None else "unknown_thread"
