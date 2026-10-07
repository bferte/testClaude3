import classNameModule from "@classname";
import styles from "./CenteredScreen.module.scss";
const className = classNameModule(styles);

type CenteredScreenProps = {
  children?: React.ReactNode;
  screen_id?: string;
};

/**
 * CenteredScreen component for displaying a centered screen.
 * 
 * Usage:
 * ```tsx
 * <CenteredScreen screen_id="example">
 *   <div>Example content</div>
 * </CenteredScreen>
 * ```
 * 
 * The screen_id is used as a data-screen attribute which is tracked by Google Tag Manager (GTM).
 */
export const CenteredScreen = ({
  children,
  screen_id,
}: CenteredScreenProps) => {
  return (
    <div {...className("CenteredScreen")} data-screen={screen_id}>
      {children}
    </div>
  );
};
