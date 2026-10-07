import { ButtonHTMLAttributes, DetailedHTMLProps, ReactNode } from "react";

import classNameModule from "@classname";
import styles from "./Button.module.scss";
const className = classNameModule(styles);

/**
 * Button component for displaying a button.
 * 
 * Usage:
 * ```tsx
 * <Button>Click me</Button>
 * ```
 * 
 * The button_id prop is used as a data-button attribute which is tracked by Google Tag Manager (GTM).
 */
export const Button = ({
  children,
  theme = "default",
  big,
  center,
  uppercase,
  className: classNameInput,
  button_id,
  ...htmlProps
}: ButtonProps) => {
  return (
    <button
      data-button={button_id}
      {...className(
        "Button",
        { theme, big, center, uppercase },
        `:${classNameInput}`
      )}
      {...htmlProps}
    >
      {children}
    </button>
  );
};

export type ButtonProps = {
  children: ReactNode;
  theme?: "default" | "outline" | "primary";
  big?: boolean;
  center?: boolean;
  uppercase?: boolean;
  button_id?: string;
} & DetailedHTMLProps<
  ButtonHTMLAttributes<HTMLButtonElement>,
  HTMLButtonElement
>;
