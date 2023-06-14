import time
from qst_data import QSTData
from qst_utils import QSTUtils
from qst_evaluator import QSTEvaluator
from qst_interface import QSTInterface

def main(tokens, print_all, delay=1000, number_of_cycles=10):
    qst_data = QSTData()

    # store java processes in qst_data
    # stack traces of these processes will be used in all the cycles 
    QSTInterface.get_active_java_processes(qst_data)

    QSTInterface.reset_files()

    # in every cycle, generate stack frames using jstack and wait for some time
    for it in range(number_of_cycles):
        QSTInterface.store_jstacks(it, qst_data)
        time.sleep(delay / 1000)

    for token in tokens:
        qst_data.found_tokens[token] = 0

    for it in range(number_of_cycles):
        QSTEvaluator.process_cycle(it, tokens, print_all, qst_data)

    QSTInterface.store_cpu_consuming_all(qst_data)

if __name__ == "__main__":
    QSTInterface.setup_interrupt()

    parser = QSTUtils.setup_parser()
    args = parser.parse_args()
    main(args.tokens, args.print_all, args.delay, args.num_jstacks)
