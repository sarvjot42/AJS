import threading
from utils import Utils
from core import Core
from connectors import Connectors
from schema import Config, Database

@Utils.benchmark_time("entire script execution")
def main():
    config = Config()
    db = Database(config)

    Utils.setup_interrupt()
    Connectors.clear_existing_files(config)

    num_jstacks = 0

    if config.file_input is True:
        num_jstacks = Core.handle_jstack_file_input(config, db)
        Core.handle_top_file_input(config, db)
    else:
        num_jstacks = config.num_jstacks

        thread1 = threading.Thread(target=Core.handle_jstack_generation, args=(config, db))
        thread2 = threading.Thread(target=Core.handle_top_generation, args=(config, db))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

    for jstack_index in range(num_jstacks):
        Core.analyse_jstacks(config, db, jstack_index)

    Core.compare_jstacks(config, db, num_jstacks)
    Connectors.prepend_contents(db)
    # Connectors.upload_output_files(config, db)
    Connectors.clear_auxilliary_folder(config)

    return db.files_deployed_to_azure

if __name__ == "__main__":
    print("Starting script execution...")

    azure_files = main()

    Utils.benchmark_cpu()
    Utils.benchmark_memory()

    if len(azure_files) > 0:
        print("\nOutput files deployed to Azure:")
    for file in azure_files:
        print(file)
