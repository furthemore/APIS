import json
import logging
import re
from decimal import Decimal

from django.conf import settings
from paho.mqtt import publish as mqtt

FORMAT_TOPIC_SYS_RE = re.compile(r'^\$')
FORMAT_TOPIC_WILDCARD_RE = re.compile(r'[\#\+ ]')

logger = logging.getLogger(__name__)

class JSONDecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o.quantize(Decimal("1.00")))
        return o

def format_topic(topic):
    """
    Removes characters that shouldn't be in an MQTT topic, namely:

    - Can't start with $
    - Can't contain # or + (wildcards)
    - All-lowercase, remove spaces
    """

    topic = FORMAT_TOPIC_SYS_RE.sub('', topic)
    topic = FORMAT_TOPIC_WILDCARD_RE.sub('', topic)
    return topic

def send_mqtt_message(topic, payload):
    # FIXME: Need to do some validation/munging on topic so we don't use any characters not allowed
    # e.g. '#' and '+', ^$
    payload_json = json.dumps(payload, cls=JSONDecimalEncoder)
    logger.info("Sending MQTT message ({0})".format(payload_json))
    mqtt.single(topic, payload_json, retain=False, hostname=settings.MQTT_BROKER["host"],
                port=settings.MQTT_BROKER["port"], auth=settings.MQTT_LOGIN)