import { Combobox } from "@kobalte/core/combobox";
import { Dialog } from "@kobalte/core/dialog";
import { ToggleGroup } from "@kobalte/core/toggle-group";
import {
  type Component,
  For,
  Match,
  Switch,
  createEffect,
  useContext,
} from "solid-js";
import { createStore } from "solid-js/store";

import { useCreateAndApplyDiscount } from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { Button } from "@components/button";
import { Modal, type ModalSignal } from "@components/modal";

const DISCOUNT_CHOICES = ["Comp", "Amount", "Percent"] as const;
type DiscountType = (typeof DISCOUNT_CHOICES)[number];

const typeForSelectedType = (
  selectedType: DiscountType,
): "Amount" | "Percent" => {
  if (selectedType === "Amount") {
    return "Amount";
  } else if (selectedType === "Comp" || selectedType === "Percent") {
    return "Percent";
  } else {
    throw new Error(`Unknown DiscountType: ${selectedType}`);
  }
};

const DEFAULT_FORM = {
  type: "Comp" as DiscountType,
  department: "",
  value: "",
  notes: "",
};

export const DiscountModal: Component<{ signal: ModalSignal }> = (props) => {
  const config = useContext(ConfigContext)!;

  const createAndApplyDiscount = useCreateAndApplyDiscount();

  const [form, setForm] = createStore(structuredClone(DEFAULT_FORM));

  createEffect(() => {
    if (!props.signal[0]()) {
      setForm(structuredClone(DEFAULT_FORM));
    }
  });

  const updateType = (type: string | null) => {
    if (type) {
      setForm({ type: type as DiscountType, value: "" });
    }
  };

  const submit = (ev: SubmitEvent) => {
    ev.preventDefault();

    createAndApplyDiscount.mutate(
      {
        type: typeForSelectedType(form.type),
        department: form.department,
        value: form.type === "Comp" ? "100" : form.value,
        notes: form.notes,
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

              <ToggleGroup
                class="btn-group w-100"
                value={form.type}
                onChange={updateType}
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
              <Match when={form.type === "Amount"}>
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
                      step="0.01"
                      min="0.01"
                      onInput={(ev) => setForm("value", ev.target.value)}
                      required
                    />
                  </div>
                </div>
              </Match>

              <Match when={form.type === "Percent"}>
                <div class="mb-3">
                  <label for="percent" class="form-label">
                    Percent
                  </label>
                  <div class="input-group">
                    <input
                      type="number"
                      class="form-control"
                      id="percent"
                      step="1"
                      min="1"
                      max="100"
                      onInput={(ev) => setForm("value", ev.target.value)}
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
                options={config()?.departments || []}
                placeholder="Select department"
                onChange={(ev) => setForm("department", ev ?? "")}
                itemComponent={(props) => (
                  <Combobox.Item item={props.item}>
                    <Combobox.ItemLabel as="a" class="dropdown-item" href="#">
                      {props.item.rawValue}
                    </Combobox.ItemLabel>
                  </Combobox.Item>
                )}
              >
                <Combobox.Control class="input-group">
                  <Combobox.Input
                    class="form-control"
                    id="department"
                    required
                  />
                  <Combobox.Trigger class="btn btn-outline-secondary dropdown-toggle" />
                </Combobox.Control>
                <Combobox.Portal>
                  <Combobox.Content style={{ "z-index": 9999 }}>
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
                class="form-control size-content"
                onInput={(ev) => setForm("notes", ev.target.value)}
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
