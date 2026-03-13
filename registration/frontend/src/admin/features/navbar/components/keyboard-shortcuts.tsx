import { Dialog } from "@kobalte/core/dialog";
import { formatForDisplay } from "@tanstack/solid-hotkeys";
import { type Component, For } from "solid-js";

import { Modal, type ModalSignal } from "@components/modal";

import { KNOWN_SHORTCUTS } from "../utils";

export const KeyboardShortcuts: Component<{ signal: ModalSignal }> = (
  props,
) => {
  return (
    <Modal signal={props.signal}>
      <div class="modal-dialog modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <Dialog.Title as="h5" class="modal-title">
              Keyboard Shortcuts
            </Dialog.Title>

            <Dialog.CloseButton type="button" class="btn-close" />
          </div>

          <Dialog.Description as="div" class="modal-body">
            <div class="table-responsive">
              <table class="table">
                <thead>
                  <tr>
                    <th>Shortcut</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  <For each={KNOWN_SHORTCUTS}>
                    {(entry) => (
                      <tr>
                        <th>
                          <kbd class="kbd">
                            {formatForDisplay(entry.shortcut)}
                          </kbd>
                        </th>
                        <td>{entry.description}</td>
                      </tr>
                    )}
                  </For>
                </tbody>
              </table>
            </div>
          </Dialog.Description>
        </div>
      </div>
    </Modal>
  );
};
