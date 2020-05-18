import zmq

# zmq class so that it can be used everywhere


class ZmqStream():
    def __init__(self, host):
        # set and maintain status
        self.status = "DISCONNECTED"
        self.host = host
        # set the port to 5556 statically, no reason to make it dynamic as of now
        self.port = "5556"
        self.zmq = None

    def connect_zmq(self):
        port = "5556"
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("tcp://*:%s" % port)
        self.zmq = socket
        self.status = "CONNECTED"
        print("CONNECTED ZMQ!")

    def disconnect_zmq(self):
        self.zmq.close()
        self.status = "DISCONNECTED"
