from __future__ import print_function

import json
import sys

if sys.version_info[0] == 2:
    from urllib2 import Request, HTTPError, urlopen
else:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

from django.conf import settings

class PushyAPI:

    @staticmethod
    def sendPushNotification(data, to, options):
        # Insert your Pushy Secret API Key here
        apiKey = settings.PUSHY_KEY;

        # Default post data to provided options or empty object
        postData = options or {}

        # Set notification payload and recipients
        postData['to'] = to
        postData['data'] = data

        # Set URL to Send Notifications API endpoint
        req = Request('https://api.pushy.me/push?api_key=' + apiKey)

        # Set Content-Type header since we're sending JSON
        req.add_header('Content-Type', 'application/json')

        try:
           # Actually send the push
           response = urlopen(req, json.dumps(postData))
        except HTTPError as e:
           # Print response errors
           print("Pushy API returned HTTP error " + str(e.code) + ": " + e.read())
