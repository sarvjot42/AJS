from qst_utils import QSTUtils

# Data is stored here
class QSTData:
    def __init__(self):
        self.found_tokens = {}
        self.process_id_vs_name = {}
        self.cpu_consuming_stack_frames = []
        self.config = QSTUtils.load_and_parse_config()

    # processes is a dictionary of form {process_id: process_name}
    def add_process(self, process_id, process_name):
        self.process_id_vs_name[process_id] = process_name

    def found_token(self, token):
        self.found_tokens[token] += 1

# Schema class for StackFrame
class StackFrame:
    def __init__(self, text, process_id):
        self.text = text
        self.process_id = process_id
        self.tags = []
        self.cpu_time = None
