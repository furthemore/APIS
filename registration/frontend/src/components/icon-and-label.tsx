import Fa from "solid-fa";
import { type Component, type JSX, splitProps } from "solid-js";

export type SolidFaProps = Parameters<typeof Fa>[0];

export type IconAndLabelProps = {
  children: string | JSX.Element;
} & SolidFaProps;

export const IconAndLabel: Component<IconAndLabelProps> = (props) => {
  const [labelProps, iconProps] = splitProps(props, ["children"]);

  return (
    <>
      <Fa {...iconProps} /> {labelProps.children}
    </>
  );
};
