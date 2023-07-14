import os
import json
import argparse
import datetime

class Config:
    session_id = ""
    jstack_folder_path = ".ajs/jstacks/"
    analysis_file_path = ".ajs/analysis.txt"
    jstacks_file_path = ".ajs/jstacks.txt"

    do_benchmark = False
    file_input = False
    top_file_path = None
    jstack_file_path = None
    namespace = None
    pod_name = None
    container_name = None
    num_jstacks = 3
    delay_bw_jstacks = 10000
    include_only = False
    filter_out = False
    tokens = None
    thread_classes = False
    classification_print_trace = False
    cpu_threshold_percentage = 0
    thread_state_frequency = False
    cpu_consuming_threads_jstack = False
    cpu_consuming_threads_top = False
    repetitive_stack_trace = False

    @staticmethod
    def init_config():
        Config.setup_cli()

    @staticmethod
    def setup_cli():
        formatter = lambda prog: argparse.HelpFormatter(prog,max_help_position=52)
        cli = argparse.ArgumentParser(description="Analyse JStacks, a tool to analyze java thread dumps. Configure settings in 'config.json', Sample config file is given in '.ajs/config.sample.json'", formatter_class=formatter)

        cli.add_argument("-b", "--benchmark", default=False, action="store_true", help="Run in benchmark mode")
        cli.add_argument("-d", "--namespace", metavar="", type=str, help="Kubernetes namespace")
        cli.add_argument("-e", "--pod_name", metavar="", type=str, help="Kubernetes pod name")
        cli.add_argument("-f", "--container_name", metavar="",type=str, help="Kubernetes container container name")
        cli.add_argument("-i", "--num_jstacks", default=3, metavar="", type=int, help="Number of jstacks to collect")
        cli.add_argument("-j", "--delay_bw_jstacks", default=10000, metavar="", type=int, help="Delay in delay between jstacks")
        cli.add_argument("-k", "--include_only", nargs='+', metavar="", type=str, help="Only include these threads")
        cli.add_argument("-l", "--filter_out", nargs='+', metavar="", type=str, help="Filter out these threads")
        cli.add_argument("-m", "--tokens", nargs='+', metavar="", type=str, help="Search for these tokens in the jstack")

        cli.add_argument("-A", "--full-analysis", action="store_true", help="Perform [A]ll analysis, equivalent to -IOSCRJTF")
        cli.add_argument("-C", "--classify-threads", action="store_true", help="[C]lassify threads based on configured regexes")
        cli.add_argument("-R", "--repetitive-stack-trace", action="store_true", help="Detect [R]epetitive stack traces in threads")
        cli.add_argument("-J", "--cpu-consuming-threads-jstack", action="store_true", help="Output most CPU Intensive threads, calculated using [J]stacks [supported in jdk11+]")
        cli.add_argument("-T", "--cpu-consuming-threads-top", action="store_true", help="Output most CPU Intensive threads, calculated using [T]op utility")

        args = cli.parse_args()

        if (args.full_analysis is True):
            args.classify_threads = True
            args.repetitive_stack_trace = True
            args.cpu_consuming_threads_jstack = True
            args.cpu_consuming_threads_top = True

        Config.session_id = Config.generate_session_id("session_")
        Config.do_benchmark = args.benchmark

        if args.namespace is not None:
            Config.namespace = args.namespace
        else:
            Config.namespace = "default"

        if args.pod_name is None or args.container_name is None:
            print("Pod and container name is required")
            exit(1)
        else:
            Config.pod_name = args.pod_name
            Config.container_name = args.container_name

        Config.num_jstacks = args.num_jstacks
        Config.delay_bw_jstacks = args.delay_bw_jstacks

        Config.include_only = args.include_only
        Config.filter_out = args.filter_out

        if args.tokens is not None:
            tokens = []
            for token in args.tokens:
               tokens.append({"text": token, "output_all_matches": True}) 
            Config.tokens = tokens
        else:
            Config.tokens = None

        with open(os.path.join(os.path.dirname(__file__), ".ajs/config.json")) as file:
            config_file = json.load(file)

            thread_classes = []

            for thread_class in config_file["classification"]:
                tag = str(thread_class["tag"])
                regex = str(thread_class["regex"])
                thread_classes.append({"tag": tag, "regex": regex})

            Config.thread_classes = thread_classes

        Config.classification_print_trace = args.classification_print_trace

        Config.cpu_threshold_percentage = config_file["cpu_threshold_percentage"]
        Config.thread_state_frequency = True
        Config.cpu_consuming_threads_jstack = args.cpu_consuming_threads_jstack
        Config.cpu_consuming_threads_top = args.cpu_consuming_threads_top
        Config.repetitive_stack_trace = args.repetitive_stack_trace

    @staticmethod
    def generate_session_id(session_name):
        time_stamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        session_id = session_name + "_" + time_stamp
        return session_id
