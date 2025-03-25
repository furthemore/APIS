import base64
import json
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal

import jwt
from django.conf import settings
from paho.mqtt import publish as mqtt

FORMAT_TOPIC_SYS_RE = re.compile(r"^\$")
FORMAT_TOPIC_WILDCARD_RE = re.compile(r"[\#\+ /]")

logger = logging.getLogger(__name__)

BASE_TOPIC = "apis"
TOPICS = [
    "receipts",
    "admin",
    "terminal",
]


class JSONDecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o.quantize(Decimal("1.00")))
        return o


def get_topic(topic, target=None):
    if target:
        return f"{BASE_TOPIC}/{topic}/{format_topic(target)}"
    return f"{BASE_TOPIC}/{topic}"


def get_client_token(firebase):
    user = format_topic(firebase.name)
    topics = [f"{get_topic(t)}/{user}/#" for t in TOPICS]
    token = get_token(user, subs=topics, publ=topics)
    return {
        "user": user,
        "token": token,
    }


def get_onsite_admin_token(firebase):
    user = format_topic(firebase.name)
    base_topic = f"{get_topic('admin')}/{user}"
    topics = [f"{base_topic}/#"]
    print_topic = None
    if firebase.print_via_mqtt and firebase.print_via_mqtt.id != firebase.id:
        print_topic = f"{get_topic('admin')}/{format_topic(firebase.print_via_mqtt.name)}/action"
        topics.append(print_topic)
    token = get_token(user, subs=topics, publ=topics)
    return {
        "user": user,
        "token": token,
        "base_topic": base_topic,
        "print_topic": print_topic,
    }


def get_token(sub, exp=None, subs=None, publ=None):
    if exp is None:
        # Never expires
        exp = 2**31 - 1

    claims = {
        "sub": sub,
        "iat": datetime.now(tz=timezone.utc),
        "exp": exp,
        "subs": subs,
        "publ": publ,
    }

    return jwt.encode(
        claims,
        base64.b64decode(settings.MQTT_JWT_SECRET),
        algorithm=settings.MQTT_JWT_ALGORITHM,
    )


def format_topic(topic):
    """
    Removes characters that shouldn't be in an MQTT topic field, namely:

    - Can't start with $ (reserved for system topics)
    - Can't contain # or + (wildcards)
    - Can't contain / (separator)
    - All-lowercase, remove spaces (recommended style)
    """

    topic = FORMAT_TOPIC_SYS_RE.sub("", topic)
    topic = FORMAT_TOPIC_WILDCARD_RE.sub("", topic)
    return topic.lower()


def send_mqtt_message(topic, payload={}, retain=False):
    payload_json = json.dumps(payload, cls=JSONDecimalEncoder)

    logger.info(f"Sending MQTT message: {topic} ({payload_json})")
    auth = {
        "username": "apis_server",
        "password": get_token("apis_server", publ=[topic]),
    }
    tls = settings.MQTT_BROKER.get("tls")
    mqtt.single(
        topic,
        payload_json,
        retain=retain,
        hostname=settings.MQTT_BROKER["host"],
        port=settings.MQTT_BROKER["port"],
        auth=auth,
        tls=tls,
    )
