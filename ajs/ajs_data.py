from ajs_utils import AJSUtils

class AJSData:
    def __init__(self):
        config = AJSUtils.load_and_parse_config()

        self.config = config
        self.token_frequency = {}
        self.process_id_vs_name = {}
        self.cpu_consuming_threads = []
        self.session_id = AJSUtils.generate_session_id()
        self.CPU_CONSUMING_THREADS_PER_JSTACK = 10

        for token in config["tokens"]:
            self.token_frequency[token["text"]] = 0

    def add_process(self, process_id, process_name):
        self.process_id_vs_name[process_id] = process_name

    def found_token(self, token):
        self.token_frequency[token["text"]] += 1

class StackFrame:
    def __init__(self, text, process_id):
        self.text = text
        self.process_id = process_id
        self.tags = []
        self.cpu_time = None
