from ajs_data import AJSData
from ajs_utils import AJSUtils
from ajs_evaluator import AJSEvaluator
from ajs_interface import AJSInterface

def init(delay_bw_jstacks, num_jstacks):
    ajs_data = AJSData()
    jstack_file_path = ajs_data.config["jstack_input_file_path"]

    if jstack_file_path is not None:
        num_jstacks = AJSInterface.handle_jstack_file_input(ajs_data)
    else:
        AJSInterface.handle_jstack_generation(ajs_data, delay_bw_jstacks, num_jstacks)

    for jstack_index in range(num_jstacks):
        AJSEvaluator.process_jstack(ajs_data, jstack_index)

    AJSInterface.output_cpu_consuming_threads(ajs_data)

if __name__ == "__main__":
    AJSInterface.setup_interrupt()
    AJSInterface.reset_output_directory()

    parser = AJSUtils.setup_parser()
    args = parser.parse_args()

    init(args.delay_bw_jstacks, args.num_jstacks)
