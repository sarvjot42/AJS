from qst_utils import QSTUtils

class QSTData:
    def __init__(self, tokens):
        self.token_frequency = {}
        self.process_id_vs_name = {}
        self.cpu_consuming_threads = []
        self.config = QSTUtils.load_and_parse_config()
        self.session_id = QSTUtils.generate_session_id()
        self.CPU_CONSUMING_THREADS_PER_JSTACK = 10

        for token in tokens:
            self.token_frequency[token] = 0

    def add_process(self, process_id, process_name):
        self.process_id_vs_name[process_id] = process_name

    def found_token(self, token):
        self.token_frequency[token] += 1

class StackFrame:
    def __init__(self, text, process_id):
        self.text = text
        self.process_id = process_id
        self.tags = []
        self.cpu_time = None
