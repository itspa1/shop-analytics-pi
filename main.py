import os
import subprocess
import threading
import time
import moment
import re
import json
from dotenv import load_dotenv, find_dotenv
from mqttClient import MqttClient

# load the .env file
load_dotenv(find_dotenv())

# get the timestamp from the probe request
timestamp_regex_pattern = '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+'
rssi_regex_pattern = '-?\d+dBm'  # get the rssi value from the probe request
# need to remove SA: in the result to get the mac id from the matched string
mac_id_regex_pattern = 'SA:(?:[0-9a-fA-F]:?){12}'
# need to remove the "Probe Request" in the result to get the ssid , would be null in case of null probe request
ssid_regex_pattern = 'Probe Request \(.*\)'

# define a frame structure with probe requests object with two classifications directed probe requests and null probe requests
frame_to_send = {'frame': {'probes': {'directed': [], 'null': []}}}

TIMER = time.time()
# get the refresh interval in seconds from the env file
refresh_interval = int(os.getenv('REFRESH_INTERVAL'))

# flags to maintain object integrity between threads
IS_PROCESSING = False
DID_NOT_SEND = False


def send_frame():
    global TIMER
    global IS_PROCESSING
    global DID_NOT_SEND
    global frame_to_send
    global mqtt_client
    if IS_PROCESSING:
        # Set this flag to True, so that after processing is complete that frame is sent
        DID_NOT_SEND = True
    else:
        # set this flag back to false so that if previous was True, that case is handled
        DID_NOT_SEND = False
        if frame_to_send['frame']['probes']['null'] == [] and frame_to_send['frame']['probes']['directed'] == []:
            # means there is nothing to send or nothing was captured between that interval
            print("Nothing to send! No Probes were captured in the last interval/cycle.")
        else:
            # send the frame on the publish and reset it back to empty
            mqtt_client.client.publish(
                'frame_topic', json.dumps(frame_to_send))
            # print(json.dumps(frame_to_send))
            print("Sent frame to Server!")
            frame_to_send = {'frame': {'probes': {'directed': [], 'null': []}}}

    TIMER = TIMER + refresh_interval
    threading.Timer(TIMER - time.time(), send_frame).start()


def build_frame_to_send(timestamp, rssi, mac_id, ssid=None):
    global frame_to_send
    global IS_PROCESSING
    global DID_NOT_SEND
    global mqtt_client

    print(f'{timestamp} {rssi} {mac_id} {ssid}')
    # Set the flag to True to tell others using the global object to wait till processing is complete
    IS_PROCESSING = True
    if ssid is not None:
        # this means it is a directed probe request
        frame_to_send['frame']['probes']['directed'].append({'timestamp':  str(
            moment.date(timestamp)), 'rssi': rssi, 'mac_id': mac_id, 'ssid': ssid})
    else:
        # this means it is a null probe request
        frame_to_send['frame']['probes']['null'].append({'timestamp':  str(
            moment.date(timestamp)), 'rssi': rssi, 'mac_id': mac_id, 'ssid': None})
    # Set this flag back to False to tell others using the global object that processing is complete and the object is usable
    IS_PROCESSING = False

    # TODO: Handle errors!!!
    # IF Did not send because it was still processing, now send and reset back the frame object back to empty
    if DID_NOT_SEND:
        mqtt_client.client.publish('frame_topic', json.dumps(frame_to_send))
        frame_to_send = {'frame': {'probes': {'directed': [], 'null': []}}}
        DID_NOT_SEND = False


def process_output_line(output_line):
    # TODO: Handle Else cases for this i.e throw error and report errors
    timestamp_search = re.search(timestamp_regex_pattern, output_line)
    if timestamp_search is not None:
        timestamp = timestamp_search.group()
    rssi_search = re.search(rssi_regex_pattern, output_line)
    if rssi_search is not None:
        rssi = rssi_search.group()
    mac_id_search = re.search(mac_id_regex_pattern, output_line)
    if mac_id_search is not None:
        mac_id_with_sa = mac_id_search.group()
        # extract the macid without the SA
        mac_id = re.sub('SA:', '', mac_id_with_sa)
    ssid_search = re.search(ssid_regex_pattern, output_line)
    if ssid_search is not None:
        ssid_with_probe = ssid_search.group()
        # extract the ssid (if any)
        ssid = re.sub('Probe Request \(|\)', '', ssid_with_probe)
        if not ssid:  # i.e SSID is '' it is a null probe request
            null_request = True
            build_frame_to_send(timestamp, rssi, mac_id)
        else:
            null_request = False
            build_frame_to_send(timestamp, rssi, mac_id, ssid)


def put_wifi_to_monitor_mode():
    command_execute_object = subprocess.run(
        ['sudo', 'airmon-ng', 'start', 'wlan0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return command_execute_object.returncode


def read_output_from_process(proc):
    for line in iter(proc.stdout.readline, b''):
        # print('got line: {0}'.format(line.decode('utf-8')), end='')
        process_output_line(line.decode('utf-8'))


def start_sniff_probes():
    # execute the sniff-probes.sh
    child_process_object = subprocess.Popen(['./sniff-probes.sh'],
                                            shell=True,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)
    send_frame()
    t = threading.Thread(target=read_output_from_process,
                         args=(child_process_object,))
    t.start()
    t.join()


def connect_to_mqtt_client(username, password, host, port):
    try:
        global mqtt_client
        mqtt_client.create_client()
        mqtt_client.client.username_pw_set(username, password)
        mqtt_client.client.on_connect = mqtt_client.on_connect_handler
        mqtt_client.client.on_disconnect = mqtt_client.on_disconnect_handler
        mqtt_client.client.on_message = mqtt_client.on_message_handler
        mqtt_client.client.connect(host, port)
        mqtt_client.start()
    except Exception as error:
        print("Error while connecting to mqtt broker " + error)
        exit(1)


print("***** Starting the Sniff script *****")
print("Putting the wifi on monitor mode")
exit_code_from_command = put_wifi_to_monitor_mode()

# if something went wrong while putting the wifi on monitor mode exit
if exit_code_from_command != 0:
    print("Something went wrong while putting the wifi on monitor mode!!!")
    exit(1)

mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = os.getenv("MQTT_PORT")
mqtt_client = MqttClient("pi_connect", "Random", [])
connect_to_mqtt_client(mqtt_username, mqtt_password, mqtt_host, int(mqtt_port))

# if everything was setup correctly start the sniff_probes function
start_sniff_probes()
