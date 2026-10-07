"use client";

import { ReactNode } from "react";
import { usePathname } from "next/navigation";

import classNameModule from "@classname";
import styles from "./DebugMessage.module.scss";
const className = classNameModule(styles);

type DebugMessageProps = {
  children?: ReactNode;
};

/**
 * DebugMessage component for displaying debug information (in dev mode only).
 * 
 * Usage:
 * ```tsx
 * <DebugMessage>
 *   <div>Debug information</div>
 * </DebugMessage>
 * ```
 * 
 * Only displayed in dev mode.
 */
export const DebugMessage = ({ children }: DebugMessageProps) => {
  const pathname = usePathname();

  if (!pathname.includes("test")) return null;

  return (
    <div {...className("DebugMessage")}>
      <span>Debug</span>
      <div>{children}</div>
    </div>
  );
};
