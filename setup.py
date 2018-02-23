#!/usr/bin/python3
import json
from os import getuid, path
from random import randint
from subprocess import call

if getuid() != 0:
    print('This script must be run as root.')
    quit()

ALPHANUM = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
apikey = ''

print('./src/Updating config.json')

with open('./src/config.json', 'r+') as f:
    data = json.load(f)

    # Option to update pin layout
    if not data['RELAY_PIN'] == 0:
        answer = input('Update the relay pin value? (Y/N)')
        if answer.upper() == 'Y':
            data['RELAY_PIN'] = 0
    if not data['OPEN_SWITCH_PIN'] == 0:
        answer = input('Update the open pin value? (Y/N)')
        if answer.upper() == 'Y':
            data['OPEN_SWITCH_PIN'] = 0
    if not data['CLOSED_SWITCH_PIN'] == 0:
        answer = input('Update the close pin value? (Y/N)')
        if answer.upper() == 'Y':
            data['CLOSED_SWITCH_PIN'] = 0

    print('Using GPIO.BOARD layout');

    while data['RELAY_PIN'] == 0:
        try:
            data['RELAY_PIN'] = int(
                        input('Which pin was connected to the relay? '))
        except ValueError:
            print('Value must be an int.')
    while data['OPEN_SWITCH_PIN'] == 0:
        try:
            data['OPEN_SWITCH_PIN'] = int(
                        input('Which pin was connected to the OPEN switch? '))
        except ValueError:
            print('Value must be an int.')
    while data['CLOSED_SWITCH_PIN'] == 0:
        try:
            data['CLOSED_SWITCH_PIN'] = int(
                        input('Which pin was connected to the CLOSE switch? '))
        except ValueError:
            print('Value must be an int.')

    # Only update API key if it does not already exist
    if data['ACCESS_TOKEN'] == '':
        print('Generating API key...')
        for i in range(25):
           apikey = apikey + ALPHANUM[randint(0,len(ALPHANUM)-1)]
        data['ACCESS_TOKEN'] = apikey
    else:
        apikey = data['ACCESS_TOKEN']


    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()

print('Installing dependencies')
call(['apt-get', 'update'])
call(['apt-get', 'install', 'python3-rpi.gpio'])

# only create new certs if they don't already exist
if (
        not (path.isfile('/etc/ssl/private/garageopener.key')
        or path.isfile('/etc/ssl/certs/garageopener.pem') )
    ):
    print('Creating SSL cert')
    # certs are good for 100 years
    call(['openssl', 'req', '-new', '-x509', '-keyout', 'garageopener.key',
            '-out', 'garageopener.pem', '-days', '36500', '-nodes'])
    print('Setting permissions')
    call(['chmod', '600', 'src/config.json'])
    call(['chmod', '600', 'garageopener.pem'])
    call(['chmod', '600', 'garageopener.key'])
    print('Moving keys')
    call(['mv', 'garageopener.pem', '/etc/ssl/certs/garageopener.pem'])
    call(['mv', 'garageopener.key', '/etc/ssl/private/garageopener.key'])


print('Migrating to /opt')
call(['cp', '-r', '.', '/opt/garage-opener'])
call(['chmod', '+x', '/opt/garage-opener/src/main.py'])

# only create systemd service if it doesn't already exist
if not path.isfile('/lib/systemd/system/garageopener.service'):
    print('Creating systemd services')
    call(['mv', './src/garageopener.service',
            '/lib/systemd/system/garageopener.service'])
    call(['systemctl', 'daemon-reload'])
    call(['systemctl', 'enable', 'garageopener.service'])
    call(['systemctl', 'start', 'garageopener.service'])
else:
    call(['systemctl', 'restart', 'garageopener.service'])

print('Complete!')
print('\nYour API key is:\n\n{}'.format(apikey))
print('\nMake sure you write it down in a safe place\n')
