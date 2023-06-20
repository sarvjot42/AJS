import re
from ajs_utils import AJSUtils

class Config:
    def __init__(self):
        self.session_id = AJSUtils.generate_session_id()

        parser = AJSUtils.setup_parser()
        args = parser.parse_args()

        self.config = AJSUtils.load_config(args)

class Database:
    def __init__(self, ajs_config):
        self.token_frequency = {}
        self.process_id_vs_name = {}
        self.threads = {}

        tokens = ajs_config.config["tokens"]
        if tokens is not None:
            for token in tokens:
                self.token_frequency[token["text"]] = 0

    def add_process(self, process_id, process_name):
        self.process_id_vs_name[process_id] = process_name

    def found_token(self, token):
        self.token_frequency[token["text"]] += 1

class Thread:
    def __init__(self, text, process_id):
        id_regex = r"\#(\d+)"
        cpu_regex = r"cpu\s*=\s*(\d+.\d+)ms"
        elapsed_regex = r"elapsed\s*=\s*(\d+\.\d+)s"
        thread_state_regex = r"java\.lang\.Thread\.State\:\s*(.*)"
        thread_name_regex = r"^\s*(.*)\s+\#\d+\s+daemon\s+prio\=5\s+os_prio\=0"

        id = re.search(id_regex, text)
        cpu = re.search(cpu_regex, text)
        elapsed = re.search(elapsed_regex, text)
        thread_state = re.search(thread_state_regex, text)
        thread_name = re.search(thread_name_regex, text)

        self.id = float(id.group(1)) if id is not None else 0
        self.cpu = float(cpu.group(1)) if cpu is not None else 0
        self.elapsed = float(elapsed.group(1)) if elapsed is not None else 0
        self.thread_state = thread_state.group(1) if thread_state is not None else "unknown_state"
        self.thread_name = thread_name.group(1) if thread_name is not None else "unknown_thread"
        self.text = text
        self.process_id = process_id
        self.tags = []
