import classNameModule from "@classname";
import styles from "./ScreenLayout.module.scss";
import { ReactNode } from "react";
const className = classNameModule(styles);

/**
 * ScreenLayout component for displaying a screen with content and buttons.
 * 
 * Usage:
 * ```tsx
 * <ScreenLayout>
 *   <div>Content</div>
 *   <div>Buttons</div>
 * </ScreenLayout>
 * ```
 * 
 * The screen_id is used as a data-screen attribute which is tracked by Google Tag Manager (GTM).
 */
export const ScreenLayout = ({ children, buttons, screen_id }: ScreenLayoutProps) => {
  return (
    <div {...className("ScreenLayout")} data-screen={screen_id}>
      <div {...className("content")}>{children}</div>
      <div {...className("buttons")}>{buttons}</div>
    </div>
  );
};

type ScreenLayoutProps = {
  children?: ReactNode;
  buttons?: ReactNode;
  screen_id?: string
};
