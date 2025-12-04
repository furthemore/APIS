import mitt, { type Emitter } from "mitt";
import mqtt from "mqtt";
import { type Accessor, type Setter, createSignal } from "solid-js";

export type ApisMqttConfig = {
  broker: string;
  auth: ApisMqttAuth;
};

export type ApisMqttAuth = {
  user: string;
  token: string;
  base_topic: string;
  print_topic?: string;
};

export type MqttTopic =
  | "alert"
  | "admin_presence"
  | "authorize_terminal"
  | "notification"
  | "open"
  | "refresh"
  | "scan/id"
  | "scan/shc"
  | "transfer";

export type MqttEmitter = Emitter<Record<MqttTopic, object | null>>;

const LOCK_KEY = "mqtt-connection";

const dec2hex = (dec: number) => {
  return dec.toString(16).padStart(2, "0");
};

export default class MqttClient {
  public errorMessage: Accessor<string | undefined>;
  private setErrorMessage: Setter<string | undefined>;

  public isConnected: Accessor<boolean>;
  private setIsConnected: Setter<boolean>;

  public emitter: Emitter<Record<MqttTopic, object | null>>;

  private client?: mqtt.MqttClient;
  private config?: ApisMqttConfig;

  constructor() {
    console.debug("Creating new MQTT client");

    const [isConnected, setIsConnected] = createSignal(false);
    [this.isConnected, this.setIsConnected] = [isConnected, setIsConnected];

    const [errorMessage, setErrorMessage] = createSignal<string>();
    [this.errorMessage, this.setErrorMessage] = [errorMessage, setErrorMessage];

    this.emitter = mitt();
  }

  public async connect(config: ApisMqttConfig) {
    if ("locks" in navigator) {
      navigator.locks.request(LOCK_KEY, async () => {
        await this._connect(config);
      });
    } else {
      await this._connect(config);
    }
  }

  private async _connect(config: ApisMqttConfig) {
    console.debug("Connecting to MQTT");

    await this._disconnect();

    this.config = config;
    const wildcardTopic = this.getPrefixedTopic("#");

    let connectResolve: (() => void) | undefined;
    let connectReject: ((err: Error) => void) | undefined;

    const promise = new Promise<void>((resolve, reject) => {
      connectResolve = resolve;
      connectReject = reject;
    });

    try {
      this.client = mqtt.connect(config.broker, {
        username: config.auth.user,
        password: config.auth.token,
        clientId: `admin-${config.auth.user}-${this.getClientId()}`,
        clean: false,
        protocolVersion: 5,
        timerVariant: "native",
        properties: {
          sessionExpiryInterval: 300,
        },
      });
    } catch (err) {
      if (err instanceof Error) {
        this.setErrorMessage(`Connection error: ${err}`);
      } else {
        this.setErrorMessage("Connection error");
      }
      return;
    }

    this.client.on("connect", async () => {
      this.setIsConnected(true);
      this.setErrorMessage(undefined);

      console.debug(`Subscribing to ${wildcardTopic}`);
      await this.client?.subscribeAsync(wildcardTopic);
      await this.client?.publishAsync(
        this.getPrefixedTopic("admin_presence"),
        JSON.stringify(this.getClientId()),
      );

      if (connectResolve) {
        connectResolve();
        connectResolve = undefined;
      }
    });

    this.client.on("error", (err: Error) => {
      console.error(`MQTT error: ${err}`);
      this.setErrorMessage(err.toString());

      if (connectReject) {
        connectReject(err);
        connectReject = undefined;
      }
    });

    this.client.on("close", () => {
      console.debug("MQTT close");
      this.setIsConnected(false);
    });

    this.client.on("disconnect", (evt) => {
      console.debug(`MQTT disconnect: ${evt.reasonCode}`);
      this.setErrorMessage(`Disconnected: ${evt.reasonCode || "Unknown"}`);
    });

    this.client.on("reconnect", () => {
      console.debug("Reconnecting to MQTT");
    });

    this.client.on("message", (topic, message) => {
      const data = message.toString();
      console.debug("MQTT message", topic, data);

      let strippedTopic: MqttTopic;
      if (topic.startsWith(config.auth.base_topic)) {
        strippedTopic = topic.slice(
          config.auth.base_topic.length + 1,
        ) as MqttTopic;
      } else {
        console.warn(`Got topic with unexpected prefix: ${topic}`);
        return;
      }

      let payload = null;
      try {
        payload = JSON.parse(data);
      } catch {
        console.warn("Payload was not valid JSON", data);
      }

      switch (strippedTopic) {
        case "notification":
          if (payload?.["text"]) {
            if (Notification.permission === "granted") {
              new Notification(payload["text"]);
            } else {
              alert(payload["text"]);
            }
          }
          break;
        case "alert":
          if (payload?.["text"]) {
            alert(payload["text"]);
          }
          break;
        case "authorize_terminal":
          if (payload?.["url"] && payload?.["state"]) {
            document.cookie = `square_oauth_state=${payload["state"]}; path=/`;
            window.open(payload["url"], "square_oauth");
          }
          break;
        case "admin_presence":
          if (payload && payload !== this.getClientId()) {
            console.warn("Another device has connected to this station");
            this.emitter?.emit("admin_presence", payload);
          }
          break;
        default:
          this.emitter?.emit(strippedTopic, payload);
          break;
      }
    });

    await promise;
  }

  public async disconnect() {
    if ("locks" in navigator) {
      navigator.locks.request(LOCK_KEY, async () => {
        await this._disconnect();
      });
    } else {
      await this._disconnect();
    }
  }

  private async _disconnect() {
    if (!this.client) return;

    console.debug("Disconnect requested, ending client");
    await this.client?.endAsync();

    this.client = undefined;
  }

  public async publishMessage(topic: string, payload: string) {
    console.debug(`Publishing MQTT message to topic ${topic}`, payload);
    await this.client?.publishAsync(topic, payload);
  }

  public async publishPrintMessage(payload: string) {
    const topic =
      this.config?.auth.print_topic || this.getPrefixedTopic("action");
    await this.publishMessage(topic, payload);
  }

  private getPrefixedTopic(topic: string): string {
    return `${this.config!.auth.base_topic}/${topic}`;
  }

  private getClientId(): string {
    let clientId = localStorage.getItem("client-id");
    if (clientId) return clientId;

    const vals = new Uint8Array(8);
    window.crypto.getRandomValues(vals);
    clientId = Array.from(vals, dec2hex).join("");
    localStorage.setItem("client-id", clientId);
    return clientId;
  }
}
