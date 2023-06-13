import time
from qst_data import QSTData
from qst_utils import QSTUtils
from qst_evaluator import QSTEvaluator
from qst_interface import QSTInterface

@QSTUtils.benchmark
def main(tokens, print_all, delay=1000, number_of_cycles=10, **kwargs):
    log_stats = kwargs["log_stats"]

    qst_data = QSTData()

    # store java processes in qst_data
    # stack traces of these processes will be used in all the cycles 
    QSTInterface.get_active_java_processes(qst_data, log_stats=log_stats, label='\nFETCHING JAVA PROCESSES')

    QSTInterface.reset_files()

    # in every cycle, generate stack frames using jstack and wait for some time
    QSTUtils.logger(log_stats, 1, 2, 1)
    QSTUtils.logger(log_stats, "FETCHING AND STORING JSTACKS (Sleeping for {} seconds in between):\n".format(delay/1000))
    store_jstacks_cycles(qst_data, delay, number_of_cycles, log_stats=log_stats, label='FETCHING AND STORING JSTACKS IN TOTAL')

    for token in tokens:
        qst_data.found_tokens[token] = 0

    QSTUtils.logger(log_stats, 1, 2, 1)
    QSTUtils.logger(log_stats, "PROCESSING CYCLES\n")
    process_cycles(qst_data, tokens, print_all, number_of_cycles, log_stats=log_stats, label='PROCESSING CYCLES')
    QSTUtils.logger(log_stats, 1, 0, 0)

    QSTUtils.logger(log_stats, 0, 2, 1)
    QSTInterface.store_cpu_consuming_all(qst_data, log_stats=log_stats, label='STORING CPU CONSUMING THREADS')

    QSTUtils.logger(log_stats, 1, 2, 1)
    for token in tokens:
        QSTUtils.logger(log_stats, "TOKEN {} WAS MATCHED IN {} STACK FRAMES".format(token, qst_data.found_tokens[token]))

    QSTUtils.logger(log_stats, 1, 2, 1)

@QSTUtils.benchmark
def store_jstacks_cycles(qst_data, delay, number_of_cycles, **kwargs):
    log_stats = kwargs["log_stats"]

    for it in range(number_of_cycles):
        QSTInterface.store_jstacks(it, qst_data, log_stats=log_stats, label='CYCLE {}'.format(QSTUtils.convert_number_to_alphabet(it)))
        time.sleep(delay / 1000)

    QSTUtils.logger(log_stats, 1, 0, 0)

@QSTUtils.benchmark
def process_cycles(qst_data, tokens, print_all, number_of_cycles, **kwargs):
    log_stats = kwargs["log_stats"]
    for it in range(number_of_cycles):
        QSTEvaluator.process_cycle(it, tokens, print_all, qst_data, log_stats=log_stats, label='\nCYCLE {}'.format(QSTUtils.convert_number_to_alphabet(it)))
        QSTUtils.logger(log_stats, 1, 1, 1)

if __name__ == "__main__":
    QSTInterface.setup_interrupt()

    parser = QSTUtils.setup_parser()
    args = parser.parse_args()
    main(args.tokens, args.print_all, args.delay, args.num_jstacks, log_stats=args.log_stats, label="SCRIPT")
