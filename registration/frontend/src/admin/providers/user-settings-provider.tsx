import {
  type Accessor,
  type Setter,
  createContext,
  createSignal,
} from "solid-js";

const STORAGE_KEY = "user-settings";

export type UserSettingKey =
  | "clearCartAfterPrint"
  | "containerFluid"
  | "multipleBadgeColumns"
  | "printAfterPayment"
  | "searchBirthday";

export type UserSettings = Record<UserSettingKey, boolean>;

const USER_DEFAULTS: UserSettings = {
  clearCartAfterPrint: false,
  containerFluid: false,
  multipleBadgeColumns: true,
  printAfterPayment: true,
  searchBirthday: true,
};

export class UserSettingsManager {
  public settings: Accessor<UserSettings>;
  private setSettings: Setter<UserSettings>;

  constructor() {
    const settingsData = window.localStorage.getItem(STORAGE_KEY);
    let userSettings: UserSettings;

    if (settingsData) {
      try {
        userSettings = { ...USER_DEFAULTS, ...JSON.parse(settingsData) };
      } catch (err) {
        console.error(`Could not parse settings: ${err}`);
        userSettings = USER_DEFAULTS;
      }
    } else {
      userSettings = USER_DEFAULTS;
    }

    const [settings, setSettings] = createSignal<UserSettings>(userSettings);
    [this.settings, this.setSettings] = [settings, setSettings];
  }

  private saveSettings() {
    const data = JSON.stringify(this.settings());
    window.localStorage.setItem(STORAGE_KEY, data);
  }

  store(setting: UserSettingKey, value: boolean) {
    this.setSettings({ ...this.settings(), [setting]: value });
    this.saveSettings();
  }
}

export const UserSettingsContext =
  createContext<Accessor<UserSettingsManager>>();
