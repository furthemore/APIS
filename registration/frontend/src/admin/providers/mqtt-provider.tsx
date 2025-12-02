import { type Accessor, createContext } from "solid-js";

import type MqttClient from "../mqtt";

export const MqttContext = createContext<Accessor<MqttClient | undefined>>();
