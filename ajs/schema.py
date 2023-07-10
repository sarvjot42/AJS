import re 

class Thread:
    def __init__(self, text, process_id):
        nid_regex = r"nid\=(0x[0-9a-fA-F]+)"
        cpu_regex = r"cpu\s*=\s*(\d+.\d+)ms"
        elapsed_regex = r"elapsed\s*=\s*(\d+.\d+)ms"
        thread_state_regex = r"java\.lang\.Thread\.State\:\s*([^\s]*)"
        thread_name_regex = r"^\s*(.*)\s+\#\d+\s+daemon\s+prio\=5\s+os_prio\=0"

        nid = re.search(nid_regex, text)
        cpu = re.search(cpu_regex, text)
        elapsed = re.search(elapsed_regex, text)
        thread_name = re.search(thread_name_regex, text)
        thread_state = re.search(thread_state_regex, text)

        self.tags = []
        self.text = text
        self.process_id = process_id
        self.nid = nid.group(1) if nid is not None else -1
        self.cpu = float(cpu.group(1)) if cpu is not None else -1
        self.elapsed = float(elapsed.group(1)) if elapsed is not None else -1
        self.thread_name = thread_name.group(1) if thread_name is not None else "unknown_thread"
        self.thread_state = thread_state.group(1) if thread_state is not None else "unknown_state"
