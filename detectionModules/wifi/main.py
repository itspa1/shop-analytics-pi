import json
import os
import re
import signal
import sys
import threading
import time

import bugsnag
import moment
from dotenv import find_dotenv, load_dotenv

from mqttClient import MqttClient

# load the .env file
load_dotenv(find_dotenv())

# get the refresh interval in seconds from the env file
refresh_interval = int(os.getenv('REFRESH_INTERVAL'))

# initialize the timer to keep the clock
TIMER = time.time()

# Get bugsnag key to notify errors onto bugsnag
BUGSNAG_KEY = os.getenv("BUGSNAG_KEY")

bugsnag.configure(api_key=BUGSNAG_KEY)

# flags to maintain object integrity between threads
IS_PROCESSING = False
DID_NOT_SEND = False


def build_frame_to_send(client, timestamp, rssi, mac_id, ssid=None):
    global IS_PROCESSING
    global DID_NOT_SEND

    print(f'{timestamp} {rssi} {mac_id} {ssid}')
    # Set the flag to True to tell others using the global object to wait till processing is complete
    IS_PROCESSING = True
    if ssid is not None:
        # this means it is a directed probe request
        client.frame_to_send.value['frame']['probes']['directed'].append({'timestamp':  str(
            moment.date(timestamp)), 'rssi': rssi, 'mac_id': mac_id, 'ssid': ssid})
    else:
        # this means it is a null probe request
        client.frame_to_send.value['frame']['probes']['null'].append({'timestamp':  str(
            moment.date(timestamp)), 'rssi': rssi, 'mac_id': mac_id, 'ssid': None})
    # Set this flag back to False to tell others using the global object that processing is complete and the object is usable
    IS_PROCESSING = False

    # TODO: Handle errors!!!
    # IF Did not send because it was still processing, now send and reset back the frame object back to empty
    if DID_NOT_SEND:
        # add timestamp to the frame to help in creating files
        client.frame_to_send.value["timestamp"] = str(
            moment.utcnow())
        mqtt_client.client.publish(
            'frame_topic', json.dumps(client.frame_to_send.value))
        client.frame_to_send.value = {
            'frame': {'probes': {'directed': [], 'null': []}}}
        DID_NOT_SEND = False


def send_frame(client):
    global TIMER
    global IS_PROCESSING
    global DID_NOT_SEND
    global mqtt_client
    if IS_PROCESSING:
        # Set this flag to True, so that after processing is complete that frame is sent
        DID_NOT_SEND = True
    else:
        # set this flag back to false so that if previous was True, that case is handled
        DID_NOT_SEND = False
        if client.frame_to_send.value['frame']['probes']['null'] == [] and client.frame_to_send.value['frame']['probes']['directed'] == []:
            # means there is nothing to send or nothing was captured between that interval
            print("Nothing to send! No Probes were captured in the last interval/cycle.")
        else:
            # send the frame on the publish and reset it back to empty
            print(mqtt_client.connected)
            # add timestamp to the frame to help in creating files
            client.frame_to_send.value["timestamp"] = str(
                moment.utcnow())
            json_in_str = json.dumps(client.frame_to_send.value)
            mqtt_client.publish_data(json_in_str)
            # reset the frame back to initial value
            client.frame_to_send.value = {
                'frame': {'probes': {'directed': [], 'null': []}}}
    TIMER = TIMER + refresh_interval
    timer_thread = threading.Timer(TIMER - time.time(), send_frame, [client])
    timer_thread.daemon = True
    timer_thread.start()


def connect_to_mqtt_client(username, password, host, port):
    try:
        global mqtt_client
        mqtt_client.create_client()
        mqtt_client.client.username_pw_set(username, password)
        mqtt_client.client.on_connect = mqtt_client.on_connect_handler
        mqtt_client.client.on_disconnect = mqtt_client.on_disconnect_handler
        mqtt_client.client.on_message = mqtt_client.on_message_handler
        mqtt_client.client.connect(host, port, keepalive=60)
        mqtt_client.start()
    except Exception as error:
        bugsnag.notify(
            Exception("Error while connecting to mqtt broker " + str(error)))
        print("Error while connecting to mqtt broker " + str(error))
        exit(1)


mqtt_username = os.getenv("MQTT_USERNAME")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = os.getenv("MQTT_PORT")
mqtt_client = MqttClient("pi_connect", "Random", [])
connect_to_mqtt_client(mqtt_username, mqtt_password, mqtt_host, int(mqtt_port))

