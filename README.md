# RPi Garage Opener
A server script to handle requests to control and monitor garage door state.

## Requirements
This script requires a Raspberry Pi with SSH enabled as well as an available 3 GPIO pins.

Other than that you'll just need a 5V relay with a low level amp allowing it to be controlled by the 3.3V GPIO pins.

## Wiring
The default layout is GPIO.BOARD for simplicity's sake

![here](https://www.jameco.com/Jameco/workshop/circuitnotes/raspberry_pi_circuit_note_fig2a.jpg)

GPIO.BOARD uses the actual physical pin's number and should be the same numbering scheme on any board.

You should be connecting your relay to a 5V and Ground pin on the pi for power as well a GPIO pin. This is your RELAY_PIN.

Your garage door should also have two switches on the rails. One next to the opener and one on the further end by the actual opening of the garage. Run a wire to each of these wiring them to separate GPIO pins. The closer switch will be your OPEN switch while the further your CLOSE switch.

Once you've connected those, connect the relay to the two terminals that your physical wall switch is connected to. When the script is told to toggle the door it will quickly close and open the switch simulating a button press. Find a good place to mount your pi and then plug it in.

## Installation
To install, simply clone the directory, and run the setup script as root:

    $ git clone https://github.com/computeythings/PiOpener-Server.git
    $ cd PiOpener-Server
    $ sudo python3 ./setup.py

You should then be prompted to enter the pin to which the relay is connected as well as the input pins which the open/closed switches are connected.

Following this you will be prompted to fill out info for your SSL cert.

**Important:** If you plan on using the Android app and wish to control your garage opener from outside of your home network, you must fill out the Common Name with your serves **external** IP address when prompted during creation of the SSL cert. It's highly recommended you use a dynamic DNS name. This is important when performing hostname verification and will cause the app to refuse the connection externally if it is not setup properly. The rest of the information can be filled out with whatever you'd like as it probably won't ever be relevant again.

Once you've finished this, the script should migrate all files to `/opt` and setup, enable, and start a systemd service called garageopener.service. To check if this has worked, run `systemctl status garageopener.service` on the pi. You should get some info on the service including some green text saying "active (running)".

That's it! Your garage opener is now up and running and ready to receive some commands.

## REST API
To control your garage door from other devices you must `POST` requests to `https://<raspberrypi.ip>/api/` and include the API key in the POST data as "access_token" as well as either `OPEN`, `CLOSE`, `TOGGLE`, or `QUERY` as your "intent".

An example would be a file payload.json

    {
      "access_token": "<your-key-here>",
      "intent": "OPEN"
    }

Followed by this command: `curl -kd @payload.json https://<raspberrypi.ip>:4443/api/`

This should be followed by a response of "Opening garage" and the actual opening of your garage if it is closed or nothing if it is already open.

The `TOGGLE` intent will trigger the garage door regardless of its current position.

`QUERY` is the only intent that will not trigger an action. It simply responds with `OPEN`, `CLOSED`, or `NEITHER` if it is somewhere in between. This is useful, for example, if all you want is to make sure your garage is closed after you leave.

## TCP server
The TCP server opens a port on the server to accept a socket connection which will allow you to monitor and get real-time updates of the garage door status. This is intended to be used with the [PiOpener-Android app](https://github.com/computeythings/PiOpener-Android).
