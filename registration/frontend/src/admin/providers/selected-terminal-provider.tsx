import { type Accessor, createContext } from "solid-js";

import type { SelectedTerminal } from "../api";

export const SelectedTerminalContext =
  createContext<Accessor<SelectedTerminal>>();
