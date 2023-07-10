import subprocess

command_list = [
    "kubectl", "exec", "-it", 
    '-n', 'default', 'java-deployment-66c74f6dbd-vjzhq',
    "-c", 'java-app', 
    "--", 
    "bash", "-c",
    "'time ps -ef'"
]

command_list = " ".join(command_list)
result = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
output, err = result.communicate()

output = output.decode("utf-8")
err = err.decode("utf-8")

output = output.strip()
print(output)

output = output.replace("\r", "")
time_output = output.split("\n\n")
print(len(time_output))
# output = output.replace(time_output, "")
#
# print(output)
# print('-----------')
# print(time_output)
