import mqtt from "mqtt";
import mitt, { Emitter } from "mitt";

import { ApisMqttConfig } from "../entrypoints/admin";

type MqttTopic =
  | "refresh"
  | "open"
  | "notification"
  | "alert"
  | "scan/id"
  | "scan/shc";

const emitter: Emitter<Record<MqttTopic, object | null>> = mitt();
window["mqttEmitter"] = emitter;

const randomClientId = Math.random().toString(16).substr(2, 8);

function sendNotification(message: string) {
  if (Notification.permission === "granted") {
    return new Notification(message);
  } else {
    alert(message);
  }
}

export function connectToMqtt(config: ApisMqttConfig) {
  const mqttErrorMessage = document.getElementById("mqtt-client-error");

  function getTopic(topic: string): string {
    return `${config.auth.base_topic}/${topic}`;
  }

  const WILDCARD_TOPIC = getTopic("#");

  const client = mqtt.connect(config.broker, {
    username: config.auth.user,
    password: config.auth.token,
    clientId: `${config.auth.user}-${randomClientId}`,
    clean: true,
  });

  client.on("connect", () => {
    mqttErrorMessage?.classList?.add("d-none");
    console.debug(`Subscribing to ${WILDCARD_TOPIC}`);
    client.subscribe(WILDCARD_TOPIC, (err) => {
      if (err) {
        console.error(`MQTT subscription failed: ${err}`);
      } else {
        client.publish(getTopic("admin_presence"), JSON.stringify(":3"));
      }
    });
  });

  client.on("error", (err) => {
    console.error(`MQTT error: ${err}`);
    mqttErrorMessage?.classList?.remove("d-none");
  });

  client.on("reconnect", () => {
    console.debug("Reconnecting to MQTT");
  });

  client.on("message", (topic, message) => {
    console.debug("MQTT message", topic, message);

    let strippedTopic: MqttTopic;
    if (topic.startsWith(config.auth.base_topic)) {
      strippedTopic = topic.slice(config.auth.base_topic.length + 1) as MqttTopic;
    } else {
      console.warn(`Got topic with unexpected prefix: ${topic}`);
      return;
    }

    let data = message.toString();
    let payload = null;
    try {
      payload = JSON.parse(data);
    } catch (err) {}

    switch (strippedTopic) {
      case "notification":
        if (payload?.["text"]) {
          sendNotification(payload?.["text"]);
        }
        break;
      case "alert":
        if (payload?.["text"]) {
          alert(payload?.["text"]);
        }
        break;
      default:
        emitter.emit(strippedTopic, payload);
        break;
    }
  });
}

export default emitter;
