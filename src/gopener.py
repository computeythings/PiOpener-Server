#!/usr/bin/python3

import RPi.GPIO as GPIO
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep
import ssl
import json
import logging

with open('config.json', 'r') as f:
    config = json.load(f)
    ACCESS_TOKEN = config['ACCESS_TOKEN']
    RELAY_PIN = config['RELAY_PIN']
    OPEN_PIN = config['OPEN_SWITCH_PIN']
    CLOSED_PIN = config['CLOSED_SWITCH_PIN']

# Setup GPIO pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(OPEN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CLOSED_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

IS_OPEN = GPIO.input(OPEN_PIN)
IS_CLOSED = GPIO.input(CLOSED_PIN)
OPENING = False
CLOSING = False


class OpenerServer(BaseHTTPRequestHandler):
    def _set_response(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        logging.info('GET request,\nPath: %s\nHeaders:\n%s\n', str(self.path),
                    str(self.headers))
        self._set_response(404)
        self.wfile.write('This link does not support that type of request.'
                        .encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Gets data size
        post_data = self.rfile.read(content_length) # Gets the data itself
        jdata = json.loads(post_data.decode('utf-8'))

        self._set_response(200)

        if self.path == '/api' or self.path == '/api/':
            if jdata['access_token'] == ACCESS_TOKEN:
                if jdata['intent'] == 'OPEN':
                    self.wfile.write('Opening garage'.encode('utf-8'))
                    self.open_garage()
                elif jdata['intent'] == 'CLOSE':
                    self.wfile.write('Closing garage'.encode('utf-8'))
                    self.close_garage()
                elif jdata['intent'] == 'TOGGLE':
                    self.wfile.write('Toggling garage'.encode('utf-8'))
                    self.toggle_garage()
                elif jdata['intent'] == 'QUERY':
                    if IS_OPEN:
                        self.wfile.write('OPEN')
                    elif IS_CLOSED:
                        self.wfile.write('CLOSED')
                    else
                        self.wfile.write('NEITHER')
                else:
                    self.wfile.write('Invalid Command'.encode('utf-8'))
            else:
                self.wfile.write('Invalid API Key'.encode('utf-8'))
        else:
            self.wfile.write('INVALID URL'.encode('utf-8'))

        jdata['access_token'] = '******'

        logging.info('POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n',
                    str(self.path), str(self.headers), jdata)

    # Quickly toggle a relay closed and open to simulate a button press
    def toggle_garage(self):
        GPIO.output(RELAY_PIN, GPIO.LOW)
        sleep(0.2)
        GPIO.output(RELAY_PIN, GPIO.HIGH)

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
        if IS_OPEN:
            return

        OPENING = True # set intent
        CLOSING = False
        self.toggle_garage()

    def close_garage(self):
        logging.info('Closing garage');
        if IS_CLOSED:
            return

        CLOSING = True # set intent
        OPENING = False
        self.toggle_garage();

    # This is run when the open switch is triggered
    def opened(channel):
        logging.info('Garage is now open')
        IS_OPEN = GPIO.input(OPEN_PIN)
        if IS_OPEN:
            OPENING = False
            if CLOSING: # toggle again if intent was to close
                self.close_garage()

    # This is run when the closed switch is triggered
    def closed(channel):
        logging.info('Garage is now closed')
        IS_CLOSED = GPIO.input(CLOSED_PIN)
        if IS_CLOSED
            CLOSING = False

            if OPENING: # toggle again if intent was to open
                self.open_garage()


def run(server_class=HTTPServer, handler_class=OpenerServer, port=4443,
        logf='/var/log/gopener.log'):
    GPIO.output(RELAY_PIN, GPIO.HIGH)
    GPIO.add_event_detect(OPEN_PIN, GPIO.BOTH, callback=handler_class.opened,
                            bouncetime=300)
    GPIO.add_event_detect(CLOSED_PIN, GPIO.BOTH, callback=handler_class.closed,
                            bouncetime=300)

    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)-8s: '
                        + '%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=logf)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./server.pem',
                                    server_side=True)
    logging.info('Starting httpd...\n')
    httpd.serve_forever()

    GPIO.cleanup()


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        run(port=int(argv[1]), logf=argv[2])
    else:
        run()
