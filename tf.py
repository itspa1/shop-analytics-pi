import sys
import signal
import json
from mqttClient import MqttClient

module_process = None


def notify_new_message(message):
    # print(message)
    new_env_value = json.loads(message)
    print(new_env_value)
    try:
        config_file = open('env.json', 'w')
        config_file.write(json.dumps(new_env_value))
        config_file.close()
    except IOError as error:
        print("An error occured while changing values in env file")
        print(error)

    try:
        # try to stop the thread with the existing configs
        stop_running_module_process()
        # restart the module again so that it picks up the new configs saved above
        start_modules()
    except Exception as error:
        print("something is wrong ", error)
        exit(1)


def start_mqtt():
    try:
        with open('env.json') as config_file:
            all_configs = json.load(config_file)
            main_env = all_configs["main"]
            mqtt_username = main_env["MQTT_USERNAME"]
            mqtt_password = main_env["MQTT_PASSWORD"]
            mqtt_host = main_env["MQTT_HOST"]
            mqtt_port = main_env["MQTT_PORT"]
            mqtt_topics = main_env["MQTT_TOPICS"]
            mqtt_client = MqttClient("pi_connect", "Random", [
                                    (i, 0) for i in mqtt_topics], notify_new_message)

    except IOError as error:
        # if not config file found exit
        print("ENV Json file not found, Exiting")
        print(error)
        exit(1)
    except:
        print("Error while loading config file from json")
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
    if module_to_use == "camera":
        camera_env = all_configs["camera"]
        if sub_module_to_use == "tf":
            from detectionModules.camera.tf.tf import TF
            module_process = TF(camera_env)
            module_process.start()
        else:
            print("No submodule with that name")


def sigterm_handler(_signo, _stack_frame):
    # Used to gracefull kill the process and put the wlan back to managed mode only if sniffing using native wifi on the raspi board
    # Raises SystemExit(0):
    global module_process
    print("Gracefully exiting")
    sys.exit(0)


# start initially the mqtt connection and the modules
start_mqtt()
start_modules()
