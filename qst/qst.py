from qst_data import QSTData
from qst_utils import QSTUtils
from qst_evaluator import QSTEvaluator
from qst_interface import QSTInterface

def init(tokens, print_all_matches, jstack_file_input, delay_bw_jstacks, num_jstacks):
    qst_data = QSTData(tokens)

    if jstack_file_input is True:
        num_jstacks = QSTInterface.handle_jstack_file_input(qst_data)
    else:
        QSTInterface.handle_jstack_generation(qst_data, delay_bw_jstacks, num_jstacks)

    for jstack_index in range(num_jstacks):
        QSTEvaluator.process_jstack(qst_data, tokens, print_all_matches, jstack_index)

    QSTInterface.output_cpu_consuming_threads(qst_data)

if __name__ == "__main__":
    QSTInterface.setup_interrupt()
    QSTInterface.reset_output_directory()

    parser = QSTUtils.setup_parser()
    args = parser.parse_args()

    init(args.tokens, args.print_all_matches, args.jstack_file_input, args.delay_bw_jstacks, args.num_jstacks)
