import { type Component, Match, Switch } from "solid-js";

import { APIError, type AttendeeOption, useFulfillOption } from "@admin/api";

export const FulfillmentButton: Component<{ option: AttendeeOption }> = (
  props,
) => {
  const fulfillOption = useFulfillOption();

  const fulfill = () => {
    fulfillOption.mutate(props.option.id, {
      onError: (err) => {
        if (err instanceof APIError) {
          alert(err.reason || "Unknown API error");
        } else {
          alert(err);
        }
      },
    });
  };

  return (
    <Switch>
      <Match
        when={props.option.requiresFulfillment && !props.option.fulfilledAt}
      >
        <button
          type="button"
          class="badge btn btn-primary text-bg-primary w-100"
          onClick={fulfill}
          disabled={fulfillOption.isPending}
        >
          Fulfill
        </button>
      </Match>
      <Match when={props.option.requiresFulfillment}>
        <button
          class="badge btn btn-secondary w-100"
          disabled
          title={`Fulfilled at ${new Date(props.option.fulfilledAt!).toLocaleString()}`}
        >
          Fulfilled
        </button>
      </Match>
    </Switch>
  );
};
