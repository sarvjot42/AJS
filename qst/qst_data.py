from qst_utils import QSTUtils

# Data is stored here
class QSTData:
    def __init__(self):
        self.process_id_vs_name = {}
        self.found_tokens = set()
        self.config = QSTUtils.load_and_parse_config()

    # processes is a dictionary of form {process_id: process_name}
    def add_process(self, process_id, process_name):
        self.process_id_vs_name[process_id] = process_name

    def found_token(self, token):
        self.found_tokens.add(token)
