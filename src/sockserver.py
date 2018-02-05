#!/usr/bin/python3

import socket
import json
import ssl
import logging as Log
from socketserver import StreamRequestHandler, ThreadingTCPServer
from gopener import Opener

with open('config.json', 'r') as f:
    config = json.load(f)
    ACCESS_TOKEN = config['ACCESS_TOKEN']
    RELAY_PIN = config['RELAY_PIN']
    OPEN_PIN = config['OPEN_SWITCH_PIN']
    CLOSED_PIN = config['CLOSED_SWITCH_PIN']
OPENER = Opener(OPEN_PIN=OPEN_PIN, CLOSED_PIN=CLOSED_PIN, RELAY_PIN=RELAY_PIN)

class PersistentStreamHandler(StreamRequestHandler):
    timeout = 600
    active = True # Initialized sockets will always be active

    def setup(self):
        self.connection = self.request

        if self.timeout is not None:
            self.connection.settimeout(self.timeout)
        if self.disable_nagle_algorithm:
            self.connection.setsockopt(socket.IPPROTO_TCP,
                                       socket.TCP_NODELAY, True)
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)

        OPENER.socket_client = self
        self.connection.sendall(str.encode('Connected.'))

    """ Run on initialization to handle socket request """
    def handle(self):
        while not self.rfile.closed and self.active:
            try:
                self.data = bytes.decode(self.connection.recv(1024).strip())
                if self.data:
                    if self.data == 'CLOSE':
                        Log.info('Client disconnect')
                        self.active = False
                    elif self.data == 'REFRESH':
                        Log.info('Client refresh')
                        OPENER.update_client()
                else:
                    Log.info('Client disconnect')
                    self.active = False
            except socket.timeout:
                Log.warning('Socket timeout')
                break
            except socket.error:
                Log.warning('Unexpected socket error')
                break

    """ Handles a dictionary input and sends data over the socket connection """
    def update(self, data):
        update_data = json.dumps(data)
        byte_data = str.encode(update_data)
        self.connection.sendall(byte_data)

    """ Called after handle() """
    def finish(self):
        OPENER.socket_client = None
        if not self.wfile.closed:
            try:
                self.wfile.flush()
            except socket.error:
                # A final socket error may have occurred here, such as
                # the local error ECONNABORTED.
                pass
        self.wfile.close()
        self.rfile.close()

class TCPStreamingServer(ThreadingTCPServer):
    def __init__(self, *args, **kwargs):
        super(TCPStreamingServer, self).__init__(*args, **kwargs)
        self.validated_clients = []

    def __enter__(self):
        return self
    def __exit__(self, handler_class, port, logf):
        self.__shutdown_request = True

    def verify_request(self, request, client_address):
            data = bytes.decode(request.recv(1024).strip())
            if data == ACCESS_TOKEN:
                Log.info('client accepted at address: ' + str(client_address))
                return True
            return False


def run(server_class=TCPStreamingServer, handler_class=PersistentStreamHandler,
            port=4444, logf='/var/log/gopener.log'):

    Log.basicConfig(level=Log.INFO,
                        format='[%(asctime)s] %(levelname)-8s: '
                        + 'TCPD: %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=logf)

    server_address = ('', port)

    with server_class(server_address, handler_class) as tcpd:
        tcpd.socket = ssl.wrap_socket(tcpd.socket,
                                    certfile='/etc/ssl/certs/garageopener.crt',
                                    keyfile='/etc/ssl/private/garageopener.key',
                                    server_side=True)
        Log.info('Starting tcpd...\n')
        try:
            tcpd.serve_forever()
        finally:
            tcpd.shutdown

if __name__ == '__main__':
    from sys import argv

    # Take CLI arguments as port and log location respectively
    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        run(port=int(argv[1]), logf=argv[2])
    else:
        run()
