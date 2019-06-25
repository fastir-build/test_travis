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
        if 'IPTablesRules' in commands:
            if not commands['IPTablesRules']:
                print('Empty IPTablesRules')
                return False
            for command, output in commands['IPTablesRules']:
                if 'iptables' not in command or 'Chain INPUT' not in output:
                    print('Wrong IPTablesRules content')
                    print(json.dumps(commands['IPTablesRules']))
                    return False
        elif 'MacOSLoadedKexts' in commands:
            if not commands['MacOSLoadedKexts']:
                print('Empty MacOSLoadedKexts')
                return False
            for command, output in commands['MacOSLoadedKexts']:
                if 'kextstat' not in command or 'Name' not in output:
                    print('Wrong MacOSLoadedKexts content')
                    print(json.dumps(commands['MacOSLoadedKexts']))
                    return False
        elif 'WindowsFirewallEnabledRules' in commands:
            if not commands['WindowsFirewallEnabledRules']:
                print('Empty WindowsFirewallEnabledRules')
                return False
            for command, output in commands['WindowsFirewallEnabledRules']:
                if 'netsh.exe' not in command or 'Windows Defender Firewall Rules:' not in output:
                    print('Wrong WindowsFirewallEnabledRules content')
                    print(json.dumps(commands['WindowsFirewallEnabledRules']))
                    return False
        else:
            print('Usual commands not found')
            print(json.dumps(commands))
            return False

    files_output = list(filter(lambda x: x.endswith('-files.zip'), os.listdir(output_directory)))
    if len(files_output) != 1:
        print('files.zip not found')
        return False
    files_output = os.path.join(output_directory, files_output[0])
    with zipfile.ZipFile(files_output) as f:
        for zi in f.infolist():
            print(f'{zi.filename} {zi.file_size}')

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
