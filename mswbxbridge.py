"""
The configuration file would look like this:
{
    "authority": "https://login.microsoftonline.com/common",
    "client_id": "your_client_id",
    "scope": ["User.ReadBasic.All"],
    "endpoint": "https://graph.microsoft.com/v1.0/users"
}
    # You can find the other permission names from this document
    # https://docs.microsoft.com/en-us/graph/permissions-reference
    # To restrict who can login to this app, you can find more Microsoft Graph API endpoints from Graph Explorer
    # https://developer.microsoft.com/en-us/graph/graph-explorer
You can then run this sample with a JSON configuration file:

    python sample.py parameters.json
"""

import sys  # For simplicity, we'll read config file from 1st CLI param sys.argv[1]
import json
import logging
import os
import time
import RPi.GPIO as GPIO
import requests
import atexit, msal
from webexteamssdk import WebexTeamsAPI

# set up for RGB LEDs. Use GPIO pins referenced below when wiring:
GPIO.setmode(GPIO.BCM)
green=20
red=21
blue=22
GPIO.setwarnings(False)
GPIO.setup(red,GPIO.OUT)
GPIO.setup(green,GPIO.OUT)
GPIO.setup(blue,GPIO.OUT)
Freq=100 #for PWM control
RED=GPIO.PWM(red,Freq)
GREEN=GPIO.PWM(green,Freq)
BLUE=GPIO.PWM(blue,Freq)


# Optional logging
# logging.basicConfig(level=logging.DEBUG)

# Read config from command line

config = json.load(open(sys.argv[1]))


# Check token cache for MS Teams
cache = msal.SerializableTokenCache()
if os.path.exists("my_cache.bin"):
    cache.deserialize(open("my_cache.bin", "r").read())
atexit.register(lambda:
    open("my_cache.bin", "w").write(cache.serialize())
    # Hint: The following optional line persists only when state changed
    if cache.has_state_changed else None
    )

# Webex Configuration

api=WebexTeamsAPI(access_token=config["access_token"])
mywebexid=config["personId"]

api.people.get(personId=mywebexid).status

# Create a preferably long-lived app instance which maintains a token cache.
app = msal.PublicClientApplication(
    config["client_id"], authority=config["authority"],
     token_cache=cache  # Default cache is in memory only.
                       # You can learn how to use SerializableTokenCache from
                       # https://msal-python.rtfd.io/en/latest/#msal.SerializableTokenCache
    )

# The pattern to acquire a token looks like this.
result = None

# Note: If your device-flow app does not have any interactive ability, you can
#   completely skip the following cache part. But here we demonstrate it anyway.
# We now check the cache to see if we have some end users signed in before.
accounts = app.get_accounts()
if accounts:
    logging.info("Account(s) exists in cache, probably with token too. Let's try.")
    print("Pick the account you want to use to proceed:")
    for a in accounts:
        print(a["username"])
    # Assuming the end user chose this one
    chosen = accounts[0]
    # Now let's try to find a token in cache for this account
    result = app.acquire_token_silent(config["scope"], account=chosen)

if not result:
    logging.info("No suitable token exists in cache. Let's get a new one from AAD.")

    flow = app.initiate_device_flow(scopes=config["scope"])
    if "user_code" not in flow:
        raise ValueError(
            "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4))

    print(flow["message"])
    sys.stdout.flush()  # Some terminal needs this to ensure the message is shown

    # Ideally you should wait here, in order to save some unnecessary polling
    # input("Press Enter after signing in from another device to proceed, CTRL+C to abort.")

    result = app.acquire_token_by_device_flow(flow)  # By default it will block
        # You can follow this instruction to shorten the block time
        #    https://msal-python.readthedocs.io/en/latest/#msal.PublicClientApplication.acquire_token_by_device_flow
        # or you may even turn off the blocking behavior,
        # and then keep calling acquire_token_by_device_flow(flow) in your own customized loop.
try:

	while "access_token" in result:
    		# Calling graph using the access token
    		graph_data = requests.get(config["endpoint"], headers={'Authorization': 'Bearer ' + result['access_token']},).json()
    		status = graph_data.get('availability') 
		#print(status)
                if status == "Available":
                        GREEN.start(100)
                        RED.start(1)
                        BLUE.start(1)
                        time.sleep (10)
                elif status == "Busy":
                        GREEN.start(1)
                        RED.start(100)
                        BLUE.start(1)
                        time.sleep (10)
		elif status == "Away":
			GREEN.start(1)
                        RED.start(1)
                        BLUE.start(100)
                        time.sleep (10)
		elif status == "BeRightBack":
			GREEN.start(85)
                        RED.start(100)
                        BLUE.start(1)
                        time.sleep (10)
                else:
                        GREEN.start(1)
                        RED.start(100)
                        BLUE.start(1)
                        time.sleep (10)

except KeyboardInterrupt:
	RED.stop()
	GREEN.stop()
	BLUE.stop()	
	GPIO.cleanup()

