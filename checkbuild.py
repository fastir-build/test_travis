import os
import subprocess
import sys

def Main():
    if sys.platform == 'linux':
        command = os.path.join('dist', 'fastir_artifacts', 'fastir_artifacts')
        command = ['sudo', command]
    elif sys.platform == 'darwin':
        command = os.path.join('dist', 'fastir_artifacts', 'fastir_artifacts')
        command = ['sudo', command]
    elif sys.platform == 'win32':
        command = os.path.join('dist', 'fastir_artifacts', 'fastir_artifacts.exe')
    else:
        return False

    try:
        command_output = subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        command_output = e.output

    print(command_output)

    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
