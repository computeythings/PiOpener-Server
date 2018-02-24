#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl
import json
import logging as Log

with open('config.json', 'r') as f:
    config = json.load(f)
    ACCESS_TOKEN = config['ACCESS_TOKEN']

class OpenerServer(BaseHTTPRequestHandler):
    def __init__(self, garage_controller, *args, **kwargs):
        self.garage_controller = garage_controller
        super(OpenerServer, self).__init__(*args, **kwargs)
    def _set_response(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        Log.info('HTTPD: GET request,\nPath: %s\nHeaders:\n%s\n', str(self.path),
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
                    self.garage_controller.open_garage()
                elif jdata['intent'] == 'CLOSE':
                    self.wfile.write('Closing garage'.encode('utf-8'))
                    self.garage_controller.close_garage()
                elif jdata['intent'] == 'TOGGLE':
                    self.wfile.write('Toggling garage'.encode('utf-8'))
                    self.garage_controller.toggle_garage()
                elif jdata['intent'] == 'QUERY':
                    if self.garage_controller.is_open():
                        self.wfile.write('OPEN'.encode('utf-8'))
                    elif self.garage_controller.is_closed():
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

        Log.info('HTTPD: POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n',
                    str(self.path), str(self.headers), jdata['intent'])

class HTTPControlServer(HTTPServer):
    def __init__(self, garage_controller, *args, **kwargs):
        self.garage_controller = garage_controller
        super(HTTPControlServer, self).__init__(*args, **kwargs)
    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(self.garage_controller, request, client_address, self)
    def __enter__(self):
        return self
    def __exit__(self, handler_class, port, logf):
        self.__shutdown_request = True

def run(server_class=HTTPControlServer, handler_class=OpenerServer, port=4443,
        logf='/var/log/gopener.log', garage_controller=None,
        cert='/etc/ssl/certs/garageopener.pem', 
        key='/etc/ssl/private/garageopener.key'):

    Log.basicConfig(level=Log.INFO,
                        format='[%(asctime)s] %(levelname)-8s: '
                        + '%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=logf)

    server_address = ('', port)
    with server_class(garage_controller, server_address, handler_class) as httpd:
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile=cert, keyfile=key,
                                        server_side=True)
        Log.info('HTTPD: Starting httpd...\n')
        try:
            httpd.serve_forever()
        finally:
            httpd.shutdown()
