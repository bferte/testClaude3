"use client";

import { useEffect, useState } from "react";
import { ChevronDownIcon, ContrastIcon, QrCodeIcon, XIcon } from "lucide-react";

import { Button, useAccessibilityContext } from "@ui/common";
import { QRCodeSVG } from "qrcode.react";
import { useDropdown } from "@hooks/common";

import { Checkbox } from "../Checkbox/Checkbox";

import classNameModule from "@classname";
import styles from "./AccessibilityButton.module.scss";
const className = classNameModule(styles);

type AccessibilityButtonProps = {
  hideQRCode?: boolean;
};

export const AccessibilityButton = ({
  hideQRCode = false,
}: AccessibilityButtonProps) => {
  const [isOpen, toggleDropdown, rootRef] = useDropdown();

  const [isQRCodeModalOpen, toggleQRCodeModal] = useState(false);

  return (
    <div {...className("AccessibilityButton")} ref={rootRef}>
      {isQRCodeModalOpen && (
        <QRCodeModal handleClose={() => toggleQRCodeModal(false)} />
      )}
      {!hideQRCode && (
        <Button
          onClick={() => toggleQRCodeModal(true)}
          {...className("QRCodeButton")}
        >
          <QrCodeIcon size={16} absoluteStrokeWidth strokeWidth={1.5} />
          <span>Afficher le QR code</span>
        </Button>
      )}
      <Button onClick={() => toggleDropdown()}>
        <ContrastIcon size={16} />
        <span>Accessibilité</span>
        <ChevronDownIcon size={16} />
      </Button>

      {isOpen && <Dropdown />}
    </div>
  );
};

type QRCodeModalProps = {
  handleClose: () => void;
};

const QRCodeModal = ({ handleClose }: QRCodeModalProps) => {
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
        <QRCodeSVG value={window.location.href} />

        <div>Scannez ce QR code pour ouvrir ce test sur un autre appareil</div>
      </div>
    </div>
  );
};

const Dropdown = () => {
  const { dyslexic, inversedContrast, largFonts, setAccessibilityData } =
    useAccessibilityContext();

  return (
    <div {...className("Dropdown")}>
      <Button
        data-button="dyslexic"
        onClick={() => {
          setAccessibilityData((accessibilityData) => ({
            ...accessibilityData,
            dyslexic: !accessibilityData.dyslexic,
          }));
        }}
      >
        <Checkbox checked={dyslexic} />
        <span>Police dyslexie</span>
      </Button>
      <Button
        data-button="inversed-contrast"
        onClick={() => {
          setAccessibilityData((accessibilityData) => ({
            ...accessibilityData,
            inversedContrast: !accessibilityData.inversedContrast,
          }));
        }}
      >
        <Checkbox checked={inversedContrast} />
        <span>Constraste inversé</span>
      </Button>
      <Button
        data-button="large-fonts"
        onClick={() => {
          setAccessibilityData((accessibilityData) => ({
            ...accessibilityData,
            largFonts: !accessibilityData.largFonts,
          }));
        }}
      >
        <Checkbox checked={largFonts} />
        <span>Grande police</span>
      </Button>
    </div>
  );
};
