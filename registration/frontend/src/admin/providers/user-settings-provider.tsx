import { Accessor, createContext, createSignal, Setter } from "solid-js";

const STORAGE_KEY = "user-settings";

export type UserSettingKey =
  | "clear_cart_after_print"
  | "container_fluid"
  | "print_after_payment";

export type UserSettings = Record<UserSettingKey, any>;

const USER_DEFAULTS: UserSettings = {
  clear_cart_after_print: false,
  container_fluid: false,
  print_after_payment: true,
};

export class UserSettingsManager {
  public userSettings: Accessor<UserSettings>;
  private setUserSettings: Setter<UserSettings>;

  constructor() {
    const settingsData = window.localStorage.getItem(STORAGE_KEY);
    let settings: UserSettings;

    if (settingsData) {
      try {
        settings = { ...USER_DEFAULTS, ...JSON.parse(settingsData) };
      } catch (err) {
        console.error(`Could not parse settings: ${err}`);
        settings = USER_DEFAULTS;
      }
    } else {
      settings = USER_DEFAULTS;
    }

    [this.userSettings, this.setUserSettings] =
      createSignal<UserSettings>(settings);
  }

  private saveSettings() {
    const data = JSON.stringify(this.userSettings());
    window.localStorage.setItem(STORAGE_KEY, data);
  }

  store(setting: UserSettingKey, value: any) {
    this.setUserSettings({ ...this.userSettings(), [setting]: value });
    this.saveSettings();
  }
}

export const UserSettingsContext = createContext<UserSettingsManager>();
