#!/usr/bin/python3
import json
from os import getuid
from random import randint
from subprocess import call

if getuid() != 0:
    print('This script must be run as root.')
    quit()

ALPHANUM = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
apikey = ''

print('Using GPIO.BOARD layout');

while True:
    try:
        relay_pin = int(input('Which pin was connected to the relay? '))
        break
    except ValueError:
        print('Value must be an int.')
while True:
    try:
        open_pin = int(input('Which pin was connected to the OPEN switch? '))
        break
    except ValueError:
        print('Value must be an int.')
while True:
    try:
        close_pin = int(input('Which pin was connected to the CLOSE switch? '))
        break
    except ValueError:
        print('Value must be an int.')

print('Generating API key...')
for i in range(25):
   apikey = apikey + ALPHANUM[randint(0,61)] 

print('./src/Updating config.json')

with open('./src/config.json', 'r+') as f:
    data = json.load(f)
    data['APIKEY'] = apikey
    data['RELAY_PIN'] = relay_pin
    data['OPEN_SWITCH_PIN'] = open_pin
    data['CLOSED_SWITCH_PIN'] = close_pin
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()

print('Installing dependencies')
call(['apt', 'install', 'python3-rpi.gpio'])
print('Setting permissions')
call(['chmod', '600', './src/config.json']) # Don't want anyone seeing our API key
print('Creating SSL cert')
call(['openssl', 'req', '-new', '-x509', '-keyout', './src/server.pem', '-out', 
        './src/server.pem', '-days', '3650', '-nodes'])
print('Migrating to /opt')
call(['cp', '-r', '.', '/opt/garage-opener'])
call(['chmod', '+x', '/opt/garage-opener/src/gopener.py'])
print('Creating systemd service')
call(['mv', './src/garageopener.service', 
        '/lib/systemd/system/garageopener.service'])
call(['systemctl', 'daemon-reload'])
call(['systemctl', 'enable', 'garageopener.service'])
call(['systemctl', 'start', 'garageopener.service'])

print('Complete!')
print('\nYour API key is:\n\n{}'.format(apikey))
print('\nMake sure you write it down in a safe place\n')

