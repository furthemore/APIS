import { createSignal } from "solid-js";

import { ScanPanel } from "./components/ScanPanel";

export { ScanPanel };

export interface IdData {
  first: string;
  last: string;
  dob: string;
  expiry: string;
  address: string;
  address2: string;
  city: string;
  state: string;
  ZIP: string;
  country: string;
}

export interface ShcData {
  name: string;
  birthday: string;
  verification: ShcIssuer;
  vaccines: ShcVaccine[];
}

export interface ShcIssuer {
  issuer: string;
  verified: boolean;
  trusted: boolean;
}

export interface ShcVaccine {
  name: string;
  lotNumber: string;
  status: string;
  date: string;
  performer: string;
}

export interface ScanLog {
  url: string | undefined;
  id: IdData | undefined;
  shc: ShcData | undefined;
}

export interface ShcMatch {
  name: boolean;
  dob: boolean;
}

const [scanLog, setScanLog] = createSignal<ScanLog>({
  url: undefined,
  id: undefined,
  shc: undefined,
});