sniff_type = os.getenv('SNIFF_TYPE')


def initializeWifiModule():
    # check the type of packet capture to use, whether to use the native raspberry-pi wifi or external esp8266
    if sniff_type == "NATIVE":
        from detectionModules.wifi.nativeSnifferClient import NativeSnifferClient
        # initialize all the necessary configs for this mode of sniffing

        # get the timestamp from the probe request
        timestamp_regex_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+'
        rssi_regex_pattern = r'-?\d+dBm'  # get the rssi value from the probe request
        # need to remove SA: in the result to get the mac id from the matched string
        mac_id_regex_pattern = r'SA:(?:[0-9a-fA-F]:?){12}'
        # need to remove the "Probe Request" in the result to get the ssid , would be null in case of null probe request
        ssid_regex_pattern = r'Probe Request \(.*\)'

        native_sniffer_client = NativeSnifferClient(
            timestamp_regex_pattern, rssi_regex_pattern, mac_id_regex_pattern, ssid_regex_pattern, bugsnag)
        print("***** Starting the Sniff script *****")
        print("Putting the wifi on monitor mode")
        exit_code_from_command = native_sniffer_client.put_wifi_to_monitor_mode()

        # if something went wrong while putting the wifi on monitor mode exit
        if exit_code_from_command != 0:
            bugsnag.notify(
                "Something went wrong while putting the wifi on monitor mode!!!")
            print("Something went wrong while putting the wifi on monitor mode!!!")
            exit(1)

        # if everything was setup correctly start the sniff_probes function
        native_sniffer_client.start_sniff_probes(
            send_frame, build_frame_to_send)
    elif sniff_type == "ESP8266":
        from detectionModules.wifi.espSnifferClient import EspSnifferClient
        # get espConfigs
        serial_path = os.getenv("SERIAL_PATH")
        baud_rate = os.getenv("BAUD_RATE")
        esp_sniffer_client = EspSnifferClient(serial_path, baud_rate, bugsnag)
        esp_sniffer_client.initialize_serial()
        esp_sniffer_client.start_sniff(
            send_frame, build_frame_to_send)


def sigterm_handler(_signo, _stack_frame):
    # Used to gracefull kill the process and put the wlan back to managed mode only if sniffing using native wifi on the raspi board
    # Raises SystemExit(0):
    if sniff_type == "NATIVE":
        print("Removing wifi from monitor mode")
        exit_code_from_running_command = native_sniffer_client.put_wifi_to_managed_mode()
        if exit_code_from_running_command != 0:
            bugsnag.notify(
                "Something went wrong while putting the wifi to managed mode!!!")
            print("Something went wrong while putting the wifi to managed mode!!!")
            exit(1)
    # else graceful exit
    print("Gracefully exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)


### OLD CODE ###

# def process_output_line_native(output_line):
#     # TODO: Handle Else cases for this i.e throw error and report errors
#     timestamp_search = re.search(timestamp_regex_pattern, output_line)
#     if timestamp_search is not None:
#         timestamp = timestamp_search.group()
#     rssi_search = re.search(rssi_regex_pattern, output_line)
#     if rssi_search is not None:
#         rssi = rssi_search.group()
#     mac_id_search = re.search(mac_id_regex_pattern, output_line)
#     if mac_id_search is not None:
#         mac_id_with_sa = mac_id_search.group()
#         # extract the macid without the SA
#         mac_id = re.sub('SA:', '', mac_id_with_sa)
#     ssid_search = re.search(ssid_regex_pattern, output_line)
#     if ssid_search is not None:
#         ssid_with_probe = ssid_search.group()
#         # extract the ssid (if any)
#         ssid = re.sub(r'Probe Request \(|\)', '', ssid_with_probe)
#         if not ssid:  # i.e SSID is '' it is a null probe request
#             build_frame_to_send(timestamp, rssi, mac_id)
#         else:
#             build_frame_to_send(timestamp, rssi, mac_id, ssid)


# def process_output_line_esp(output_line):
#     # example output line -45,02:7a:f7:c7:1c:fa or -45,7,02:7a:f7:c7:1c:fa,SSID
#     timestamp = str(moment.utcnow())
#     split_values = output_line.split(",")
#     if len(split_values) == 2:
#         # this means it has no ssid
#         build_frame_to_send(timestamp, split_values[0], split_values[1])
#     elif len(split_values) == 3:
#         build_frame_to_send(
#             timestamp, split_values[0], split_values[1], split_values[2])
#     else:
#         # error
#         raise Exception("Unknown output from esp")
