import subprocess
import time
import argparse
import signal

def handle_interrupt(signal, frame):
    print('\nReceived SIGINT, exiting')
    exit(0)

signal.signal(signal.SIGINT, handle_interrupt) # allow exiting with Ctrl+C

def get_active_java_processes():
    result = subprocess.run(['jps'], capture_output=True, text=True)
    process_lines = result.stdout.strip().split('\n') # remove spaces from end, and split by new lines
    processes = [line.split(' ', 1) for line in process_lines] # split each line by whitespace ' ', at max once
    return processes

def get_stack_trace(process_id):
    result = subprocess.run(['jstack', process_id], capture_output=True, text=True)
    stack_trace = result.stdout.strip()
    stack_frames = stack_trace.split('\n\n') # stack frames are separated by empty lines 
    return stack_frames

class ResponseData:
    def __init__(self):
        self.processes = {}
        self.stack_frames = []
        self.stack_frames_for_token = {}
    
    def add_process(self, process_id, process_name):
        self.processes[process_id] = process_name
    
    def add_stack_frame(self, stack_frame, process_id):
        self.stack_frames.append({ 'frame': stack_frame, 'process_id': process_id })

    def add_stack_frame_for_token(self, token, stack_frame_index):
        if self.stack_frames_for_token.get(token) is None:
            self.stack_frames_for_token[token] = []
        self.stack_frames_for_token[token].append(stack_frame_index)

    def get_stack_frames(self):
        return self.stack_frames

    def print_data(self, allow_multiple):
        for token in self.stack_frames_for_token:
            print(f"\nTOKEN {token} FOUND IN {len(self.stack_frames_for_token[token])} STACK FRAMES")

            if not allow_multiple:
                self.stack_frames_for_token[token] = self.stack_frames_for_token[token][:1]
            for index in self.stack_frames_for_token[token]:
                stack_frame = self.stack_frames[index]
                process_id = stack_frame['process_id']
                process_name = self.processes[process_id]

                print(f"\nProcess Name: {process_name}, Process Id: {process_id}")
                print(stack_frame['frame'])

def generate_response_data(tokens, response_data):
    active_processes = get_active_java_processes()
    active_processes = [p for p in active_processes if len(p) == 2] # keep process only if it has both id and name

    for process_id, process_name in active_processes:
        response_data.add_process(process_id, process_name)
        stack_trace = get_stack_trace(process_id)

        for stack_frame in stack_trace:
            response_data.add_stack_frame(stack_frame, process_id)

    for stack_frame_index, stack_frame in enumerate(response_data.get_stack_frames()):
        for token in tokens:
            if token in stack_frame['frame']:
                response_data.add_stack_frame_for_token(token, stack_frame_index)
            
def main(tokens, allow_multiple, periodicity=1000, number_of_cycles=10):
    response_data = ResponseData()

    for _ in range(number_of_cycles):
        generate_response_data(tokens, response_data)
        time.sleep(periodicity / 1000)

    response_data.print_data(allow_multiple)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search for tokens in stack traces of all running Java processes')
    parser.add_argument('tokens', nargs='+', help='Enter tokens to search in stack traces')
    parser.add_argument('-p', '--periodicity', metavar='', type=int, default=100, help='Delay between two consecutive JStacks in milliseconds')
    parser.add_argument('-n', '--num_jstacks', metavar='', type=int, default=10, help='Number of JStacks to be processed')
    parser.add_argument('-a', '--allow_multiple', action='store_true', help='Allow multiple straces for same token')

    args = parser.parse_args()

    main(args.tokens, args.allow_multiple, args.periodicity, args.num_jstacks)
