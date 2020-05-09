# Shop-Analytics-Pi

### This can run multiple types of collection of people data

- By MAC address identification i.e Capturing probe-requests nearby
- By Camera using people detection

### How Each of them works

- Capturing probe-requests
  - This is done by either putting the wifi-card of the device on monitor mode and running a `tcpdump` with appropriate flags.
  - If the native wifi-card does not support monitor-mode, you could plug an esp8266 microcontroller to run as a wifi-sniffer.
- People Detection
  - Several models can be run using the `tf` module present in this, you just need to swap out the appropriate tensorflow models by downloading from their Github repo.
  - YOLO is also supported to run on this by using the native CV2 library.

### Steps to Run this on a raspberry pi

- Ensure the pi's wifi card supports monitor mode (if using Native Sniffer module)
- Clone this repo onto the raspberry pi
- ### add gitignored files

  - env.json

  ```
  {
  "main": {
    "MQTT_USERNAME": "peekay",
    "MQTT_PASSWORD": "peekay",
    "MQTT_HOST": "localhost",
    "MQTT_PORT": 1883,
    "MQTT_TOPICS": ["remote_access"],
    "BUGSNAG_KEY": "abc"
  },
  "MODULE": "camera",
  "SUBMODULE": "yolo",
  "camera": {
    "MODEL_PATH": "./models/yolov3-tiny",
    "NMS_SUPPRESSION_PROBABILITY": 0.1,
    "MINIMUM_THRESHOLD": 0.6,
    "VIDEO_SOURCE": 0,
    "WIDTH": 416,
    "HEIGHT": 416,
    "THRESHOLD": 0.7
  },
  "wifi": {
    "REFRESH_INTERVAL": 5,
    "SERIAL_PATH": "/dev/ttyUSB0",
    "BAUD_RATE": 115200
  }
  }

  ```

- run `pip3 install -r requirements.txt` to install all the required modules for this repo
- P.S requirements.txt were generated using pipreqs, check the requirements once to ensure everything is setup properly
- while deploying add this to the crontab of the raspberry pi `@reboot sleep 10 && /bin/bash /home/pi/pi-sniffer/startup.sh`
