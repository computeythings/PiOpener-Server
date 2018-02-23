#!/usr/bin/python3

import socket
import json
import ssl
import logging as Log
from socketserver import StreamRequestHandler, ThreadingTCPServer

with open('config.json', 'r') as f:
    config = json.load(f)
    ACCESS_TOKEN = config['ACCESS_TOKEN']

class PersistentStreamHandler(StreamRequestHandler):
    active = True # Initialized sockets will always be active

    def __init__(self, garage_controller, *args, **kwargs):
        self.garage_controller = garage_controller
        super(PersistentStreamHandler, self).__init__(*args, **kwargs)
    def setup(self):
        self.connection = self.request

        if self.timeout is not None:
            self.connection.settimeout(self.timeout)
        if self.disable_nagle_algorithm:
            self.connection.setsockopt(socket.IPPROTO_TCP,
                                       socket.TCP_NODELAY, True)
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)

        self.garage_controller.add_client(self)
        self.connection.sendall(str.encode('Connected.\n'))
        self.wfile.flush()

    """ Run on initialization to handle socket request """
    def handle(self):
        while not self.rfile.closed and self.active:
            try:
                self.data = bytes.decode(self.connection.recv(1024).strip())
                if self.data:
                    if self.data == 'KILL':
                        Log.info('TCPD: Client disconnect')
                        self.active = False
                    elif self.data == 'REFRESH':
                        Log.info('TCPD: Client refresh')
                        self.garage_controller.update_client()
                    elif self.data == 'OPEN_GARAGE':
                        Log.info('TCPD: Opening garage')
                        self.garage_controller.open_garage()
                    elif self.data == 'CLOSE_GARAGE':
                        Log.info('TCPD: Closing garage')
                        self.garage_controller.close_garage()
                    else:
                        Log.info('TCPD: Client sent: ' + self.data)
                else:
                    Log.info('TCPD: Client disconnect')
                    self.active = False
            except socket.timeout:
                Log.warning('TCPD: Socket timeout')
                break
            except socket.error:
                Log.warning('TCPD: Unexpected socket error')
                break

    """ Handles a dictionary input and sends data over the socket connection """
    def update(self, data):
        update_data = json.dumps(data)
        byte_data = str.encode(update_data + '\n')
        self.connection.sendall(byte_data)
        self.wfile.flush()

    """ Called after handle() """
    def finish(self):
        self.garage_controller.remove_client(self)
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
    allow_reuse_address = True # Prevents failure on module restart
    def __init__(self, garage_controller, *args, **kwargs):
        self.garage_controller = garage_controller
        super(TCPStreamingServer, self).__init__(*args, **kwargs)
    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(self.garage_controller, request, client_address, self)
    def __enter__(self):
        return self
    def __exit__(self, handler_class, port, logf):
        self.__shutdown_request = True

    def verify_request(self, request, client_address):
            data = bytes.decode(request.recv(1024).strip())
            if data == ACCESS_TOKEN:
                Log.info('TCPD: client accepted at address: ' + str(client_address))
                return True
            return False


def run(server_class=TCPStreamingServer, handler_class=PersistentStreamHandler,
            port=4444, logf='/var/log/gopener.log', garage_controller=None):

    Log.basicConfig(level=Log.INFO,
                        format='[%(asctime)s] %(levelname)-8s: '
                        + '%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=logf)

    server_address = ('', port)

    with server_class(garage_controller, server_address, handler_class) as tcpd:

        tcpd.socket = ssl.wrap_socket(tcpd.socket,
                                    certfile='/etc/ssl/certs/garageopener.pem',
                                    keyfile='/etc/ssl/private/garageopener.key',
                                    server_side=True)
        Log.info('TCPD: Starting tcpd...\n')
        try:
            tcpd.serve_forever()
        finally:
            tcpd.shutdown
