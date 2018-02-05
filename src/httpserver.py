#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import json
import logging
from gopener import Opener

# Read config file
with open('config.json', 'r') as f:
    config = json.load(f)
    ACCESS_TOKEN = config['ACCESS_TOKEN']
    RELAY_PIN = config['RELAY_PIN']
    OPEN_PIN = config['OPEN_SWITCH_PIN']
    CLOSED_PIN = config['CLOSED_SWITCH_PIN']
OPENER = Opener(OPEN_PIN=OPEN_PIN, CLOSED_PIN=CLOSED_PIN, RELAY_PIN=RELAY_PIN)

class OpenerServer(BaseHTTPRequestHandler):
    def _set_response(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        logging.info('GET request,\nPath: %s\nHeaders:\n%s\n', str(self.path),
                    str(self.headers))
        self._set_response(405)
        self.wfile.write('This link does not support that type of request.'
                        .encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # Gets data size
        post_data = self.rfile.read(content_length) # Gets the data itself
        jdata = json.loads(post_data.decode('utf-8'))

        if self.path == '/api' or self.path == '/api/':
            if jdata['access_token'] == ACCESS_TOKEN:
                self._set_response(200)
                if jdata['intent'] == 'OPEN':
                    self.wfile.write('Opening garage'.encode('utf-8'))
                    OPENER.open_garage()
                elif jdata['intent'] == 'CLOSE':
                    self.wfile.write('Closing garage'.encode('utf-8'))
                    OPENER.close_garage()
                elif jdata['intent'] == 'TOGGLE':
                    self.wfile.write('Toggling garage'.encode('utf-8'))
                    OPENER.toggle_garage()
                elif jdata['intent'] == 'QUERY':
                    if OPENER.is_open():
                        self.wfile.write('OPEN'.encode('utf-8'))
                    elif OPENER.is_closed():
                        self.wfile.write('CLOSED'.encode('utf-8'))
                    else:
                        self.wfile.write('NEITHER'.encode('utf-8'))
                else:
                    self._set_response(404)
                    self.wfile.write('Invalid Command'.encode('utf-8'))
            else:
                self._set_response(401)
                self.wfile.write('Invalid API Key'.encode('utf-8'))
        else:
            self._set_response(404)
            self.wfile.write('INVALID URL'.encode('utf-8'))

        jdata['access_token'] = '******'

        logging.info('POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n',
                    str(self.path), str(self.headers), jdata['intent'])

def run(server_class=HTTPServer, handler_class=OpenerServer, port=4443,
        logf='/var/log/gopener.log'):

    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)-8s: '
                        + 'HTTPD: %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=logf)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.socket = ssl.wrap_socket(httpd.socket,
                                    certfile='/etc/ssl/certs/garageopener.crt',
                                    keyfile='/etc/ssl/private/garageopener.key'
                                    server_side=True)
    logging.info('Starting httpd...\n')
    httpd.serve_forever()


if __name__ == '__main__':
    from sys import argv

    # Take CLI arguments as port and log location respectively
    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        run(port=int(argv[1]), logf=argv[2])
    else:
        run()
