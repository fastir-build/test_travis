import os
import subprocess
import sys

def Main():
    if sys.platform == 'darwin' or sys.platform == 'linux':
        command = os.path.join('dist', 'fastir_artifacts', 'fastir_artifacts')
        command = ['sudo', command]
    elif sys.platform == 'win32':
        command = os.path.join('dist', 'fastir_artifacts', 'fastir_artifacts.exe')
    else:
        print(f'Unknown platform {sys.platform}')
        return False

    try:
        command_output = subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        command_output = e.output
        return False
    finally:
        print(str(command_output, 'utf-8'))

    if b'Finished collecting artifacts' not in command_output:
        return False

    output_directory = list(filter(lambda x: x.startswith('20'), os.listdir('.')))[0]

#    if sys.platform == 'darwin' or sys.platform == 'linux':
#        command = ['sudo', 'chown', '-R', f'{os.getuid()}:{os.getgid()}', output_directory]
#        subprocess.check_output(command, stderr=subprocess.STDOUT)

    print(os.listdir(output_directory))

    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
