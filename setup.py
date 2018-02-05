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

while True:
    try:
        use_monitor = input('Would you like to enable the garage monitoring' +
                            'service to be used with the android app? [Y/N]')
                            .upper() == 'Y'
        break

print('Generating API key...')
for i in range(25):
   apikey = apikey + ALPHANUM[randint(0,len(ALPHANUM)-1)]

print('./src/Updating config.json')

with open('./src/config.json', 'r+') as f:
    data = json.load(f)
    data['ACCESS_TOKEN'] = apikey
    data['RELAY_PIN'] = relay_pin
    data['OPEN_SWITCH_PIN'] = open_pin
    data['CLOSED_SWITCH_PIN'] = close_pin
    f.seek(0)
    json.dump(data, f, indent=4)
    f.truncate()

print('Installing dependencies')
call(['apt', 'install', 'python3-rpi.gpio'])
print('Creating SSL cert')
call(['openssl', 'req', '-new', '-x509', '-keyout', 'garageopener.pem', '-out',
        'garageopener.pem', '-days', '36500', '-nodes']) # certs are good for 100 years
print('Creating crt and key files')
pem = open('garageopener.pem').read()
key, cert = pem.spit('-----END PRIVATE KEY-----\n')
keyfile = open('garageopener.key', 'w')
keyfile.write(key + '-----END PRIVATE KEY-----')
keyfile.close()
crtfile = open('garageopener.crt', 'w')
crtfile.write(cert)
crtfile.close()
call(['rm', 'garageopener.pem'])
print('Setting permissions')
call(['chmod', '600', 'src/config.json'])
call(['chmod', '600', 'garageopener.crt'])
call(['chmod', '600', 'garageopener.key'])
print('Moving keys')
call(['mv', 'garageopener.crt', '/etc/ssl/certs/garageopener.crt'])
call(['mv', 'garageopener.key', '/etc/ssl/private/garageopener.key'])
print('Migrating to /opt')
call(['cp', '-r', '.', '/opt/garage-opener'])
call(['chmod', '+x', '/opt/garage-opener/src/httpserver.py'])
call(['chmod', '+x', '/opt/garage-opener/src/sockserver.py'])
print('Creating systemd services')
call(['mv', './src/garageopener.service',
        '/lib/systemd/system/garageopener.service'])
call(['systemctl', 'daemon-reload'])
call(['systemctl', 'enable', 'garageopener.service'])
call(['systemctl', 'start', 'garageopener.service'])
if use_monitor:
    call(['mv', './src/garagemonitor.service',
    '/lib/systemd/system/garagemonitor.service'])
    call(['systemctl', 'enable', 'garagemonitor.service'])
    call(['systemctl', 'start', 'garagemonitor.service'])

print('Complete!')
print('\nYour API key is:\n\n{}'.format(apikey))
print('\nMake sure you write it down in a safe place\n')
