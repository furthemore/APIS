import { type Accessor, createContext } from "solid-js";

import type { OnsiteAdminContext } from "../api";

export const ConfigContext =
  createContext<Accessor<OnsiteAdminContext | undefined>>();
