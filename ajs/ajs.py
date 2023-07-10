import threading
from utils import Utils
from core import Core
from connectors import Connectors
from data import Config, Database

@Utils.benchmark_time("entire script execution")
def main():
    Config.init_config()
    Database.init_database()
    Utils.setup_interrupt()
    Connectors.clear_existing_files()

    print("Starting script execution...")

    num_jstacks = 0

    if Config.file_input is True:
        num_jstacks = Core.handle_jstack_file_input()
        Core.handle_top_file_input()
    else:
        num_jstacks = Config.num_jstacks

        thread1 = threading.Thread(target=Core.handle_jstack_generation)
        thread2 = threading.Thread(target=Core.handle_top_generation)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

    for jstack_index in range(num_jstacks):
        Core.analyse_jstacks(jstack_index)

    Core.compare_jstacks()
    Connectors.output_jstacks_in_one_file(num_jstacks)
    Connectors.prepend_contents()
    # Connectors.upload_output_files()
    Connectors.clear_auxilliary_folder()

    return Database.files_deployed_to_azure

if __name__ == "__main__":
    azure_files = main()

    Utils.benchmark_cpu()
    Utils.benchmark_memory()
    Utils.benchmark_pod_cpu()

    if len(azure_files) > 0:
        print("\nOutput files deployed to Azure:")
    for file in azure_files:
        print(file)
