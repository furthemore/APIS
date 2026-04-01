import { Combobox } from "@kobalte/core/combobox";
import { Dialog } from "@kobalte/core/dialog";
import { ToggleGroup } from "@kobalte/core/toggle-group";
import {
  type Component,
  For,
  Match,
  Switch,
  createEffect,
  createSignal,
  useContext,
} from "solid-js";

import { useCreateAndApplyDiscount } from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { Button } from "@components/button";
import { Modal, type ModalSignal } from "@components/modal";

const DISCOUNT_CHOICES = ["Comp", "Amount", "Percent"] as const;
type DiscountType = (typeof DISCOUNT_CHOICES)[number];

export const DiscountModal: Component<{ signal: ModalSignal }> = (props) => {
  const config = useContext(ConfigContext)!;

  const createAndApplyDiscount = useCreateAndApplyDiscount();

  const [selectedType, setSelectedType] = createSignal<DiscountType>("Comp");

  createEffect(() => {
    if (!props.signal[0]()) {
      setSelectedType("Comp");
    }
  });

  const submit = (ev: SubmitEvent) => {
    ev.preventDefault();

    if (!(ev.target instanceof HTMLFormElement)) {
      return;
    }

    const data = new FormData(ev.target);

    createAndApplyDiscount.mutate(
      {
        type: data.get("discount-type") === "Amount" ? "Amount" : "Percent",
        department: data.get("department")?.toString() || "",
        value: data.get("value")?.toString().trim() || "",
        notes: data.get("notes")?.toString().trim() || "",
      },
      {
        onSuccess: () => props.signal[1](false),
      },
    );
  };

  return (
    <Modal signal={props.signal}>
      <div class="modal-dialog modal-dialog-scrollable">
        <form class="modal-content" onSubmit={submit}>
          <div class="modal-header">
            <Dialog.Title as="h5" class="modal-title">
              Create Discount
            </Dialog.Title>

            <Dialog.CloseButton
              type="button"
              class="btn-close"
              disabled={createAndApplyDiscount.isPending}
            />
          </div>

          <Dialog.Description as="div" class="modal-body">
            <div class="mb-3">
              <p class="form-label">Discount Type</p>

              <input
                type="hidden"
                name="discount-type"
                value={selectedType()}
              />

              <ToggleGroup
                class="btn-group w-100"
                value={selectedType()}
                onChange={setSelectedType}
              >
                <For each={DISCOUNT_CHOICES}>
                  {(type) => (
                    <ToggleGroup.Item
                      class="btn btn-outline-primary"
                      value={type}
                    >
                      {type}
                    </ToggleGroup.Item>
                  )}
                </For>
              </ToggleGroup>
            </div>

            <Switch>
              <Match when={selectedType() === "Comp"}>
                <input type="hidden" name="value" value="100" />
              </Match>

              <Match when={selectedType() === "Amount"}>
                <div class="mb-3">
                  <label for="amount" class="form-label">
                    Amount
                  </label>
                  <div class="input-group">
                    <span class="input-group-text">$</span>
                    <input
                      type="number"
                      class="form-control"
                      id="amount"
                      name="value"
                      step="0.01"
                      min="0.01"
                      required
                    />
                  </div>
                </div>
              </Match>

              <Match when={selectedType() === "Percent"}>
                <div class="mb-3">
                  <label for="percent" class="form-label">
                    Percent
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      class="form-control"
                      id="percent"
                      name="value"
                      step="1"
                      min="1"
                      max="100"
                      required
                    />
                    <span class="input-group-text">%</span>
                  </div>
                </div>
              </Match>
            </Switch>

            <div class="mb-3">
              <label class="form-label" for="department">
                Sponsoring Department
              </label>

              <Combobox
                name="department"
                options={config()?.departments || []}
                placeholder="Select department"
                itemComponent={(props) => (
                  <Combobox.Item item={props.item}>
                    <Combobox.ItemLabel as="a" class="dropdown-item" href="#">
                      {props.item.rawValue}
                    </Combobox.ItemLabel>
                  </Combobox.Item>
                )}
              >
                <Combobox.HiddenSelect />
                <Combobox.Control class="input-group">
                  <Combobox.Input
                    class="form-control"
                    id="department"
                    required
                  />
                  <Combobox.Trigger class="btn btn-outline-secondary dropdown-toggle" />
                </Combobox.Control>
                <Combobox.Portal>
                  <Combobox.Content style={{ "z-index": 99999 }}>
                    <Combobox.Listbox class="dropdown-menu show" />
                  </Combobox.Content>
                </Combobox.Portal>
              </Combobox>
            </div>

            <div class="mb-3">
              <label class="form-label" for="notes">
                Notes
              </label>

              <textarea
                id="notes"
                name="notes"
                class="form-control size-content"
              />
            </div>
          </Dialog.Description>

          <div class="modal-footer">
            <Dialog.CloseButton
              class="btn btn-outline-danger"
              disabled={createAndApplyDiscount.isPending}
            >
              Cancel
            </Dialog.CloseButton>

            <Button
              type="submit"
              class="btn btn-primary"
              loading={createAndApplyDiscount.isPending}
            >
              Apply
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
