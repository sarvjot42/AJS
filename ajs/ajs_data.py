import re
from ajs_utils import AJSUtils

class Config:
    def __init__(self):
        cli = AJSUtils.setup_cli()
        args = cli.parse_args()

        self.session_id = AJSUtils.generate_session_id()
        self.thread_states = [
            { "regex": ".*RUNNABLE.*", "tag": "RUNNABLE" }, 
            { "regex": ".*TIMED_WAITING.*", "tag": "TIMED_WAITING" },
            { "regex": ".*WAITING.*", "tag": "WAITING" },
            { "regex": ".*BLOCKED.*", "tag": "BLOCKED" }
        ]

        AJSUtils.setup_config(self, args)

class Database:
    def __init__(self, ajs_config):
        self.threads = {}
        self.token_frequency = {}
        self.process_id_vs_name = {}
        self.state_frequency_dicts = [] 

        tokens = ajs_config.tokens
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

        self.id = float(id.group(1)) if id is not None else -1
        self.cpu = float(cpu.group(1)) if cpu is not None else -1
        self.elapsed = float(elapsed.group(1)) if elapsed is not None else -1
        self.thread_state = thread_state.group(1) if thread_state is not None else "unknown_state"
        self.thread_name = thread_name.group(1) if thread_name is not None else "unknown_thread"
        self.tags = []
        self.text = text
        self.process_id = process_id
