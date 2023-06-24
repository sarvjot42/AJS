from core import Core
from utils import Utils
from connectors import Connectors
from schema import Config, Database

def init():
    config = Config()
    db = Database(config)

    jstack_file_path = config.jstack_file_path
    num_jstacks = 0

    if jstack_file_path is not None:
        num_jstacks = Core.handle_jstack_file_input(config, db)
    else:
        num_jstacks = config.num_jstacks
        Core.handle_jstack_generation(config, db)

    for jstack_index in range(num_jstacks):
        Core.analyse_jstacks(config, db, jstack_index)

    Core.compare_jstacks(config, db, num_jstacks)

if __name__ == "__main__":
    Utils.setup_interrupt()
    Connectors.reset_output_files()
    init()
