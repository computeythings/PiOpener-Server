#!/usr/bin/python3

import RPi.GPIO as GPIO
from time import sleep
import logging as Log

OPEN = 1
CLOSE = 2

class Opener:
    def __init__(self, OPEN_PIN, CLOSED_PIN, RELAY_PIN, socket_client=None):
        self.OPEN_PIN = OPEN_PIN
        self.CLOSED_PIN = CLOSED_PIN
        self.RELAY_PIN = RELAY_PIN

        # if defined should be used to send a client status data
        self.socket_client = socket_client

        # Setup GPIO pins
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.OPEN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.CLOSED_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.output(self.RELAY_PIN, GPIO.HIGH)
        GPIO.add_event_detect(self.OPEN_PIN, GPIO.BOTH,
                                callback=self.open_trigger, bouncetime=300)
        GPIO.add_event_detect(self.CLOSED_PIN, GPIO.BOTH,
                                callback=self.close_trigger, bouncetime=300)

        self.IS_FULLY_OPEN = not GPIO.input(self.OPEN_PIN)
        self.IS_FULLY_CLOSED = not GPIO.input(self.CLOSED_PIN)
        self.OPENING = False
        self.CLOSING = False
        self.WANT = 0 # Changed on user request

    def open_trigger(self, channel):
        sleep(0.01)
        if(GPIO.input(channel)):
            self.closing()
        else:
            self.opened()

    def close_trigger(self, channel):
        sleep(0.005)
        if(GPIO.input(channel)):
            self.opening()
        else:
            self.closed()

    def is_open(self):
        return self.IS_FULLY_OPEN

    def is_closed(self):
        return self.IS_FULLY_CLOSED

    """

    Since there's no open/close wire to connect to, we can only toggle the door.
    A software check is run to determine whether or not we should toggle
    given each command.

    If the garage is in a middle state (i.e. not fully open OR closed) when the
    command is run, the door will be toggled once and then again if the desired
    state was not reached.

    """

    """ Quickly toggle a relay closed and open to simulate a button press """
    def toggle(self):
        GPIO.output(self.RELAY_PIN, GPIO.LOW)
        sleep(0.2)
        GPIO.output(self.RELAY_PIN, GPIO.HIGH)

    def toggle_garage(self):
        if self.OPENING or self.IS_FULLY_OPEN:
            self.close_garage()
        elif self.CLOSING or self.IS_FULLY_CLOSED:
            self.open_garage()
        else:
            Log.info('Status unverifiable: toggling garage.')
            self.toggle()

    def open_garage(self):
        if not self.IS_FULLY_OPEN:
            Log.info('Opening garage')
            self.WANT = OPEN # set intent
            self.toggle()
            self.update_client()
        else:
            Log.info('Garage is already open.')

    def close_garage(self):
        if not self.IS_FULLY_CLOSED:
            Log.info('Closing garage')
            self.WANT = CLOSE # set intent
            self.toggle();
            self.update_client()
        else:
            Log.info('Garage is already closed.')

    """ This is run when the open switch is connected """
    def opened(self):
        self.IS_FULLY_OPEN = True
        Log.info('Garage is now open')
        self.OPENING = False
        if self.WANT == CLOSE: # toggle again if intent was to close
            self.close_garage()
        else:
            self.WANT = 0
        self.update_client()

    """ This is run when the open switch is disconnected """
    def closing(self):
        self.CLOSING = True
        self.IS_FULLY_OPEN = False
        Log.info('Garage is no longer open')
        self.update_client()


    """ This is run when the closed switch is connected """
    def closed(self):
        self.IS_FULLY_CLOSED = True
        Log.info('Garage is now closed')
        self.CLOSING = False
        if self.WANT == OPEN: # toggle again if intent was to open
            self.open_garage()
        else:
            self.WANT = 0
        self.update_client()

    """ This is run when the closed switch is disconnected """
    def opening(self):
        self.OPENING = True
        self.IS_FULLY_CLOSED = False;
        Log.info('Garage is no longer closed')
        self.update_client()

    """ Status info for every volatile variable """
    def status(self):
        data = {}
        data['OPEN'] = self.IS_FULLY_OPEN
        data['CLOSED'] = self.IS_FULLY_CLOSED
        data['OPENING'] = self.OPENING
        data['CLOSING'] = self.CLOSING
        return data

    """ This is run on any state change and will return data to a socket
    client that has implemented an update callback method. """
    def update_client(self):
        if self.socket_client:
            self.socket_client.update(self.status())

    """ Run on garbage collection """
    def __del__(self):
        # Clear pins
        Log.debug('Cleaning up GPIO')
        GPIO.cleanup()
