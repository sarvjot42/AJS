import threading
import time
import subprocess
import argparse
import json
import operator
import multiprocessing


current_milli_time = lambda: int(round(time.time() * 1000))
get_java_threads_output = []
java_process_jstacks = {}
list_of_pids_string = ""
jstack_errors = []


def get_thread_jstack(jstack, nid):
    kernel_nid = "nid=" + hex(nid)
    nid_index = jstack.find(kernel_nid)

    if nid_index == -1:
        return "error"
    else:
        start_string = jstack[0:nid_index]
        end_string = jstack[nid_index:]
        start_index = start_string.rfind("\n")
        end_index = end_string.find('\n"') + nid_index
        to_return = jstack[start_index + 1 : end_index]
        if "TIMED_WAITING" not in to_return:
            return to_return

        return "error"


def print_and_exit(error=None, stats=None, threads=None):

    if error is not None:

        result = {}
        result["success"] = "false"
        result["reason"] = error
        result["consuming_threads"] = []
        result["total_time"] = 0
        print(json.dumps(result))
        exit(1)

    else:
        result = {}
        result["success"] = "true"
        result["reason"] = ""
        result["consuming_threads"] = threads
        result["total_time"] = stats["total_time"]
        print(json.dumps(result))
        exit(1)


def compute_jstack(pid, user):

    global jstack_errors
    global java_process_jstacks
    jstack_command = "su - " + user + " -c 'jstack -l " + str(pid) + "'"
    jstack_output, error = subprocess.Popen(
        jstack_command,
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).communicate()

    if error == "":
        java_process_jstacks[pid] = jstack_output
    else:
        jstack_errors.append(error)


def get_threads_stats(top_output):
    split = top_output.split("\n")
    flag = 0
    for i in range(len(split) - 1):
        thread_stats = split[i].split()
        if flag == 0 and len(thread_stats) > 0 and thread_stats[0] == "PID":
            flag = 1
        elif flag == 1 and len(thread_stats) > 0 and thread_stats[0] == "PID":
            return split[i + 1 : -1]
    return []

def get_pid(tid):
    get_pid_command = "cat /proc/" + str(tid) + "/status"
    output, error = subprocess.Popen(
        get_pid_command,
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).communicate()
    if error != "":
        return -1

    output = output.split("\n")
    for line in output:
        infos = line.split()
        if infos[0] == "Tgid:":
            return infos[1]


def compute_top():
    global list_of_pids_string
    global get_java_threads_output
    get_java_threads_command = "top -p " + list_of_pids_string[:-1] + " -H -b -n2"
    get_java_threads_output, error = subprocess.Popen(
        get_java_threads_command,
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).communicate()

    if error != "":
        print_and_exit(error)

    get_java_threads_output = get_threads_stats(get_java_threads_output)


