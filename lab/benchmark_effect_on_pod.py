import subprocess

command_list = ["kubectl", "exec", "-it", '-n', namespace, pod_name, "-c", container_name, "--", "echo", "'Hello World'"]
result = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
