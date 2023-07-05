from utils import Utils
from core import Core
from connectors import Connectors
from schema import Config, Database

@Utils.benchmark_time("entire script execution")
def main():
    config = Config()
    db = Database(config)

    Utils.setup_interrupt()
    Connectors.reset_output_files(config)

    num_jstacks = 0

    if config.file_input is True:
        num_jstacks = Core.handle_jstack_file_input(config, db)
        Core.handle_top_file_input(config, db)
    else:
        num_jstacks = config.num_jstacks
        Core.handle_jstack_generation(config, db)
        Core.handle_top_generation(config, db)

    for jstack_index in range(num_jstacks):
        Core.analyse_jstacks(config, db, jstack_index)

    Core.compare_jstacks(config, db, num_jstacks)
    Connectors.upload_output_files(config, db)

    return db.files_deployed_to_azure

if __name__ == "__main__":
    output = main()

    Utils.benchmark_cpu()
    Utils.benchmark_memory()

    print("\nOutput files deployed to Azure:")
    for file in output:
        print(file)
