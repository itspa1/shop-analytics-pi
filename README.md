# PI-SNIFFER

### Steps to Run this on a raspberry pi

- Ensure the pi's wifi card supports monitor mode
- Clone this repo onto the raspberry pi
- ### add gitignored files
  - .env
  ```
  REFRESH_INTERVAL=5
  MQTT_USERNAME=peekay
  MQTT_PASSWORD=peekay
  MQTT_HOST=localhost
  MQTT_PORT=1883
  SNIFF_TYPE=TYPE
  SERIAL_PATH=PATH FOR SERIAL(if esp8266)
  BAUD_RATE=baud rate (if esp8266)
  BUGSNAG_KEY=bugsnag_key
  ```
- run `pip3 install -r requirements.txt` to install all the required modules for this repo
- P.S requirements.txt were generated using pipreqs, check the requirements once to ensure everything is setup properly
- while deploying add this to the crontab of the raspberry pi `@reboot sleep 10 && /bin/bash /home/pi/pi-sniffer/startup.sh`
