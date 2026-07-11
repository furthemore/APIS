import base64
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
from django.conf import settings
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
    sub = get_topic("payment/#", name=str(firebase.name))

    pub = [
        get_topic("web/notify/alert", name=str(firebase.name)),
        get_topic("web/notify/payment", name=str(firebase.name)),
        get_topic("web/notify/scan/raw", name=str(firebase.name)),
    ]

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=pub, exp=60 * 60 * 24 * 7)

    return {
        "user": user,
        "token": token,
        "root_topic": get_topic(name=str(firebase.name)),
    }


def get_onsite_admin_token(firebase: Firebase) -> dict:
    sub = get_topic("web/#", name=str(firebase.name))

    pub = [
        get_topic("web/presence", name=str(firebase.name)),
        get_topic("payment/#", name=str(firebase.name)),
        get_topic("station/#", name=str(firebase.name)),
    ]

    print_topic = None
    if firebase.print_via_mqtt:
        print_firebase = firebase.print_via_mqtt

        print_device = None
        match firebase.print_target:
            case Firebase.STATION_SERVICE:
                print_device = "station"
            case Firebase.MQTT_REGISTER_APP:
                print_device = "payment"
            case Firebase.WEB_USB:
                print_device = "web"

        if print_device:
            print_topic = get_topic(
                print_device, "print", name=str(print_firebase.name)
            )

            if (
                print_device not in ("payment", "station")
                or print_firebase.id != firebase.id
            ):
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
    sub = get_topic("receipt/#", name=str(firebase.name))
    pub = get_topic("web/notify/alert", name=str(firebase.name))

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=[pub], exp=60 * 60 * 24 * 7)

    return {
        "user": user,
        "token": token,
    }


def get_station_token(firebase: Firebase) -> dict:
    sub = get_topic("station/#", name=str(firebase.name))
    pub = [get_topic("web/notify/#", name=str(firebase.name))]

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=pub, exp=60 * 60 * 24 * 7)

    return {
        "user": user,
        "token": token,
        "base_topic": get_topic("station", name=str(firebase.name)),
    }


def get_state_token(firebase: Firebase) -> dict:
    sub = get_topic("payment/state", name=str(firebase.name))

    user = format_topic(str(firebase.name))
    token = get_token(user, subs=[sub], publ=[])

    return {"user": user, "token": token}


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
    - Can't contain # or + (wildcards) unless specifically permitted
    - All-lowercase, remove spaces (recommended style)
    """

    if "/" in topic:
        return "/".join(
            [
                format_topic(segment, allow_wildcard=allow_wildcard)
                for segment in topic.split("/")
            ]
        )

    if allow_wildcard and topic in ("+", "#"):
        return topic

    topic = FORMAT_TOPIC_SYS_RE.sub("", topic)
    topic = FORMAT_TOPIC_WILDCARD_RE.sub("", topic)

    if len(topic) == 0:
        raise ValueError("Each topic segment must have value")

    return topic.lower()


def send_mqtt_message(topic: str, payload: dict = {}, retain: bool = False):
    payload_json = json.dumps(payload, cls=JSONDecimalEncoder)
    logger.debug(
        "Sending MQTT message",
        extra={"topic": topic, "payload_size": len(payload_json)},
    )

    auth = {
        "username": "apis-server",
        "password": get_token("apis-server", publ=[topic], exp=30),
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
