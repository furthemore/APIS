import { Combobox } from "@kobalte/core/combobox";
import { Dialog } from "@kobalte/core/dialog";
import { createWritableMemo } from "@solid-primitives/memo";
import { useQuery } from "@tanstack/solid-query";
import { type Accessor, type Component, For, Show, useContext } from "solid-js";

import {
  APIError,
  type BadgeCart,
  type BadgeEditParams,
  type IdAndName,
  badgeHistoryOptions,
  urlForBadge,
  useEditBadge,
  useRemoveBadgeFromCart,
} from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { Button } from "@components/button";
import { Modal } from "@components/modal";

export const BadgeEditModal: Component<{
  badge: BadgeCart;
  open: Accessor<boolean>;
  onOpenChange: (open: boolean) => void;
}> = (props) => {
  const config = useContext(ConfigContext)!;

  const [badgeName, setBadgeName] = createWritableMemo(
    () => props.badge.badgeName,
  );
  const [eventId, setEventId] = createWritableMemo(() => props.badge.eventId);

  const editBadge = useEditBadge();
  const removeFromCart = useRemoveBadgeFromCart();
  const history = useQuery(() => badgeHistoryOptions(props.badge.id));

  const currentEvent = () => config()?.events.find((e) => e.id === eventId());
  const hasRollHistory = () => (history.data?.rollHistory.length ?? 0) > 0;
  const hasPrintHistory = () => (history.data?.printHistory.length ?? 0) > 0;

  const submit = async (ev: SubmitEvent) => {
    ev.preventDefault();

    const rollingForward = eventId() !== props.badge.eventId;
    const params: BadgeEditParams = {
      id: props.badge.id,
      badgeName: badgeName(),
      eventId: eventId(),
    };

    try {
      await editBadge.mutateAsync(params);
      if (rollingForward) {
        await removeFromCart.mutateAsync(props.badge.id);
      }
      props.onOpenChange(false);
    } catch (err) {
      if (err instanceof APIError) {
        alert(err.reason || "Unknown API error");
      } else {
        alert(err);
      }
    }
  };

  return (
    <Modal open={props.open} onOpenChange={props.onOpenChange}>
      <div class="modal-dialog modal-dialog-scrollable">
        <form class="modal-content" onSubmit={submit}>
          <div class="modal-header">
            <Dialog.Title as="h5" class="modal-title">
              Edit Badge
            </Dialog.Title>

            <Dialog.CloseButton
              type="button"
              class="btn-close"
              disabled={editBadge.isPending}
            />
          </div>

          <Dialog.Description as="div" class="modal-body">
            <div class="mb-3">
              <label class="form-label" for="badge-name">
                Badge Name
              </label>

              <input
                id="badge-name"
                type="text"
                class="form-control"
                value={badgeName()}
                onInput={(e) => setBadgeName(e.currentTarget.value)}
                maxlength={200}
                required
              />
            </div>

            <div class="mb-3">
              <label class="form-label" for="badge-event">
                Event
              </label>

              <Combobox<IdAndName>
                options={config()?.events ?? []}
                optionValue="id"
                optionTextValue="name"
                optionLabel="name"
                value={currentEvent()}
                onChange={(ev) => setEventId(ev?.id ?? props.badge.eventId)}
                disabled={hasRollHistory()}
                itemComponent={(itemProps) => (
                  <Combobox.Item item={itemProps.item}>
                    <Combobox.ItemLabel as="a" class="dropdown-item" href="#">
                      {itemProps.item.rawValue.name}
                    </Combobox.ItemLabel>
                  </Combobox.Item>
                )}
              >
                <Combobox.Control class="input-group">
                  <Combobox.Input class="form-control" id="badge-event" />
                  <Combobox.Trigger class="btn btn-outline-secondary dropdown-toggle" />
                </Combobox.Control>
                <Combobox.Portal>
                  <Combobox.Content style={{ "z-index": 9999 }}>
                    <Combobox.Listbox class="dropdown-menu show" />
                  </Combobox.Content>
                </Combobox.Portal>
              </Combobox>
            </div>

            <Show when={hasPrintHistory()}>
              <div class="mb-3">
                <p class="form-label">Print History</p>
                <table class="table table-sm table-striped table-bordered">
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Terminal</th>
                      <th>When</th>
                    </tr>
                  </thead>
                  <tbody>
                    <For each={history.data!.printHistory}>
                      {(entry) => (
                        <tr>
                          <td>{entry.source}</td>
                          <td>{entry.terminal}</td>
                          <td>
                            {new Date(entry.printedAt).toLocaleDateString()}
                          </td>
                        </tr>
                      )}
                    </For>
                  </tbody>
                </table>
              </div>
            </Show>

            <Show when={hasRollHistory()}>
              <div class="mb-3">
                <p class="form-label">Roll-Forward History</p>
                <table class="table table-sm table-striped table-bordered">
                  <thead>
                    <tr>
                      <th>From</th>
                      <th>To</th>
                      <th>When</th>
                      <th>By</th>
                    </tr>
                  </thead>
                  <tbody>
                    <For each={history.data!.rollHistory}>
                      {(entry) => (
                        <tr>
                          <td>{entry.fromEvent}</td>
                          <td>{entry.toEvent}</td>
                          <td>
                            {new Date(entry.rolledAt).toLocaleDateString()}
                          </td>
                          <td>{entry.rolledBy}</td>
                        </tr>
                      )}
                    </For>
                  </tbody>
                </table>
              </div>
            </Show>
          </Dialog.Description>

          <div class="modal-footer">
            <a
              href={urlForBadge(props.badge.id).toString()}
              target="edit"
              class="btn btn-outline-secondary me-auto"
            >
              Open in Admin
            </a>

            <Dialog.CloseButton
              class="btn btn-outline-danger"
              disabled={editBadge.isPending}
            >
              Cancel
            </Dialog.CloseButton>

            <Button
              type="submit"
              class="btn btn-primary"
              loading={editBadge.isPending}
            >
              Save
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
