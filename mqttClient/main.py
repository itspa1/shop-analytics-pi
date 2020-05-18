import paho.mqtt.client as mqtt
from threading import Thread
import json


class MqttClient(Thread):
    def __init__(self, name, client_uid, topics, publish_topic, thread_q):
        Thread.__init__(self)
        Thread.daemon = True
        self.name = name
        self.connected = False
        self.cached_data_to_file = False
        self.topics = topics
        self.client_uid = client_uid
        self.publish_topic = publish_topic
        self.thread_q = thread_q
        self.cache_file_handler = open("cache_file", "a+")

    def run(self):
        self.client.loop_forever()

    def on_message_handler(self, client, user_data, msg):
        # print("new message", msg.payload)
        # set the data onto the shared queue for consumers to use it
        self.thread_q.put(msg.payload)

    def on_connect_handler(self, client, user_data, flags, return_code):
        if return_code == 0:
            print(self.name + " Connected with result code " + str(return_code))
            self.connected = True
            self.subscribe()
            if self.cached_data_to_file == True:
                self.__send_cached_frames()

    def on_subscribe_handler(self, client, obj, mid, granted_ops):
        print(self.name + " subscribed to topic", str(mid))

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

    # publisher
    def publish_data(self, json_in_str):
        if self.connected:
            # connected so send it over mqtt
            self.client.publish(self.publish_topic, json_in_str)
            print("Sent frame to server")
        else:
            # print(json_in_str)
            self.cached_data_to_file = True
            self.cache_file_handler.write(json_in_str + "\n")
            self.cache_file_handler.flush()
            print("Cached frame in file")

    def __send_cached_frames(self):
        print("Running internal function to send cache frames to server")
        # print(self.connected)
        if self.connected:
            lines_from_file = open("cache_file", "r").read()
            lines_from_file_split = lines_from_file.split("\n")
            # print(lines_from_file_split)
            # remove last empty string character '' from the split function
            lines_from_file_split.pop()
            lines_from_file_split = [json.loads(
                i) for i in lines_from_file_split]
            frame_array_to_send = {"cached_frames": lines_from_file_split}
            # connected send it over mqtt
            # print(json.dumps(frame_array_to_send))
            self.client.publish('cache_frame_topic',
                                json.dumps(frame_array_to_send))
            self.cached_data_to_file = False
            # reset the file/ truncate it
            self.cache_file_handler.seek(0, 0)
            self.cache_file_handler.truncate()
            print("sent cached frames to server")
        else:
            print("Still no internet, continuing caching of frames to file")
