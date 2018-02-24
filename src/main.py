#!/usr/bin/python3

import httpserver
import sockserver
import json
from sys import argv
from gopener import Opener
from threading import Thread
from optparse import OptionParser,OptionGroup

with open('config.json', 'r') as f:
    config = json.load(f)
    ACCESS_TOKEN = config['ACCESS_TOKEN']
    RELAY_PIN = config['RELAY_PIN']
    OPEN_PIN = config['OPEN_SWITCH_PIN']
    CLOSED_PIN = config['CLOSED_SWITCH_PIN']
OPENER = Opener(OPEN_PIN=OPEN_PIN, CLOSED_PIN=CLOSED_PIN, RELAY_PIN=RELAY_PIN)

def parse_args():
    parser = OptionParser()
    parser.description = 'Server application for garage door control.'
    parser.add_option('', '--http-only', action='store_true', default=False,
            dest='http_only', help='Only start the HTTP server.')
    parser.add_option('', '--tcp-only', action='store_true', default=False,
            dest='tcp_only', help='Only start the TCP server.')
    parser.add_option('-T', '--tcp-port', default=4444, dest='tcp_port',
            metavar='port', help='Set the TCP server port')
    parser.add_option('-H', '--http-port', default=4443, dest='http_port',
            metavar='port', help='Set the HTTP server port')
    parser.add_option('-l', '--logfile', default='/var/log/gopener.log',
            metavar='file', dest='log', help='Set the log file location.')
    parser.add_option('-c', '--cert', default='/etc/ssl/certs/garageopener.pem',
            metavar='file', dest='log',
            help='Specify the SSL certificate location.')
    parser.add_option('-k', '--key', default='/etc/ssl/private/garageopener.key',
            metavar='file', dest='log',
            help='Specify the SSL private key location.')
    parser.usage = 'Usage: %prog [options]'
    (options, args) = parser.parse_args()

    return (options, args)

def run():
    (options, args) = parse_args()

    if not options.tcp_only:
        Thread(target=httpserver.run, kwargs={'port': options.http_port,
                    'logf': options.log, 'garage_controller': OPENER}).start()
    if options.http_only:
        return
    Thread(target=sockserver.run, kwargs={'port': options.tcp_port,
                'logf': options.log, 'garage_controller': OPENER}).start()
if __name__ == '__main__':
    run()
