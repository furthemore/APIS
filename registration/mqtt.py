import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import logging
import re

from django.conf import settings
import jwt
from paho.mqtt import publish as mqtt_publish

from registration.models import Firebase

FORMAT_TOPIC_SYS_RE = re.compile(r"^\$")
FORMAT_TOPIC_WILDCARD_RE = re.compile(r"[\#\+ /]")

BASE_TOPIC = "apis"

logger = logging.getLogger(__name__)


class JSONDecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o.quantize(Decimal("1.00")))
        return o


def get_topic(*args: str, name: str) -> str:
    """Build a topic for a given device.

    Wildcard segments are allowed."""
    segments = [BASE_TOPIC, format_topic(name)] + [
        format_topic(segment, allow_wildcard=True) for segment in args
    ]
    return "/".join(segments)


def get_payment_token(firebase: Firebase) -> dict:
    sub = get_topic("payment", "#", name=str(firebase.name))

    pub = [
        get_topic("station", "notify", "alert", name=str(firebase.name)),
        get_topic("station", "notify", "payment", name=str(firebase.name)),
    ]

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=pub, exp=60 * 60 * 24 * 7)

    return {
        "user": user,
        "token": token,
        "root_topic": get_topic(name=str(firebase.name)),
    }


def get_onsite_admin_token(firebase: Firebase) -> dict:
    sub = get_topic("web", "#", name=str(firebase.name))

    pub = [
        get_topic("payment", "#", name=str(firebase.name)),
        get_topic("station", "#", name=str(firebase.name)),
    ]

    print_firebase = firebase
    if firebase.print_via_mqtt and firebase.print_via_mqtt.id != firebase.id:
        print_firebase = firebase.print_via_mqtt

    print_device = "station"
    if firebase.print_via_payment:
        print_device = "payment"

    print_topic = get_topic(print_device, "print", name=str(print_firebase.name))

    if print_device != "station" or print_firebase.id != firebase.id:
        pub.append(print_topic)

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=pub, exp=60 * 60 * 24)

    return {
        "user": user,
        "token": token,
        "root_topic": get_topic(name=str(firebase.name)),
        "print_topic": print_topic,
    }


def get_receipt_token(firebase: Firebase) -> dict:
    sub = get_topic("receipt", "#", name=str(firebase.name))

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=[], exp=60 * 60 * 24 * 7)

    return {
        "user": user,
        "token": token,
    }


def get_station_token(firebase: Firebase) -> dict:
    sub = get_topic("station", "#", name=str(firebase.name))

    pub = [
        get_topic("web", "notify", "#", name=str(firebase.name))
    ]

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=pub, exp=60 * 60 * 24 * 7)

    return {
        "user": user,
        "token": token,
        "base_topic": get_topic("station", name=str(firebase.name)),
    }


def get_token(sub, exp=None, subs=None, publ=None) -> str:
    if exp is None:
        # Never expires
        exp = 2**31 - 1
    else:
        exp = datetime.now(tz=timezone.utc) + timedelta(seconds=exp)

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


def format_topic(topic: str, allow_wildcard: bool = False) -> str:
    """
    Removes characters that shouldn't be in an MQTT topic field, namely:

    - Can't start with $ (reserved for system topics)
    - Can't contain # or + (wildcards)
    - Can't contain / (separator)
    - All-lowercase, remove spaces (recommended style)
    """

    if allow_wildcard and topic in ("+", "#"):
        return topic

    topic = FORMAT_TOPIC_SYS_RE.sub("", topic)
    topic = FORMAT_TOPIC_WILDCARD_RE.sub("", topic)
    return topic.lower()


def send_mqtt_message(topic: str, payload: dict = {}, retain: bool = False):
    payload_json = json.dumps(payload, cls=JSONDecimalEncoder)

    logger.info(f"Sending MQTT message: {topic} ({payload_json})")

    auth = {
        "username": "apis_server",
        "password": get_token("apis_server", publ=[topic], exp=30),
    }
    tls = settings.MQTT_BROKER.get("tls")

    mqtt_publish.single(
        topic,
        payload_json,
        retain=retain,
        hostname=settings.MQTT_BROKER["host"],
        port=settings.MQTT_BROKER["port"],
        auth=auth,
        tls=tls,
    )
