import serial
import threading
import moment
from frame import Frame


class EspSnifferClient:

    def __init__(self, serial_path, baud_rate):
        self.serial = None
        self.serial_path = serial_path
        self.baud_rate = baud_rate
        self.frame_to_send = Frame()

    def initialize_serial(self):
        self.serial = serial.Serial(self.serial_path, self.baud_rate)

    def start_reading_from_serial(self, process_output_line, build_frame_to_send):
        try:
            while 1:
                if(self.serial.in_waiting > 0):
                    line = self.serial.readline()
                    if process_output_line is None:
                        print(line.decode())
                    else:
                        # need not decode to 'utf-8' cause the esp writes to the serial in unicode and python already uses unicode natively
                        process_output_line(line.decode(), build_frame_to_send)
        except Exception as error:
            print("ERROR: " + str(error))

    def process_output_line(self, output_line, build_frame_to_send):
        # example output line -45,02:7a:f7:c7:1c:fa or -45,7,02:7a:f7:c7:1c:fa,SSID
        timestamp = str(moment.utcnow().date)
        split_values = output_line.split(",")
        if len(split_values) == 2:
            # this means it has no ssid
            build_frame_to_send(
                self, timestamp, split_values[0], split_values[1].strip())
        elif len(split_values) == 3:
            build_frame_to_send(
                self, timestamp, split_values[0], split_values[1].strip(), split_values[2])
        else:
            # error
            raise Exception("Unknown output from esp")

    def start_sniff(self, send_frame, build_frame_to_send):
        send_frame(self)
        t = threading.Thread(target=self.start_reading_from_serial,
                             args=([self.process_output_line, build_frame_to_send]), daemon=True)
        t.start()
        t.join()
