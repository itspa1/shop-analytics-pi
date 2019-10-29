import paho.mqtt.client as mqtt
from threading import Thread
import json

class MqttClient(Thread):
    def __init__(self, name, client_uid, topics):
        Thread.__init__(self)
        self.name = name
        self.connected = False
        self.topics = topics
        self.client_uid = client_uid

    def run(self):
        self.client.loop_forever()

    def on_message_handler(self, client, user_data, msg):
        print("new message " + msg)

    def on_connect_handler(self, client, user_data, flags, return_code):
        if return_code == 0:
            print(self.name + " Connected with result code " + str(return_code))
            self.connected = True
            #self.subscribe()

    def on_subscribe_handler(self, client, obj, mid, granted_ops):
        print(self.name + " subscribed to topic")

    def on_publish_handler(self, client, userdata, result):
        print("data published\n")

    def on_disconnect_handler(self, client, userdata, rc):
        self.connected = False
        print(self.name + " disconnected from broker")

    def create_client(self):
        self.client = mqtt.Client(
            client_id=self.name, clean_session=True)

    def subscribe(self):
        self.client.subscribe(self.topics)
