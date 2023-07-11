import json
import argparse
import datetime

class Config:
    session_id = "" 
    jstack_folder_path = ".ajs/jstacks/"
    analysis_file_path = ".ajs/analysis.txt"
    jstacks_file_path = ".ajs/jstacks.txt"

    @staticmethod 
    def init_config():
        args = Config.setup_cli()
        Config.session_id = Config.generate_session_id(args.session_name)
        Config.setup_config(args)

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
        cli.add_argument("-F", "--thread-state-frequency", action="store_true", help="Analyse thread state [F]requencies for all jstacks")

        args = cli.parse_args()

        if (args.full_analysis is True):
            args.include_only = True
            args.filter_out = True
            args.search_tokens = True
            args.classify_threads = True
            args.repetitive_stack_trace = True
            args.cpu_consuming_threads_jstack = True
            args.cpu_consuming_threads_top = True
            args.thread_state_frequency = True

        return args

    @staticmethod
    def generate_session_id(session_name):
        time_stamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        session_id = session_name + "_" + time_stamp
        return session_id

    @staticmethod
    def setup_config(args):
        with open("config.json") as file:
            config_file = json.load(file)

        try:
            Config.setup_filter_config(args, config_file)
            Config.setup_token_config(args, config_file)
            Config.setup_classification_config(args, config_file)
            Config.setup_input_config(args, config_file)

            Config.thread_cpu_threshold_percentage = config_file["thread_cpu_threshold_percentage"] if "thread_cpu_threshold_percentage" in config_file else 0.0

            Config.thread_state_frequency = args.thread_state_frequency
            Config.cpu_consuming_threads_jstack = args.cpu_consuming_threads_jstack
            Config.cpu_consuming_threads_top = args.cpu_consuming_threads_top
            Config.repetitive_stack_trace = args.repetitive_stack_trace

            Config.do_benchmark = args.benchmark

        except KeyError as e:
            exit("\nKey " + str(e) + " not found in config file, please refer to the sample config file")

    @staticmethod
    def setup_filter_config(args, config_file):
        if args.include_only is True:
            wanted_tokens = []
            for wanted_token in config_file["include_only"]:
                wanted_tokens.append(str(wanted_token["regex"]))
            Config.include_only = wanted_tokens
        else:
            Config.include_only = None

        if args.filter_out is True:
            unwanted_tokens = []
            for unwanted_token in config_file["filter_out"]:
                unwanted_tokens.append(str(unwanted_token["regex"]))
            Config.filter_out = unwanted_tokens
        else:
            Config.filter_out = None

    @staticmethod
    def setup_token_config(args, config_file):
        if args.search_tokens is True:
            tokens = []
            for token in config_file["search_tokens"]:
                token_text = str(token["text"])
                output_all_matches = token["output_all_matches"]
                tokens.append({"text": token_text, "output_all_matches": output_all_matches})
            Config.tokens = tokens
        else:
            Config.tokens = None

    @staticmethod
    def setup_classification_config(args, config_file):
        if args.classify_threads is True:
            classification_groups = []

            for group in config_file["classification_groups"]:
                group_items = []
                for item in group:
                    tag = str(item["tag"])
                    regex = str(item["regex"])
                    group_items.append({"tag": tag, "regex": regex})
                classification_groups.append(group_items)

            Config.classification_groups = classification_groups
        else:
            Config.classification_groups = None

    @staticmethod
    def setup_input_config(args, config_file):
        Config.file_input = args.file_input

        if args.file_input is True:
            Config.top_file_path = str(config_file["top_file_path"])
            Config.jstack_file_path = str(config_file["jstack_file_path"])

            Config.namespace = None
            Config.pod_name = None
            Config.container_name = None
            Config.num_jstacks = None 
            Config.delay_bw_jstacks = None
        else:
            Config.top_file_path = None
            Config.jstack_file_path = None

            Config.namespace = str(config_file["namespace"])
            Config.pod_name = str(config_file["pod_name"])
            Config.container_name = str(config_file["container_name"])
            Config.num_jstacks = int(config_file["num_jstacks"]) if "num_jstacks" in config_file else 3
            Config.delay_bw_jstacks = int(config_file["delay_bw_jstacks"]) if "delay_bw_jstacks" in config_file else 10000

class Database:
    threads = {}
    pod_cpu_time = 0
    file_contents = []
    token_frequency = {}
    unchanged_threads = {}
    process_id_vs_name = {}
    jstack_time_stamps = []
    state_frequency_dicts = [] 
    files_deployed_to_azure = []
    top_cpu_consuming_threads = []
    system_calls_total_cpu_time = 0
    system_compatible_with_top = True 

    @staticmethod
    def init_database():
        tokens = Config.tokens
        if tokens is not None:
            for token in tokens:
                Database.token_frequency[token["text"]] = 0

    @staticmethod
    def found_token(token):
        Database.token_frequency[token["text"]] += 1

    @staticmethod
    def add_process(process_id, process_name):
        Database.process_id_vs_name[process_id] = process_name
