import sys
import signal
import json
from mqttClient import MqttClient
import threading
from getmac import get_mac_address
from queue import Queue

import bugsnag

module_process = None
mqtt_client = None
# get mac address to be sent with every ping
device_mac_address = "".join(get_mac_address().upper().split(":"))

# create a shared queue that gets synced across threads
shared_queue = Queue()


def start_mqtt():
    global mqtt_client
    try:
        with open('env.json') as config_file:
            all_configs = json.load(config_file)
            main_env = all_configs["main"]
            bugsnag.configure(api_key=main_env["BUGSNAG_KEY"])
            mqtt_username = main_env["MQTT_USERNAME"]
            mqtt_password = main_env["MQTT_PASSWORD"]
            mqtt_host = main_env["MQTT_HOST"]
            mqtt_port = main_env["MQTT_PORT"]
            mqtt_topics = main_env["MQTT_TOPICS"]
            mqtt_publish_topic = main_env["PUBLISH_TOPIC"]
            # module_to_use = all_configs["MODULE"]
            mqtt_client = MqttClient("pi_connect", "Random", [
                (i, 0) for i in mqtt_topics], mqtt_publish_topic, shared_queue)

    except IOError as error:
        # if not config file found exit
        print("ENV Json file not found, Exiting")
        print(error)
        exit(1)
    except Exception as e:
        print("Error while loading config file from json")
        print(e)
        exit(1)

    # print(main_env)

    mqtt_client.create_client()
    mqtt_client.client.username_pw_set(mqtt_username, mqtt_password)
    mqtt_client.client.on_connect = mqtt_client.on_connect_handler
    mqtt_client.client.on_disconnect = mqtt_client.on_disconnect_handler
    mqtt_client.client.on_subscribe = mqtt_client.on_subscribe_handler
    mqtt_client.client.on_message = mqtt_client.on_message_handler
    mqtt_client.client.connect(mqtt_host, mqtt_port, keepalive=60)
    mqtt_client.start()


def start_modules():
    try:
        with open('env.json') as config_file:
            all_configs = json.load(config_file)
    except IOError as error:
        # if not config file found exit
        print("ENV Json file not found, Exiting")
        print(error)
        exit(1)
    except:
        print("Error while loading config file from json")
        exit(1)

    module_to_use = all_configs["MODULE"]
    sub_module_to_use = all_configs["SUBMODULE"]
    global module_process
    global mqtt_client
    if module_to_use == "camera":
        camera_env = all_configs["camera"]
        if sub_module_to_use == "yolo" or sub_module_to_use == "tf":
            from detectionModules.camera import Camera
            module_process = Camera(
                device_mac_address, sub_module_to_use, camera_env, mqtt_client, bugsnag, shared_queue)
            module_process.start()
        # elif sub_module_to_use == "tf":
        #     from detectionModules.camera.tf.tf import TF
        #     module_process = TF(camera_env)
        #     module_process.start()
        else:
            print("No submodule for camera with that name")
    elif module_to_use == "wifi":
        wifi_env = all_configs["wifi"]
        if sub_module_to_use == "native" or sub_module_to_use == "esp8266":
            from detectionModules.wifi import WiFi
            module_process = WiFi(
                device_mac_address=device_mac_address, sniff_type=sub_module_to_use, configs=wifi_env, mqtt_client=mqtt_client, bugsnag=bugsnag)
            module_process.start()
        else:
            print("No Submodule for wifi with that name")
    else:
        print("NO MODULE WITH THAT NAME")
        exit(1)


def sigterm_handler(_signo, _stack_frame):
    # Used to gracefull kill the process and put the wlan back to managed mode only if sniffing using native wifi on the raspi board
    # Raises SystemExit(0):
    print("Gracefully exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)


# start initially the mqtt connection and the modules
start_mqtt()
start_modules()