# Example response for top command
# PID USER   PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
# 1 root     20   0  125624   3704   2160 S  0.0  0.0  17:52.53 systemd
def find_cpu_intensive_threads(cutoff, iterations, time_gap, process_cutoff):

    global get_java_threads_output
    global jstack_errors
    threads_score = {}
    global java_process_jstacks
    java_process_users = {}
    get_java_process_command = "ps -e o user:18,pid,pcpu,cmd | grep java"
    threads_per_iteration_state = {}
    global list_of_pids_string
    negative_weight = -0.35
    thread_process_id = {}
    start_time = current_milli_time()
    interesting_java_process = []

    get_java_process_output, error = subprocess.Popen(
        get_java_process_command,
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).communicate()

    if error != "":
        print_and_exit(error)

    get_java_process_output = get_java_process_output.split("\n")[:-1]

    for java_process in get_java_process_output:

        java_process_fields = java_process.split()
        if len(java_process_fields) < 4:
            continue

        if float(java_process_fields[2]) == 0.0:
            continue

        process_cpu = float(java_process_fields[2])
        pid = java_process_fields[1]
        java_process_users[pid] = java_process_fields[0]
        list_of_pids_string += pid + ","

    if not java_process_users:
        print_and_exit("No java process !")

    list_of_pids_string = list_of_pids_string[:-1]

    get_java_cpu_percent_command = "top -p " + list_of_pids_string + " -b -n2"
    get_java_cpu_percent_output, error = subprocess.Popen(
        get_java_cpu_percent_command,
        shell=True,
        executable="/bin/bash",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).communicate()

    if error != "":
        print_and_exit(error)

    get_java_cpu_percent_output = get_threads_stats(get_java_cpu_percent_output)
    list_of_pids_string = ""

    for java_process in get_java_cpu_percent_output:
        java_process_fields = java_process.split()

        if len(java_process_fields) < 12:
            continue

        if float(java_process_fields[8]) > process_cutoff:
            interesting_java_process.append(java_process_fields[0])
            list_of_pids_string += java_process_fields[0] + ","

    if len(interesting_java_process) == 0:
        print_and_exit("No interesting java process !")

    for j in range(iterations):

        threads = []

        for java_process in interesting_java_process:
            jstack_compute_thread = threading.Thread(
                target=compute_jstack,
                args=(java_process, java_process_users[java_process]),
            )
            threads.append(jstack_compute_thread)

        compute_top()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        for java_thread in get_java_threads_output:
            java_thread_fields = java_thread.split()

            if len(java_thread_fields) < 12:
                continue

            if float(java_thread_fields[8]) < cutoff:
                break

            tid = java_thread_fields[0]

            if tid not in thread_process_id:
                pid = get_pid(tid)
                thread_process_id[tid] = pid
            else:
                pid = thread_process_id[tid]

            if pid in java_process_jstacks:
                thread_jstack = get_thread_jstack(java_process_jstacks[pid], int(tid))
                if thread_jstack == "error":
                    continue

                score1 = 1.0
                score2 = 1.0
                score3 = iterations / (iterations - j)
                iteration_state = {}
                iteration_state["index"] = j
                iteration_state["cpu"] = float(java_thread_fields[8])
                iteration_state["jstack"] = thread_jstack
                if tid in threads_per_iteration_state:
                    last_occurence = threads_per_iteration_state[tid][-1]
                    last_index = last_occurence["index"]
                    score1 = iterations / (j - last_index)
                    score2 = iterations / (
                        iterations - len(threads_per_iteration_state[tid])
                    )

                else:
                    threads_per_iteration_state[tid] = []
                    threads_score[tid] = 0.0

                total_score = (score1 + score2 + score3) / 3.0
                if iterations > 1:
                    final_weighted_score = (
                        (total_score - 1.0) / (float(iterations) - 1.0)
                    ) + 1.0
                else:
                    final_weighted_score = 1.0

                threads_score[tid] += final_weighted_score
                threads_per_iteration_state[tid].append(iteration_state)

        time.sleep(time_gap)

    refined_ranks = {}

    if not threads_per_iteration_state:
        print_and_exit(
            "Can not compute jstack!! and reasons are - " + json.dumps(jstack_errors)
        )

    for key in threads_per_iteration_state:
        thread_states = threads_per_iteration_state[key]
        threads_score[key] += negative_weight * (iterations - len(thread_states))
        if threads_score[key] >= 0:
            total_cpu_of_thread = 0.0
            for state in thread_states:
                total_cpu_of_thread += float(state["cpu"])

            refined_ranks[key] = total_cpu_of_thread / len(thread_states)

    sorted_ranks = sorted(
        refined_ranks.items(), key=operator.itemgetter(1), reverse=True
    )

    if len(sorted_ranks) == 0:
        print_and_exit(error="No such Thread")

    consuming_threads_stats = []
    for j in range(len(sorted_ranks)):
        stats = {}
        tid = sorted_ranks[j][0]

        stats["average_cpu"] = sorted_ranks[j][1]
        stats["nid"] = tid
        stats["pid"] = thread_process_id[tid]
        stats["state_per_iteration"] = threads_per_iteration_state[tid]
        consuming_threads_stats.append(stats)

    end_time = current_milli_time()
    stats = {}
    stats["total_time"] = end_time - start_time
    print_and_exit(stats=stats, threads=consuming_threads_stats)


if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cutoff", help="Percentage CPU cutoff for threads")
    ap.add_argument("-i", "--iterations", help="Number of iterations")
    ap.add_argument("-t", "--time", help="Time of sleep between iterations in seconds")
    ap.add_argument("-p", "--process_cutoff", help="Cutoff percentage for java process")

    try:
        args = vars(ap.parse_args())
    except Exception as e:
        print_and_exit(e)

    if args["cutoff"] is None:
        args["cutoff"] = 25.0
    if args["time"] is None:
        args["time"] = 1
    if args["iterations"] is None:
        args["iterations"] = 10
    if args["process_cutoff"] is None:
        args["process_cutoff"] = 50.0

    try:
        cutoff = float(args["cutoff"])
        time_gap = int(args["time"])
        iterations = int(args["iterations"])
        process_cutoff = float(args["process_cutoff"])

    except Exception as e:
        print_and_exit("Arguments parsing error!")

    find_cpu_intensive_threads(cutoff, iterations, time_gap, process_cutoff)
