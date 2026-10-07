import { CheckIcon } from "lucide-react";

import classNameModule from "@classname";
import styles from "./Checkbox.module.scss";
const className = classNameModule(styles);

type CheckboxProps = {
  checked: boolean;
};

/**
 * 
 * Checkbox component for selecting options.
 * 
 * Usage:
 * ```tsx
 * <Checkbox checked={true} />
 * ```
 * 
 * Click should be managed by the parent component.
 * 
 */
export const Checkbox = ({ checked }: CheckboxProps) => (
  <div {...className("Checkbox", { checked })}>
    <CheckIcon size={15} strokeWidth={3} />
  </div>
);
