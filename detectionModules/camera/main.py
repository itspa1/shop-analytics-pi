import json
import os
import re
import threading
import time

import moment

# initialize the timer to keep the clock
TIMER = time.time()


class Camera():
    def __init__(self, device_mac_address, sub_module_type, configs, mqtt_client, bugsnag, thread_q):
        self.device_mac_address = device_mac_address
        self.sub_module_type = sub_module_type
        self.bugsnag = bugsnag
        self.mqtt_client = mqtt_client
        self.configs = configs
        self.debug = configs["DEBUG"]
        self.refresh_interval = configs["REFRESH_INTERVAL"]
        self.running_module = None
        self.thread_q = thread_q

    def start(self):
        self._initialize_camera_module()
        print("Stopping Camera")

    def start_send_frame(self, client):
        global TIMER
        if len(client.detections) != 0:
            print(max(client.detections))
            detections = max(client.detections)
            client.detections.clear()
            frame = {"deviceMacId": self.device_mac_address,
                     "detections": detections, "timestamp": str(moment.utcnow())}
            json_string = json.dumps(frame)
            self.mqtt_client.publish_data(json_string)
        TIMER = TIMER + self.refresh_interval
        timer_thread = threading.Timer(
            TIMER - time.time(), self.start_send_frame, [client])
        timer_thread.daemon = True
        timer_thread.start()

    def _initialize_camera_module(self):
        if self.sub_module_type == "yolo":
            from .yolo.yolo import YOLO
            self.running_module = YOLO(
                self.configs, self.debug, self.thread_q)
        elif self.sub_module_type == "tf":
            from .tf.tf import TF
            self.running_module = TF(
                self.configs, self.debug, self.thread_q)

        self.running_module.start(self.start_send_frame)
