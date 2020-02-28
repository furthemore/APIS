import json
import logging
import urllib2

from django.conf import settings

logger = logging.getLogger(__name__)


class PushyAPI:
    @staticmethod
    def sendPushNotification(data, to, options):
        # Insert your Pushy Secret API Key here
        apiKey = settings.CLOUD_MESSAGING_KEY

        # Default post data to provided options or empty object
        postData = options or {}

        # Set notification payload and recipients
        postData["to"] = to
        postData["data"] = data

        # Set URL to Send Notifications API endpoint
        req = urllib2.Request("https://api.pushy.me/push?api_key=" + apiKey)

        # Set Content-Type header since we're sending JSON
        req.add_header("Content-Type", "application/json")

        try:
            # Actually send the push
            response = urllib2.urlopen(req, json.dumps(postData))
        except urllib2.HTTPError as e:
            # Print response errors
            error_message = (
                "Pushy API returned HTTP error " + str(e.code) + ": " + e.read()
            )
            logger.error(error_message)
            raise PushyError(error_message)


class PushyError(Exception):
    pass
