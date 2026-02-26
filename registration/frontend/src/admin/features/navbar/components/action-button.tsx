import { type IconDefinition } from "@fortawesome/free-solid-svg-icons";
import { DropdownMenu } from "@kobalte/core/dropdown-menu";
import type { KbdKey } from "@solid-primitives/keyboard";
import { type Component, For, createMemo } from "solid-js";

import { IconAndLabel } from "@components/icon-and-label";

const KEY_NAMES: Record<KbdKey, string> = {
  Control: "Ctrl",
  Alt: "Alt",
  Meta: "Meta",
  Shift: "Shift",
};

export const ActionButton: Component<{
  name: string;
  icon: IconDefinition;
  action: () => unknown;
  keyboardShortcut?: KbdKey[];
  spin?: boolean;
}> = (props) => {
  const renamedKeys = createMemo(() => {
    return props.keyboardShortcut?.map((key) => {
      return KEY_NAMES[key] || key;
    });
  });

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
          <span>
            <For each={renamedKeys()}>
              {(key, index) => (
                <>
                  {index() > 0 && " + "}
                  <kbd class="kbd">{key}</kbd>
                </>
              )}
            </For>
          </span>
        )}
      </button>
    </DropdownMenu.Item>
  );
};
