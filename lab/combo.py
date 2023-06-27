import os
import re
import subprocess

def classify_as_multple_or_singleton_jstacks():
    sample_jstacks_folder = "/Users/sarvjotsingh/dev/QueryStackTrace/sample_jstacks/"

    for filename in os.listdir(sample_jstacks_folder):
        if not filename.endswith(".txt"):
            continue

        with open(sample_jstacks_folder + filename) as file:
            jstacks_file = file.read()
        
        pattern = r"(?m)(JNI global ref.*$)"
        iterable_matches = re.finditer(pattern, jstacks_file)
        length_of_matches = len(list(iterable_matches))

        # find length of matches
        if length_of_matches == 1:
            os.rename(sample_jstacks_folder + filename, sample_jstacks_folder + "singleton_jstacks/" + filename)
        elif length_of_matches > 1:
            os.rename(sample_jstacks_folder + filename, sample_jstacks_folder + "multiple_jstacks/" + filename)

def get_all_thread_states():
    sample_jstacks_folder = "/Users/sarvjotsingh/dev/QueryStackTrace/sample_jstacks/"
    jstack_folders = ["singleton_jstacks", "multiple_jstacks"]
    thread_states = set()

    for folder in jstack_folders:
        for filename in os.listdir(sample_jstacks_folder + folder):
            if not filename.endswith(".txt"):
                continue

            with open(sample_jstacks_folder + folder + "/" + filename) as file:
                jstacks_file = file.read()
            
            pattern = r"(?m)(java.lang.Thread.State:.*$)"
            matches = re.finditer(pattern, jstacks_file)

            for match in matches:   
                state = match.group(0)[24:]
                thread_states.add(state)

    # sort the thread states
    thread_states = sorted(thread_states)

    for state in thread_states:
        print(state)

def break_multiple_into_singleton():
    sample_jstacks_folder = "/Users/sarvjotsingh/dev/QueryStackTrace/sample_jstacks/"
    multiple_jstacks_folder = sample_jstacks_folder + "multiple_jstacks/"
    converted_jstacks_folder = sample_jstacks_folder + "converted_jstacks/"

    for filename in os.listdir(multiple_jstacks_folder):
        if not filename.endswith(".txt"):
            continue

        with open(multiple_jstacks_folder + filename) as file:
            jstacks_file = file.read()
        
        pattern = r"(?m)(JNI global ref.*$)"
        matches = re.finditer(pattern, jstacks_file)

        it = 0
        prev_ind = 0
        for match in matches:
            it += 1
            jstack = jstacks_file[prev_ind:match.end() + 1] 
            prev_ind = match.end() + 1

            target_filename = converted_jstacks_folder + filename[:-4] + "_" + str(it) + ".txt"

            if not os.path.exists(os.path.dirname(target_filename)):
                os.makedirs(os.path.dirname(target_filename))
            with open(target_filename, "w") as file:
                file.write(jstack)

def subprocess_call(command_list):
    result = subprocess.Popen(command_list, stdout=subprocess.PIPE)
    output, _ = result.communicate()
    return output.strip()

def get_jstack_of_java_process(process_id):
    jstack = subprocess_call(["jstack", str(process_id)])
    return jstack 

def get_active_java_processes():
    output = subprocess_call(["ps", "-e"])
    lines = output.split(b"\n")

    processes = []
    for line in lines:
        if b"java" in line:
            cols = line.split()
            process_id = cols[0]
            processes.append(process_id)

    return processes

def get_jstacks_of_active_java_processes(processes):
    jstacks = []

    for process_id in processes:
        jstacks.append(get_jstack_of_java_process(process_id))

    return jstacks

def parse_top_file(top_file_path):
    with open(top_file_path, "r") as f:
        top = f.read()

    header_regex = r"(?m)(PID USER.*$)"
    header = re.search(header_regex, top)

    if header is not None:
        # get the text after this header
        header_text = header.group(0)
        header_text_index = top.index(header_text)
        top_threads = top[header_text_index + len(header_text):]

        top_threads = top_threads.split("\n")
        thread_ids = [thread.split()[0] for thread in top_threads if thread != ""]

        nids = [hex(int(thread_id)) for thread_id in thread_ids]
        print(nids[:30])
    else: 
        exit("Given top file does is not in the correct format")

def get_hash_nid_tuple():
    multiple_jstacks_folder = "/Users/sarvjotsingh/dev/AnalyseJStack/sample_jstacks/multiple_jstacks/"

    hash_nid_regex = r"(?m)(\"\s#(\d+)\s.*nid=(0x[0-9a-f]+)\s.*)"
    for filename in os.listdir(multiple_jstacks_folder):
        hash_nid_tuples = []
        
        with open(multiple_jstacks_folder + filename) as file:
            jstacks_file = file.read()

        matches = re.finditer(hash_nid_regex, jstacks_file)
        for match in matches:
            hash_nid_tuples.append((match.group(2), match.group(3)))

        for i in hash_nid_tuples:
            for j in hash_nid_tuples:
                if i[0] == j[0] and i[1] != j[1]:
                    print("Hash collision found")

        # new_file_name = "hash_nid_tuples/" + filename[:-4] + ".txt"
        #
        # if not os.path.exists(os.path.dirname(new_file_name)):
        #     os.makedirs(os.path.dirname(new_file_name))
        # with open(new_file_name, "w") as file:
        #     file.write(str(hash_nid_tuple))

if __name__ == "__main__":
    get_hash_nid_tuple()

    # parse_top_file("/Users/sarvjotsingh/docker_top_output.txt")

    # processes = get_active_java_processes()
    #
    # jstacks_all_iterations = []
    # for i in range(5):
    #     jstacks = get_jstacks_of_active_java_processes(processes)
    #     jstacks_all_iterations.extend(jstacks)
    #
    # for jstack in jstacks_all_iterations:
    #     print(jstack)
