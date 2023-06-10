import argparse

others_category = "Others"
prefixes_to_ignore = ['cluster-ClusterId','grpc-default','kafka-producer-network-thread','broadcastRedisContainer','cluster-rtt-ClusterId','CompilerThread0']
category_vs_identifier_keyword = {'Mongo':'MongoTemplateInternal',"Elasticsearch":'elasticsearch'}
category_vs_stack_frame_count = {}
category_vs_stack_frames = {}
category_vs_runnable_stack_frame_count = {}
category_vs_runnable_stack_frames = {}
fetch_stack_frame = False
fetch_runnable_stack_frame = False
prefixes_to_fetch = None

def define_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('files',nargs='+',metavar='FILENAME1 FILENAME2', help='Input Jstack files')
    parser.add_argument('-f', '--fetch', action='store_true', help='Fetch matching stack frames')
    parser.add_argument('-fr', '--fetch_runnable', action='store_true', help='Fetch runnable matching stack frames')
    parser.add_argument('-p', '--prefix',nargs='+',metavar='prefix', help='Thread Prefixes to search for')
    return parser.parse_args()

def get_file_contents(filePath):
    with open(filePath, 'r') as file:
        # Read the entire content of the file
        content = file.read()
        return content

def execute(jstack):
    stack_frames = get_stack_frames(jstack)
    add_stack_frame_to_appropriate_type(stack_frames)

# Get stack trace for a process using jstack
def get_stack_frames(jstack):
    stack_trace = jstack.strip()
    stack_frames = stack_trace.split("\n\n")
    return filterStackFrames(stack_frames)

def filterStackFrames(stack_frames):
    if prefixes_to_fetch is not None:
       return fetchFramesMatchingPrefix(stack_frames)
    return fetchFramesIgnoringPrefix(stack_frames)
    
def fetchFramesMatchingPrefix(stack_frames):
    filteredStackFrames = []
    for stack_frame in stack_frames:
        for prefix in prefixes_to_fetch:
            if prefix in stack_frame:
                filteredStackFrames.append(stack_frame)
                break;
    return filteredStackFrames

def fetchFramesIgnoringPrefix(stack_frame):
    filteredStackFrames = []
    for stack_frame in stack_frames:
        ignoreFrame = False;
        for prefix in prefixes_to_ignore:
            if prefix in stack_frame:
                ignoreFrame = True
                break;
        if(ignoreFrame is False):
            filteredStackFrames.append(stack_frame)
    return filteredStackFrames

# Query stack frames for a category and add to map
def add_stack_frame_to_appropriate_type(stack_frames):
    matched_a_type = False
    category_vs_stack_frame = {}
    
    for stack_frame in stack_frames:
        for category in category_vs_identifier_keyword:
            identifier_keyword = category_vs_identifier_keyword[category]
            if identifier_keyword in stack_frame:
                update_category_vs_stack_frame_data(category, stack_frame)
                matched_a_type = True
                break
        if matched_a_type is False:
            update_category_vs_stack_frame_data(others_category,stack_frame)

    return category_vs_stack_frame;

def update_category_vs_stack_frame_data(category, stack_frame):
    if category_vs_stack_frame_count.get(category) is None:
        category_vs_stack_frame_count[category] = 0
    category_vs_stack_frame_count[category] +=1


    if fetch_stack_frame:
        if category_vs_stack_frames.get(category) is None:
            category_vs_stack_frames[category] = []
        category_vs_stack_frames[category].append(stack_frame)

    if isThreadRunnable(stack_frame):
        update_category_vs_runnable_stack_frame_data(category,stack_frame)


def update_category_vs_runnable_stack_frame_data(category,stack_frame):
    if category_vs_runnable_stack_frame_count.get(category) is None:
        category_vs_runnable_stack_frame_count[category] = 0
    category_vs_runnable_stack_frame_count[category] +=1


    if fetch_runnable_stack_frame:
        if category_vs_runnable_stack_frames.get(category) is None:
            category_vs_runnable_stack_frames[category] = []
        category_vs_runnable_stack_frames[category].append(stack_frame) 


def print_data(category_vs_stack_frames,print_stack_trace = False):
    for category in category_vs_identifier_keyword:
        print_data_for_category(category,print_stack_trace)
    print_data_for_category(others_category,print_stack_trace)

def print_data_for_category(category,print_stack_trace):
    if category_vs_stack_frame_count.get(category) is not None:
        stack_frames_count = category_vs_stack_frame_count[category]
        print("\n {} count is {}".format(category, stack_frames_count))
    if category_vs_runnable_stack_frame_count.get(category) is not None:
        runnable_stack_frames_count = category_vs_runnable_stack_frame_count[category]
        print("\n {} runnable count is {}".format(category, runnable_stack_frames_count))
        if print_stack_trace:
            stack_frames_with_category = category_vs_stack_frames[category]
            for stack_frame in stack_frames_with_category:
                print(stack_frame)  
        if fetch_runnable_stack_frame:
            runnable_stack_frames_with_category = category_vs_runnable_stack_frames[category]
            for stack_frame in runnable_stack_frames_with_category:
                print(stack_frame)    

def isThreadRunnable(stack_frame):
    return 'RUNNABLE' in stack_frame


if __name__ == "__main__":
    args = define_args()
    fetch_stack_frame = args.fetch
    fetch_runnable_stack_frame = args.fetch_runnable
    prefixes_to_fetch = args.prefix
    for file in args.files:
        jstack = get_file_contents(file)
        execute(jstack)
    print_data(category_vs_stack_frames,args.fetch)

