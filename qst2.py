import time
import signal
import argparse
import subprocess


def handle_interrupt(signal, frame):
    print("\nReceived SIGINT, exiting")
    exit(0)

# allow exiting the script with Ctrl + C 
# register the signal handler
signal.signal(signal.SIGINT, handle_interrupt)


# Schema class for StackFrame
class StackFrameWithProcessID:
    def __init__(self, frame_text, process_id):
        self.frame_text = frame_text
        self.process_id = process_id


# Data is stored here
class QSTData:
    def __init__(self):
        self.processes = {}
        self.stack_frames_by_token = {}

    # processes is a dictionary of form {process_id: process_name}
    def add_process(self, process_id, process_name):
        self.processes[process_id] = process_name

    # stack frames_by_token is a dictionary of form {token: [ StackFramesWithProcessID ]}
    def add_stack_frame_by_token(self, token, stack_frame):
        if self.stack_frames_by_token.get(token) is None:
            self.stack_frames_by_token[token] = []
        self.stack_frames_by_token[token].append(stack_frame)


# Business logic for qst is stored here
class QSTEvaluator:
    # Get all active java processes and store them in qst_data.processes
    # Use "ps -e" to get all active processes
    @staticmethod
    def get_active_java_processes(qst_data):
        result = subprocess.Popen(["ps", "-e"], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        lines = output.strip().split("\n")

        active_processes = []
        for line in lines:
            if "java" in line:
                cols = line.split()
                process_id = cols[0]
                process_name = ""
                for i in range(3, len(cols)):
                    process_name = process_name + cols[i] + " "
                active_processes.append([process_id, process_name])

        for process_id, process_name in active_processes:
            qst_data.add_process(process_id, process_name)

    # Get stack trace for a process using jstack, using process_id
    @staticmethod
    def get_stack_trace(process_id):
        result = subprocess.Popen(["jstack", str(process_id)], stdout=subprocess.PIPE)
        output, _ = result.communicate()
        stack_trace = output.strip()
        stack_frames = stack_trace.split("\n\n")
        return stack_frames

    # Query stack frames for a token
    @staticmethod
    def query_stack_trace(tokens, print_all, qst_data):
        for process_id in qst_data.processes:
            stack_trace = QSTEvaluator.get_stack_trace(process_id)

            for frame_text in stack_trace:
                stack_frame_with_process_id = StackFrameWithProcessID(frame_text, process_id)
                for token in tokens:
                    if print_all is False and qst_data.stack_frames_by_token.get(token) is not None:
                        break
                    if token in frame_text:
                        qst_data.add_stack_frame_by_token(token, stack_frame_with_process_id)

    # Print stack frames for a token
    @staticmethod
    def print_data(tokens, qst_data):
        for token in tokens:
            print(
                "\nTOKEN {} FOUND IN {} STACK FRAMES".format(
                    token, len(qst_data.stack_frames_by_token[token])
                )
            )

            for stack_frame_with_process_id in qst_data.stack_frames_by_token[token]:
                frame_text = stack_frame_with_process_id.frame_text
                process_id = stack_frame_with_process_id.process_id
                process_name = qst_data.processes[process_id]

                print("\nProcess Name: {}, Process Id: {}".format(process_name, process_id))
                print(frame_text)


def main(tokens, print_all, delay=1000, number_of_cycles=10):
    qst_data = QSTData()

    # store java processes in qst_data
    # stack traces of these processes will be used in all the cycles 
    QSTEvaluator.get_active_java_processes(qst_data)

    # in every cycle, generate stack frames using jstack and wait for some time
    for _ in range(number_of_cycles):
        QSTEvaluator.query_stack_trace(tokens, print_all, qst_data)
        time.sleep(delay / 1000)

    # now you have stack frames for all the processes for all cycles
    # query/search these for tokens
    QSTEvaluator.print_data(tokens, qst_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search for tokens in stack traces of all running Java processes"
    )

    # tokens is a positional argument which accepts one or more values
    parser.add_argument(
        "tokens", nargs="+", help="Enter tokens to search in stack traces"
    )
    # print_all is a boolean argument, which assumes value True if passed, else False
    parser.add_argument(
        "-a",
        "--print_all",
        action="store_true",
        help="Print [a]ll stack frames for tokens",
    )
    # delay is an optional argument with default value of 100 milliseconds
    parser.add_argument(
        "-d",
        "--delay",
        metavar="",
        type=int,
        default=100,
        help="[D]elay between two consecutive JStacks in milliseconds",
    )
    # num_jstacks is an optional argument with default value of 10 cycles
    parser.add_argument(
        "-n",
        "--num_jstacks",
        metavar="",
        type=int,
        default=10,
        help="[N]umber of JStacks to be processed",
    )

    args = parser.parse_args()
    main(args.tokens, args.print_all, args.delay, args.num_jstacks)
