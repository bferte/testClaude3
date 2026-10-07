import classNameModule from "@classname";
import styles from "./QRCodeModal.module.scss";
const className = classNameModule(styles);

import { useEffect } from "react";
import { XIcon } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

type QRCodeModalProps = {
  url: string;
  handleClose: () => void;
};

/**
 * QRCodeModal component for displaying a QR code.
 * 
 * Usage:
 * ```tsx
 * <QRCodeModal url="https://example.com" handleClose={() => {}} />
 * ```
 * 
 * The url and handleClose props are required.
 */
export const QRCodeModal = ({ url, handleClose }: QRCodeModalProps) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        handleClose();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, []);

  return (
    <div {...className("QRCodeModal")}>
      <div>
        <button onClick={handleClose} {...className("closeButton")}>
          <XIcon size={20} />
        </button>
        <QRCodeSVG value={url} />

        <div>Scannez ce QR code pour ouvrir ce test sur un autre appareil</div>
      </div>
    </div>
  );
};
