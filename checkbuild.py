import json
import os
import subprocess
import sys
import zipfile

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
        print('Artifacts collection did not finish')
        return False

    output_directory = list(filter(lambda x: x.startswith('20'), os.listdir('.')))
    if len(output_directory) != 1:
        print('Output directory not found')
        return False
    output_directory = output_directory[0]

    if sys.platform == 'darwin' or sys.platform == 'linux':
        command = ['sudo', 'chown', '-R', f'{os.getuid()}:{os.getgid()}', output_directory]
        subprocess.check_output(command)

    commands_output = list(filter(lambda x: x.endswith('-commands.json'), os.listdir(output_directory)))
    if len(commands_output) != 1:
        print('commands.json not found')
        return False
    commands_output = os.path.join(output_directory, commands_output[0])
    with open(commands_output, 'r') as f:
        commands = json.load(f)
        print(json.dumps(commands))

    files_output = list(filter(lambda x: x.endswith('-files.zip'), os.listdir(output_directory)))
    if len(files_output) != 1:
        print('files.zip not found')
        return False
    files_output = os.path.join(output_directory, files_output[0])
    with zipfile.ZipFile(files_output) as f:
        for n in f.filelist:
            print(n)

    logs_output = list(filter(lambda x: x.endswith('-logs.txt'), os.listdir(output_directory)))
    if len(logs_output) != 1:
        print('logs.txt not found')
        return False
    logs_output = os.path.join(output_directory, logs_output[0])
    with open(logs_output, 'r') as f:
        for l in f.readlines():
            print(l.strip())

    if sys.platform == 'win32':
        wmi_output = list(filter(lambda x: x.endswith('-wmi.json'), os.listdir(output_directory)))
        if len(wmi_output) != 1:
            print('wmi.json not found')
            return False
        wmi_output = os.path.join(output_directory, wmi_output[0])
        with open(wmi_output, 'r') as f:
            wmi = json.load(f)
            print(json.dumps(wmi))

    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
