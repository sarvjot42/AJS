from ajs_data import Config 
from ajs_data import Database 
from ajs_evaluator import AJSEvaluator
from ajs_interface import AJSInterface

def init():
    ajs_config = Config()
    ajs_db = Database(ajs_config)

    jstack_file_path = ajs_config.config["jstack_input_file_path"]
    num_jstacks = 0

    if jstack_file_path is not None:
        num_jstacks = AJSInterface.handle_jstack_file_input(ajs_config, ajs_db)
    else:
        num_jstacks = ajs_config.config["num_jstacks"]
        AJSInterface.handle_jstack_generation(ajs_config, ajs_db)

    AJSInterface.reset_output_directory()

    for jstack_index in range(num_jstacks):
        AJSEvaluator.process_jstack(ajs_config, ajs_db, jstack_index)

    for thread_id in ajs_db.threads:
        thread_instances = ajs_db.threads[thread_id]
        print(int(thread_id), len(thread_instances))

    # AJSEvaluator.compare_jstacks(ajs_config, ajs_db)
    # AJSInterface.output_cpu_consuming_threads(ajs_db)

if __name__ == "__main__":
    AJSInterface.setup_interrupt()
    init()
