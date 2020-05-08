import subprocess
from detectionModules.wifi.frame import Frame
import threading
import re


class NativeSnifferClient:
    def __init__(self, timestamp_regex_pattern, rssi_regex_pattern, mac_id_regex_pattern, ssid_regex_pattern, bugsnag):
        self.timestamp_regex_pattern = timestamp_regex_pattern
        self.rssi_regex_pattern = rssi_regex_pattern
        self.mac_id_regex_pattern = mac_id_regex_pattern
        self.ssid_regex_pattern = ssid_regex_pattern
        self.frame_to_send = Frame()
        self.bugsnag = bugsnag

    def put_wifi_to_managed_mode(self):
        command_execute_object = subprocess.run(
            ['sudo', 'airmon-ng', 'stop', 'wlan0mon'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return command_execute_object.returncode

    def put_wifi_to_monitor_mode(self):
        command_execute_object = subprocess.run(
            ['sudo', 'airmon-ng', 'start', 'wlxd03745465d3b'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return command_execute_object.returncode

    def process_output_line(self, output_line, build_frame_to_send):
        print(output_line)
        # TODO: Handle Else cases for this i.e throw error and report errors
        timestamp_search = re.search(self.timestamp_regex_pattern, output_line)
        if timestamp_search is not None:
            timestamp = timestamp_search.group()
        rssi_search = re.search(self.rssi_regex_pattern, output_line)
        if rssi_search is not None:
            rssi = rssi_search.group()
        mac_id_search = re.search(self.mac_id_regex_pattern, output_line)
        if mac_id_search is not None:
            mac_id_with_sa = mac_id_search.group()
            # extract the macid without the SA
            mac_id = re.sub('SA:', '', mac_id_with_sa)
        ssid_search = re.search(self.ssid_regex_pattern, output_line)
        if ssid_search is not None:
            ssid_with_probe = ssid_search.group()
            # extract the ssid (if any)
            ssid = re.sub(r'Probe Request \(|\)', '', ssid_with_probe)
            if not ssid:  # i.e SSID is '' it is a null probe request
                build_frame_to_send(self, timestamp, rssi, mac_id)
            else:
                build_frame_to_send(self, timestamp, rssi, mac_id, ssid)

    def read_output_from_process(self, proc, process_output_line=None, build_frame_to_send=None):
        for line in iter(proc.stdout.readline, b''):
            # print('got line: {0}'.format(line.decode('utf-8')), end='')
            if process_output_line is None:
                print(line.decode('utf-8'))
            else:
                process_output_line(line.decode('utf-8'), build_frame_to_send)

    def start_sniff_probes(self, send_frame, build_frame_to_send):
        # execute the sniff-probes.sh
        child_process_object = subprocess.Popen(['./sniff-probes.sh'],
                                                shell=True,
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT)
        send_frame(self)
        t = threading.Thread(target=self.read_output_from_process,
                             args=(child_process_object, self.process_output_line, build_frame_to_send), daemon=True)
        t.start()
        t.join()
