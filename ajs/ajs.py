from ajs_data import Config 
from ajs_data import Database 
from ajs_evaluator import AJSEvaluator
from ajs_interface import AJSInterface

def init():
    ajs_config = Config()
    ajs_db = Database(ajs_config)

    jstack_file_path = ajs_config.jstack_input_file_path
    num_jstacks = 0

    if jstack_file_path is not None:
        num_jstacks = AJSInterface.handle_jstack_file_input(ajs_config, ajs_db)
    else:
        num_jstacks = ajs_config.num_jstacks
        AJSInterface.handle_jstack_generation(ajs_config, ajs_db)

    for jstack_index in range(num_jstacks):
        AJSEvaluator.process_jstack(ajs_config, ajs_db, jstack_index)

    AJSEvaluator.output_jstack_comparison_header(ajs_config)
    AJSInterface.output_thread_state_frequency(ajs_config, ajs_db)
    AJSEvaluator.process_cpu_consuming_threads(ajs_config, ajs_db)
    AJSInterface.output_jstacks_in_one_file(ajs_config, ajs_db, num_jstacks)
    AJSInterface.upload_output_files(ajs_config)

if __name__ == "__main__":
    AJSInterface.setup_interrupt()
    AJSInterface.reset_output_files()
    init()
