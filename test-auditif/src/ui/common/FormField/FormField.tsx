import classNameModule from "@classname";
import styles from "./FormField.module.scss";
import { ReactNode } from "react";
const className = classNameModule(styles);

type FormFieldProps = {
  label?: string;
  children?: ReactNode;
};

/**
 * FormField component for displaying a label and a child component.
 * 
 * Usage:
 * ```tsx
 * <FormField label="Label">
 *   <div>Content</div>
 * </FormField>
 * ```
 * 
 * Manage margin to simplify the layout of the parent component.
 * 
 */
export const FormField = ({ label, children }: FormFieldProps) => {
  return (
    <div {...className("FormField")}>
      {label && <div {...className("label")}>{label}</div>}

      {children}
    </div>
  );
};
