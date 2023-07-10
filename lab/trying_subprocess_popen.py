import subprocess

def run_command(command):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        shell=False,
    )
    output, err = process.communicate()
    return output.decode("utf-8")

if __name__ == "__main__":
    command = ["kubectl", "exec", "-it", "-n", "default", "java-deployment-66c74f6dbd-vjzhq", "-c", "java-app", "--", "bash", "-c", "time ps -ef"]
    output = run_command(command)
    print(output)
