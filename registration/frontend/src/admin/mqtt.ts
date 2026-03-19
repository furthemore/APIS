import mitt, { type Emitter } from "mitt";
import mqtt from "mqtt";
import { type Accessor, type Setter, createSignal } from "solid-js";

import { type AttendeeDetails, urlForOnsiteDetails } from "./api";

export type ApisMqttConfig = {
  broker: string;
  auth: ApisMqttAuth;
};

export type ApisMqttAuth = {
  user: string;
  token: string;
  root_topic: string;
  print_topic?: string;
};

export type MqttTopic =
  | "authorize/square"
  | "notify/alert"
  | "notify/info"
  | "notify/payment"
  | "notify/scan/id"
  | "notify/scan/raw"
  | "notify/scan/shc"
  | "notify/scan/url"
  | "presence"
  | "refresh"
  | "registration/completed"
  | "transfer";

export type MqttEmitter = Emitter<Record<MqttTopic, object | null>>;

const dec2hex = (dec: number) => {
  return dec.toString(16).padStart(2, "0");
};

export default class MqttClient {
  public errorMessage: Accessor<string | undefined>;
  private readonly setErrorMessage: Setter<string | undefined>;

  public isConnected: Accessor<boolean>;
  private readonly setIsConnected: Setter<boolean>;

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
    console.debug("Connecting to MQTT");

    await this.disconnect();

    this.config = config;
    const wildcardTopic = this.getPrefixedTopic("web/#");

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
        clientId: `web-${config.auth.user}-${this.getClientId()}`,
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

    this.client.on("connect", async (packet) => {
      this.setIsConnected(true);
      this.setErrorMessage(undefined);

      console.debug(
        `Connected to MQTT, sessionPresent - ${packet.sessionPresent}, subscribing to ${wildcardTopic}`,
      );

      try {
        await this.client?.subscribeAsync(wildcardTopic);
        await this.client?.publishAsync(
          this.getPrefixedTopic("web/presence"),
          JSON.stringify(this.getClientId()),
        );
      } catch (err) {
        console.error(`Could not subscribe: ${err}`);

        if (err instanceof Error) {
          this.setErrorMessage(`Connection error: ${err}`);
        } else {
          this.setErrorMessage("Connection error");
        }
        return;
      }

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

      const webPrefix = `${config.auth.root_topic}/web/`;

      let strippedTopic: MqttTopic;
      if (topic.startsWith(webPrefix)) {
        strippedTopic = topic.slice(webPrefix.length) as MqttTopic;
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
        case "authorize/square":
          if (payload?.["url"] && payload?.["state"]) {
            document.cookie = `square_oauth_state=${payload["state"]}; path=/; secure`;
            globalThis.open(payload["url"], "square_oauth");
          }
          break;
        case "notify/alert":
          if (payload?.["text"]) {
            alert(payload["text"]);
          }
          break;
        case "presence":
          if (payload && payload !== this.getClientId()) {
            console.warn("Another device has connected to this station");
            this.emitter?.emit("presence", payload);
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
    if (!this.client) return;

    console.debug("Disconnect requested, ending client");
    await this.client.endAsync();

    this.client = undefined;
  }

  public async publishPrintMessage(payload: string) {
    const topic =
      this.config?.auth.print_topic || this.getPrefixedTopic("station/print");
    await this.client?.publishAsync(topic, payload);
  }

  public async displayRegistration(token: string, details: AttendeeDetails) {
    const url = urlForOnsiteDetails(details);

    await this.client?.publishAsync(
      this.getPrefixedTopic("payment/registration/display"),
      JSON.stringify({ url, token }),
    );
  }

  public async cancelRegistration() {
    await this.client?.publishAsync(
      this.getPrefixedTopic("payment/registration/cancel"),
      "",
    );
  }

  private getPrefixedTopic(topic: string): string {
    return `${this.config!.auth.root_topic}/${topic}`;
  }

  private getClientId(): string {
    let clientId = localStorage.getItem("client-id");
    if (clientId) return clientId;

    const vals = new Uint8Array(8);
    globalThis.crypto.getRandomValues(vals);
    clientId = Array.from(vals, dec2hex).join("");
    localStorage.setItem("client-id", clientId);
    return clientId;
  }
}
