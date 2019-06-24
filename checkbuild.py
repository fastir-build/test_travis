import os
import subprocess
import sys

def Main():
    if sys.platform == 'linux':
        command = os.path.join('dist', 'main', 'main')
    elif sys.platform == 'darwin':
        command = os.path.join('dist', 'main', 'main')
    elif sys.platform == 'win32':
        command = os.path.join('dist', 'main', 'main.exe')
    else:
        return False

    print(subprocess.check_output(command, stderr=subprocess.STDOUT))

    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
