import subprocess
import threading
import time

def put_wifi_to_monitor_mode():
    command_execute_object = subprocess.run(['sudo','airmon-ng','start','wlan0'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return command_execute_object.returncode

def read_output_from_process(proc):
    for line in iter(proc.stdout.readline, b''):
        print('got line: {0}'.format(line.decode('utf-8')), end='')


def start_sniff_probes():
    #execute the sniff-probes.sh
    child_process_object = subprocess.Popen(['./sniff-probes.sh'],
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    t = threading.Thread(target=read_output_from_process, args=(child_process_object,))
    t.start()
    t.join()

print("***** Starting the Sniff script *****")
print("Putting the wifi on monitor mode")
exit_code_from_command = put_wifi_to_monitor_mode()

#if something went wrong while putting the wifi on monitor mode exit
if exit_code_from_command != 0:
    print("Something went wrong!!!")
    exit(1)

#if everything was setup correctly start the sniff_probes function
start_sniff_probes()