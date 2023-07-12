from legacy_configuration import Config

class Context:
    threads = {}
    pod_cpu_time = 0
    file_contents = []
    token_frequency = {}
    process_id_vs_name = {}
    jstack_time_stamps = []
    state_frequency_dicts = [] 
    files_uploaded_to_azure = []
    top_cpu_consuming_threads = []
    system_calls_total_cpu_time = 0

    @staticmethod
    def init_database():
        tokens = Config.tokens
        if tokens is not None:
            for token in tokens:
                Context.token_frequency[token["text"]] = 0

    @staticmethod
    def found_token(token):
        Context.token_frequency[token["text"]] += 1

    @staticmethod
    def add_process(process_id, process_name):
        Context.process_id_vs_name[process_id] = process_name
