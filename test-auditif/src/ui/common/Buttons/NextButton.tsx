import classNameModule from "@classname";
import styles from "./NextButton.module.scss";
import { Button, ButtonProps } from "./Button";
import { ArrowRightIcon } from "lucide-react";
const className = classNameModule(styles);

type NextButtonProps = { button_id?: string } & ButtonProps;

export const NextButton = ({
  children,
  button_id,
  ...buttonProps
}: NextButtonProps) => {
  return (
    <Button {...className("NextButton")} {...buttonProps} button_id={button_id}>
      <span>{children}</span>
      <ArrowRightIcon size={15} absoluteStrokeWidth strokeWidth={2} />
    </Button>
  );
};
