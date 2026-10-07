import classNameModule from "@classname";
import styles from "./Logo.module.scss";
import Image from "next/image";
const className = classNameModule(styles);

/**
 * ATOL logo component for displaying the logo.
 * 
 * Usage:
 * ```tsx
 * <Logo />
 * ```
 */
export const Logo = () => {
  return (
    <div {...className("Logo")}>
      <Image src="/logo.png" alt="Logo" width={131} height={80} />
    </div>
  );
};
