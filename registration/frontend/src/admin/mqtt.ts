import mqtt from "mqtt";
import mitt, { Emitter } from "mitt";

import { ApisMqttConfig } from "../entrypoints/admin";
import { Accessor, createSignal, Setter } from "solid-js";

export type MqttTopic =
  | "refresh"
  | "open"
  | "notification"
  | "alert"
  | "scan/id"
  | "scan/shc";

export type MqttEmitter = Emitter<Record<MqttTopic, object | null>>;

export default class MqttClient {
  public errorMessage: Accessor<string>;
  private setErrorMessage: Setter<string>;

  public emitter: Emitter<Record<MqttTopic, object | null>>;

  private client: mqtt.MqttClient;
  private config: ApisMqttConfig;

  constructor(config: ApisMqttConfig) {
    this.config = config;

    const [errorMessage, setErrorMessage] = createSignal<string>();
    this.errorMessage = errorMessage;
    this.setErrorMessage = setErrorMessage;

    this.emitter = mitt();

    const WILDCARD_TOPIC = this.getPrefixedTopic("#");

    const randomClientId = Math.random().toString(16).substr(2, 8);
    this.client = mqtt.connect(config.broker, {
      username: config.auth.user,
      password: config.auth.token,
      clientId: `${config.auth.user}-${randomClientId}`,
      clean: true,
    });

    this.client.on("connect", () => {
      this.setErrorMessage(undefined);
      console.debug(`Subscribing to ${WILDCARD_TOPIC}`);
      this.client.subscribe(WILDCARD_TOPIC, (err) => {
        if (err) {
          console.error(`MQTT subscription failed: ${err}`);
        } else {
          this.client.publish(
            this.getPrefixedTopic("admin_presence"),
            JSON.stringify(":3")
          );
        }
      });
    });

    this.client.on("error", (err: Error) => {
      console.error(`MQTT error: ${err}`);
      this.setErrorMessage(err.toString());
    });

    this.client.on("reconnect", () => {
      console.debug("Reconnecting to MQTT");
    });

    this.client.on("message", (topic, message) => {
      let data = message.toString();
      console.debug("MQTT message", topic, data);

      let strippedTopic: MqttTopic;
      if (topic.startsWith(config.auth.base_topic)) {
        strippedTopic = topic.slice(
          config.auth.base_topic.length + 1
        ) as MqttTopic;
      } else {
        console.warn(`Got topic with unexpected prefix: ${topic}`);
        return;
      }

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
          this.emitter.emit(strippedTopic, payload);
          break;
      }
    });
  }

  public disconnect() {
    this.client.end();
  }

  public publishMessage(topic: string, payload: string) {
    this.client.publish(this.getPrefixedTopic(topic), payload);
  }

  private getPrefixedTopic(topic: string): string {
    return `${this.config.auth.base_topic}/${topic}`;
  }
}

function sendNotification(message: string) {
  if (Notification.permission === "granted") {
    return new Notification(message);
  } else {
    alert(message);
  }
}
