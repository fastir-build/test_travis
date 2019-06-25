import json
import os
import subprocess
import sys
import zipfile

def Main():
    # Launch fastir_artifacts
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

    # Check if collection was successful
    if b'Finished collecting artifacts' not in command_output:
        print('Artifacts collection did not finish')
        return False

    # Check output directory
    output_directory = list(filter(lambda x: x.startswith('20'), os.listdir('.')))
    if len(output_directory) != 1:
        print('Output directory not found')
        return False
    output_directory = output_directory[0]

    # Fix output directory ownership
    if sys.platform == 'darwin' or sys.platform == 'linux':
        command = ['sudo', 'chown', '-R', f'{os.getuid()}:{os.getgid()}', output_directory]
        subprocess.check_output(command)

    # Check COMMAND artifacts
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
            for command, output in commands['IPTablesRules'].items():
                if 'iptables' not in command or 'Chain INPUT' not in output:
                    print('Wrong IPTablesRules content')
                    print(json.dumps(commands['IPTablesRules']))
                    return False
        elif 'MacOSLoadedKexts' in commands:
            if not commands['MacOSLoadedKexts']:
                print('Empty MacOSLoadedKexts')
                return False
            for command, output in commands['MacOSLoadedKexts'].items():
                if 'kextstat' not in command or 'Name' not in output:
                    print('Wrong MacOSLoadedKexts content')
                    print(json.dumps(commands['MacOSLoadedKexts']))
                    return False
        elif 'WindowsFirewallEnabledRules' in commands:
            if not commands['WindowsFirewallEnabledRules']:
                print('Empty WindowsFirewallEnabledRules')
                return False
            for command, output in commands['WindowsFirewallEnabledRules'].items():
                if 'netsh.exe' not in command or 'Windows Defender Firewall Rules:' not in output:
                    print('Wrong WindowsFirewallEnabledRules content')
                    print(json.dumps(commands['WindowsFirewallEnabledRules']))
                    return False
        else:
            print('Usual commands not found')
            print(json.dumps(commands))
            return False

    # Check FILE artifacts
    files_output = list(filter(lambda x: x.endswith('-files.zip'), os.listdir(output_directory)))
    if len(files_output) != 1:
        print('files.zip not found')
        return False
    files_output = os.path.join(output_directory, files_output[0])
    with zipfile.ZipFile(files_output) as z:
        nl = z.namelist()
        if '/etc/passwd' in nl and '/proc/mounts' in nl:
            with z.open('/etc/passwd') as f:
                if b'root' not in f.read():
                    print('Wrong /etc/passwd file')
                    return False
            with z.open('/proc/mounts') as f:
                if b' / ' not in f.read():
                    print('Wrong /proc/mounts file')
                    return False
        elif '/private/etc/passwd' in nl:
            with z.open('/private/etc/passwd') as f:
                if b'root' not in f.read():
                    print('Wrong /private/etc/passwd file')
                    return False
        elif 'C/$MFT' in nl and 'C/Windows/System32/drivers/etc/hosts' in nl:
            with z.open('C/$MFT') as f:
                if b'FILE0' not in f.read():
                    print('Wrong C/$MFT')
                    return False
            with z.open('C/Windows/System32/drivers/etc/hosts') as f:
                if b'This is a sample HOSTS file used by Microsoft TCP/IP for Windows.' not in f.read():
                    print('Wrong C/Windows/System32/drivers/etc/hosts')
                    return False
        else:
            print('Usual files not found')
            print(nl)
            return False

    # Check logs file
    logs_output = list(filter(lambda x: x.endswith('-logs.txt'), os.listdir(output_directory)))
    if len(logs_output) != 1:
        print('logs.txt not found')
        return False
    logs_output = os.path.join(output_directory, logs_output[0])
    with open(logs_output, 'r') as f:
        d = f.read()
        if 'Loading artifacts' not in d or 'Collecting artifacts from ' not in d or 'Collecting file ' not in d or 'Collecting command ' not in d or 'Finished collecting artifacts' not in d:
            print('Wrong logs.txt')
            print(d)
            return False

    # Check WMI artifacts
    if sys.platform == 'win32':
        wmi_output = list(filter(lambda x: x.endswith('-wmi.json'), os.listdir(output_directory)))
        if len(wmi_output) != 1:
            print('wmi.json not found')
            return False
        wmi_output = os.path.join(output_directory, wmi_output[0])
        with open(wmi_output, 'r') as f:
            wmi = json.load(f)
            if 'WMIDrivers' not in wmi:
                print('WMIDrivers not found')
                return False
            if not wmi['WMIDrivers']:
                print('Empty WMIDrivers')
                return False
            for query, output in wmi['WMIDrivers'].items():
                if 'SELECT' not in query:
                    print('Wrong WMIDrivers query')
                    print(query)
                    return False
                if len(output) == 0:
                    print('Wrong WMIDrivers output')
                    print(output)
                    return False
                if 'Description' not in output[0] and 'DisplayName' not in output[0]:
                    print('Wrong WMIDrivers output')
                    print(output[0])
                    return False

    return True

if __name__ == '__main__':
    if not Main():
        sys.exit(1)
    else:
        sys.exit(0)
