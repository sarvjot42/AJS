import re
import json
import argparse
import datetime

class Config:
    do_benchmark = None 

    def __init__(self):
        args = Config.setup_cli()

        self.session_id = Config.generate_session_id(args.session_name)
        self.jstack_folder_path = ".ajs/jstacks/"
        self.analysis_file_path = ".ajs/analysis.txt"
        self.jstacks_file_path = ".ajs/jstacks.txt"

        Config.setup_config(self, args)

    @staticmethod
    def setup_cli():
        formatter = lambda prog: argparse.HelpFormatter(prog,max_help_position=52)
        cli = argparse.ArgumentParser(description="Analyse JStacks, a tool to analyze java thread dumps. Configure settings in 'config.json', Sample config file is given in 'config.sample.json'", formatter_class=formatter)

        cli.add_argument("session_name", type=str, help="Name of the debugging session")
        cli.add_argument("-b", "--benchmark", action="store_true", help="Run in [b]enchmark mode")
        cli.add_argument("-f", "--file-input", action="store_true", help="Use configured JStack and Top [f]iles as input")

        cli.add_argument("-A", "--full-analysis", action="store_true", help="Perform [A]ll analysis, equivalent to -IOSCRJTF")
        cli.add_argument("-I", "--include-only", action="store_true", help="Only [I]nclude configured threads")
        cli.add_argument("-O", "--filter-out", action="store_true", help="Filter [O]ut configured threads [preference will be given to -I]")
        cli.add_argument("-S", "--search-tokens", action="store_true", help="[S]earch for configured tokens in the jstack")
        cli.add_argument("-C", "--classify-threads", action="store_true", help="[C]lassify threads based on configured regexes")
        cli.add_argument("-R", "--repetitive-stack-trace", action="store_true", help="Detect [R]epetitive stack traces in threads")
        cli.add_argument("-J", "--cpu-consuming-threads-jstack", action="store_true", help="Output most CPU Intensive threads, calculated using [J]stacks [supported in jdk11+]")
        cli.add_argument("-T", "--cpu-consuming-threads-top", action="store_true", help="Output most CPU Intensive threads, calculated using [T]op utility")
        cli.add_argument("-F", "--thread-state-frequency-table", action="store_true", help="Output thread state [F]requency table for all jstacks")

        args = cli.parse_args()

        if (args.full_analysis is True):
            args.include_only = True
            args.filter_out = True
            args.search_tokens = True
            args.classify_threads = True
            args.repetitive_stack_trace = True
            args.cpu_consuming_threads_jstack = True
            args.cpu_consuming_threads_top = True
            args.thread_state_frequency_table = True

        return args

    @staticmethod
    def generate_session_id(session_name):
        time_stamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        session_id = session_name + "_" + time_stamp
        return session_id

    @staticmethod
    def setup_config(config, args):
        with open("config.json") as file:
            config_file = json.load(file)

        try:
            Config.setup_filter_config(config, args, config_file)
            Config.setup_token_config(config, args, config_file)
            Config.setup_classification_config(config, args, config_file)
            Config.setup_input_config(config, args, config_file)

            config.thread_cpu_threshold_limit = config_file["thread_cpu_threshold_limit"] if "thread_cpu_threshold_limit" in config_file else 0.0

            config.thread_state_frequency_table = args.thread_state_frequency_table
            config.cpu_consuming_threads_jstack = args.cpu_consuming_threads_jstack
            config.cpu_consuming_threads_top = args.cpu_consuming_threads_top
            config.repetitive_stack_trace = args.repetitive_stack_trace

            Config.do_benchmark = args.benchmark

        except KeyError as e:
            exit("\nKey " + str(e) + " not found in config file, please refer to the sample config file")

    @staticmethod
    def setup_filter_config(config, args, config_file):
        if args.include_only is True:
            wanted_tokens = []
            for wanted_token in config_file["include_only"]:
                wanted_tokens.append(str(wanted_token["regex"]))
            config.include_only = wanted_tokens
        else:
            config.include_only = None

        if args.filter_out is True:
            unwanted_tokens = []
            for unwanted_token in config_file["filter_out"]:
                unwanted_tokens.append(str(unwanted_token["regex"]))
            config.filter_out = unwanted_tokens
        else:
            config.filter_out = None

    @staticmethod
    def setup_token_config(config, args, config_file):
        if args.search_tokens is True:
            tokens = []
            for token in config_file["search_tokens"]:
                token_text = str(token["text"])
                output_all_matches = token["output_all_matches"]
                tokens.append({"text": token_text, "output_all_matches": output_all_matches})
            config.tokens = tokens
        else:
            config.tokens = None

    @staticmethod
    def setup_classification_config(config, args, config_file):
        if args.classify_threads is True:
            classification_groups = []

            for group in config_file["classification_groups"]:
                group_items = []
                for item in group:
                    tag = str(item["tag"])
                    regex = str(item["regex"])
                    group_items.append({"tag": tag, "regex": regex})
                classification_groups.append(group_items)

            config.classification_groups = classification_groups
        else:
            config.classification_groups = None

    @staticmethod
    def setup_input_config(config, args, config_file):
        config.file_input = args.file_input

        if args.file_input is True:
            config.top_file_path = str(config_file["top_file_path"])
            config.jstack_file_path = str(config_file["jstack_file_path"])
        else:
            config.namespace = str(config_file["namespace"])
            config.pod_name = str(config_file["pod_name"])
            config.container_name = str(config_file["container_name"])
            config.num_jstacks = int(config_file["num_jstacks"]) if "num_jstacks" in config_file else 3 
            config.delay_bw_jstacks = int(config_file["delay_bw_jstacks"]) if "delay_bw_jstacks" in config_file else 10000 

class Database:
    def __init__(self, config):
        self.threads = {}
        self.pod_cpu_time = 0
        self.file_contents = []
        self.token_frequency = {}
        self.process_id_vs_name = {}
        self.jstack_time_stamps = []
        self.state_frequency_dicts = [] 
        self.files_deployed_to_azure = []
        self.top_cpu_consuming_threads = []
        self.system_compatible_with_top = True 

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
        nid_regex = r"nid\=(0x[0-9a-fA-F]+)"
        cpu_regex = r"cpu\s*=\s*(\d+.\d+)ms"
        thread_state_regex = r"java\.lang\.Thread\.State\:\s*([^\s]*)"
        thread_name_regex = r"^\s*(.*)\s+\#\d+\s+daemon\s+prio\=5\s+os_prio\=0"

        nid = re.search(nid_regex, text)
        cpu = re.search(cpu_regex, text)
        thread_name = re.search(thread_name_regex, text)
        thread_state = re.search(thread_state_regex, text)

        self.tags = []
        self.text = text
        self.process_id = process_id
        self.nid = nid.group(1) if nid is not None else -1
        self.cpu = float(cpu.group(1)) if cpu is not None else -1
        self.thread_name = thread_name.group(1) if thread_name is not None else "unknown_thread"
        self.thread_state = thread_state.group(1) if thread_state is not None else "unknown_state"
