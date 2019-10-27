import subprocess
import threading
import moment
import re

timestamp_regex_pattern = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+' #get the timestamp from the probe request
rssi_regex_pattern = '-?\d+dBm' #get the rssi value from the probe request
mac_id_regex_pattern = 'SA:(?:[0-9a-fA-F]:?){12}' #need to remove SA: in the result to get the mac id from the matched string
ssid_regex_pattern = 'Probe Request \(.*\)' #need to remove the "Probe Request" in the result to get the ssid , would be null in case of null probe request

frame_to_send = {'frame': {'probes': {'directed': [],'null': []}}} # define a frame structure with probe requests object with two classifications directed probe requests and null probe requests

def build_frame_to_send(timestamp,rssi,mac_id,ssid=None):
    if ssid is not None:
        #this means it is a directed probe request
        frame_to_send['frame']['probes']['directed'].append({'timestamp':  str(moment.date(timestamp)),'rssi': rssi,'mac_id':mac_id,'ssid': ssid})
    else:
        #this means it is a null probe request
        frame_to_send['frame']['probes']['null'].append({'timestamp':  str(moment.date(timestamp)),'rssi': rssi,'mac_id':mac_id,'ssid': None})


def process_output_line(output_line):
    #TODO: Handle Else cases for this i.e throw error and report errors
    timestamp_search = re.search(timestamp_regex_pattern,output_line)
    if timestamp_search is not None:
        timestamp = timestamp_search.group()
    rssi_search = re.search(rssi_regex_pattern,output_line)
    if rssi_search is not None:
        rssi = rssi_search.group()
    mac_id_search = re.search(mac_id_regex_pattern,output_line)
    if mac_id_search is not None:
        mac_id_with_sa = mac_id_search.group()
        mac_id = re.sub('SA:','',mac_id_with_sa) #extract the macid without the SA
    ssid_search = re.search(ssid_regex_pattern,output_line)
    if ssid_search is not None:
        ssid_with_probe = ssid_search.group()
        ssid = re.sub('Probe Request \(|\)','',ssid_with_probe) #extract the ssid (if any)
        if not ssid: #i.e SSID is '' it is a null probe request
            null_request = True
        else:
            null_request = False
    
    

def put_wifi_to_monitor_mode():
    command_execute_object = subprocess.run(['sudo','airmon-ng','start','wlan0'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return command_execute_object.returncode

def read_output_from_process(proc):
    for line in iter(proc.stdout.readline, b''):
        print('got line: {0}'.format(line.decode('utf-8')), end='')
        process_output_line(line.decode('utf-8'))


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