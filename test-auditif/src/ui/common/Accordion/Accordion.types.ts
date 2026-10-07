import { ReactNode } from "react";

export type AccordionContextType = {
  openedItem: string | null;
  setOpenedItem: (id: string | null) => void;
};

export type AccordionProps = {
  children?: ReactNode;
  defaultOpenedItem?: string | null;
};

export type AccordionItemProps = {
  label?: string;
  children?: ReactNode;
  id: string;
  className?: string;
};
