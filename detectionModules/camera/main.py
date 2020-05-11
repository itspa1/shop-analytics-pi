import json
import os
import re
import threading
import time

import moment

# initialize the timer to keep the clock
TIMER = time.time()


class Camera():
    def __init__(self, sub_module_type, configs, mqtt_client, bugsnag):
        self.sub_module_type = sub_module_type
        self.bugsnag = bugsnag
        self.mqtt_client = mqtt_client
        self.configs = configs
        self.refresh_interval = configs["REFRESH_INTERVAL"]

    def start(self):
        self._initialize_camera_module()
        print("Stopping Camera")

    def start_send_frame(self, client):
        global TIMER
        print(client.detections)
        client.detections.clear()
        TIMER = TIMER + self.refresh_interval
        timer_thread = threading.Timer(
            TIMER - time.time(), self.start_send_frame, [client])
        timer_thread.daemon = True
        timer_thread.start()

    def _initialize_camera_module(self):
        if self.sub_module_type == "yolo":
            from .yolo.yolo import YOLO
            running_module = YOLO(self.configs)
        elif self.sub_module_type == "tf":
            from .tf.tf import TF
            running_module = TF(self.configs)

        running_module.start(self.start_send_frame)
