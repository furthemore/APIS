import {
  type Accessor,
  type Component,
  type JSX,
  Show,
  splitProps,
  useContext,
} from "solid-js";

import { type AttendeeDetails, useGetToken } from "@admin/api";
import { ConfigContext } from "@admin/providers/config-provider";
import { MqttContext } from "@admin/providers/mqtt-provider";

export const DisplayRegistrationButton: Component<
  {
    children: JSX.Element;
    details?: Accessor<AttendeeDetails>;
  } & JSX.IntrinsicElements["button"]
> = (props) => {
  const config = useContext(ConfigContext)!;
  const mqtt = useContext(MqttContext)!;

  const regToken = useGetToken();

  const isLoading = () => regToken.isPending;

  const [customProps, buttonProps] = splitProps(props, ["children", "details"]);

  const display = async () => {
    const resp = await regToken.mutateAsync();

    mqtt()?.displayRegistration(resp.token, props.details?.() || {});
  };

  return (
    <Show when={config()?.terminals.selected?.features.prompt}>
      <button
        type="button"
        {...buttonProps}
        classList={{ "is-loading": isLoading() }}
        onClick={() => display()}
      >
        {customProps.children}
      </button>
    </Show>
  );
};
