import os
import re

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

if __name__ == "__main__":
    break_multiple_into_singleton()
