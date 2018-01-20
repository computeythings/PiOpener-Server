#!/usr/bin/python3

import RPi.GPIO as GPIO
from time import sleep
import logging

class Opener:
    def __init__(self, OPEN_PIN, CLOSED_PIN, RELAY_PIN):
        self.OPEN_PIN = OPEN_PIN
        self.CLOSED_PIN = CLOSED_PIN
        self.RELAY_PIN = RELAY_PIN

        # Setup GPIO pins
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.OPEN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.CLOSED_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.output(self.RELAY_PIN, GPIO.HIGH)
        GPIO.add_event_detect(self.OPEN_PIN, GPIO.BOTH,
                                callback=self.opened, bouncetime=300)
        GPIO.add_event_detect(self.CLOSED_PIN, GPIO.BOTH,
                                callback=self.closed, bouncetime=300)

        self.IS_OPEN = GPIO.input(self.OPEN_PIN)
        self.IS_CLOSED = GPIO.input(self.CLOSED_PIN)
        self.OPENING = False
        self.CLOSING = False

    def is_open(self):
        return self.IS_OPEN

    def is_closed(self):
        return self.IS_CLOSED

    # Quickly toggle a relay closed and open to simulate a button press
    def toggle_garage(self):
        GPIO.output(self.RELAY_PIN, GPIO.LOW)
        sleep(0.2)
        GPIO.output(self.RELAY_PIN, GPIO.HIGH)

    """
    Since there's no open/close wire to connect to, we can only toggle the door.
    A software check is run to determine whether or not we should toggle
    given each command.

    If the garage is in a middle state (i.e. not fully open OR closed) when the
    command is run, the door will be toggled once and then again if the desired
    state was not reached.
    """
    def open_garage(self):
        logging.info('Opening garage');
        if self.IS_OPEN:
            return

        self.OPENING = True # set intent
        self.CLOSING = False
        self.toggle_garage()

    def close_garage(self):
        logging.info('Closing garage');
        if self.IS_CLOSED:
            return

        self.CLOSING = True # set intent
        self.OPENING = False
        self.toggle_garage();

    # This is run when the open switch is triggered
    def opened(self, channel):
        logging.info('Garage is now open')
        self.IS_OPEN = GPIO.input(self.OPEN_PIN)
        if self.IS_OPEN:
            self.OPENING = False
            if self.CLOSING: # toggle again if intent was to close
                self.close_garage()

    # This is run when the closed switch is triggered
    def closed(self, channel):
        logging.info('Garage is now closed')
        self.IS_CLOSED = GPIO.input(self.CLOSED_PIN)
        if self.IS_CLOSED:
            self.CLOSING = False

            if self.OPENING: # toggle again if intent was to open
                self.open_garage()

    def __del__(self):
        # Clear pins on GC
        logging.debug('Cleaning up GPIO')
        GPIO.cleanup()
