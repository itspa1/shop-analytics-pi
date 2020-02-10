#!/bin/bash
cd /
cd home/pi/pi-sniffer
python3 -u < /dev/null main.py > log 2>&1
