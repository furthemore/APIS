import { faCheck, faXmark } from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import { type Component, useContext } from "solid-js";

import {
  type UserSettingKey,
  UserSettingsContext,
} from "@admin/providers/user-settings-provider";
import { IconAndLabel } from "@components/icon-and-label";

export const ToggleSetting: Component<{
  name: string;
  key: UserSettingKey;
}> = (props) => {
  const userSettings = useContext(UserSettingsContext)!;

  const enabled = () => userSettings().settings()[props.key];

  const setEnabled = (enabled: boolean) => {
    userSettings().store(props.key, enabled);
  };

  return (
    <DropdownMenu.CheckboxItem
      as="li"
      closeOnSelect={false}
      checked={enabled()}
      onChange={setEnabled}
    >
      <button class="dropdown-item">
        <IconAndLabel
          children={props.name}
          icon={enabled() ? faCheck : faXmark}
          fw
        />
      </button>
    </DropdownMenu.CheckboxItem>
  );
};
