import os

jstacks_folder = "/Users/sarvjotsingh/dev/AnalyseJStack/sample_jstacks/multiple_jstacks/"
target_folder = "/Users/sarvjotsingh/dev/AnalyseJStack/sample_jstacks/analysed_jstacks/"

if not os.path.exists(target_folder):
    os.makedirs(target_folder)

for file in os.listdir(jstacks_folder):
    os.system("python2 ajs.py -FRJT -f " + jstacks_folder + file)
    even_more_targeted_folder = target_folder + file

    if not os.path.exists(even_more_targeted_folder):
        os.makedirs(even_more_targeted_folder)

    os.system("mv .ajs/analysis.txt " + even_more_targeted_folder + "/analysis.txt")
    os.system("mv .ajs/jstacks.txt " + even_more_targeted_folder + "/jstacks.txt")
