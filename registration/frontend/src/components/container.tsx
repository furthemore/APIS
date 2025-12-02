import { type Component, type JSX, useContext } from "solid-js";

import { UserSettingsContext } from "../admin/providers/user-settings-provider";

export const Container: Component<{
  children: JSX.Element;
}> = (props) => {
  const settings = useContext(UserSettingsContext);

  const isFluid = () => settings?.().settings().containerFluid;
  const containerClasses = () => (isFluid() ? "container-fluid" : "container");

  return <div class={containerClasses()}>{props.children}</div>;
};
