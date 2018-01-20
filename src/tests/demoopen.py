#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import RPi.GPIO as GPIO

sys.path.append(os.path.dirname(__file__) + '/..')
from gopener import Opener

# Read config file
with open('config.json', 'r') as f:
    config = json.load(f)
    RELAY_PIN = config['RELAY_PIN']
    OPEN_PIN = config['OPEN_SWITCH_PIN']
    CLOSED_PIN = config['CLOSED_SWITCH_PIN']

def run():
    opener = Opener(OPEN_PIN=OPEN_PIN, CLOSED_PIN=CLOSED_PIN, RELAY_PIN=RELAY_PIN)

    opener.open_garage()


if __name__ == '__main__':
    run()
