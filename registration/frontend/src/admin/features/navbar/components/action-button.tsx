import { type IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import { type Hotkey, formatForDisplay } from "@tanstack/solid-hotkeys";
import { type Component } from "solid-js";

import { IconAndLabel } from "@components/icon-and-label";

export const ActionButton: Component<{
  name: string;
  icon: IconDefinition;
  action: () => unknown;
  keyboardShortcut?: Hotkey;
  spin?: boolean;
}> = (props) => {
  return (
    <DropdownMenu.Item as="li">
      <button
        type="button"
        class="dropdown-item d-flex align-items-center column-gap-2"
        onClick={() => props.action()}
      >
        <IconAndLabel icon={props.icon} spin={props.spin} fw>
          <span class="flex-grow-1">{props.name}</span>
        </IconAndLabel>

        {props.keyboardShortcut && (
          <kbd class="kbd">{formatForDisplay(props.keyboardShortcut)}</kbd>
        )}
      </button>
    </DropdownMenu.Item>
  );
};
