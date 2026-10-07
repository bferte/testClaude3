import { ReactNode } from "react";

import classNameModule from "@classname";
import styles from "./ThemeContext.module.scss";
const className = classNameModule(styles);

type ThemeContextProps = {
  children: ReactNode;
};

export const ThemeContext = ({ children }: ThemeContextProps) => {
  return <div {...className("ThemeContext")}>{children}</div>;
};
