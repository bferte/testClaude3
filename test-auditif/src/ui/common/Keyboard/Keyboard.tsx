import { ReactNode, useState } from "react";
import { DeleteIcon } from "lucide-react";

import classNameModule from "@classname";
import styles from "./Keyboard.module.scss";
import { Button } from "@ui/common";
const className = classNameModule(styles);

const KEYBOARD_KEYS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

type KeyboardProps = {
  handleClick: (number: number) => void;
  handleClickDelete: () => void;
  handleClickValidate: () => void;
  activeValidateButton: boolean;
  activeNumbers: boolean;
};

/**
 * Responsive digit keyboard.
 * 
 * Usage:
 * ```tsx
 * <Keyboard
 *   handleClick={handleClick}
 *   handleClickDelete={handleClickDelete}
 *   handleClickValidate={handleClickValidate}
 *   activeValidateButton={activeValidateButton}
 *   activeNumbers={activeNumbers}
 * />
 */
export const Keyboard = ({
  handleClick,
  handleClickDelete,
  handleClickValidate,
  activeValidateButton,
  activeNumbers,
}: KeyboardProps) => (
  <div {...className("Keyboard")}>
    {KEYBOARD_KEYS.map((key) => (
      <KeyboardButton
        key={key}
        onClick={() => handleClick(key)}
        active={activeNumbers}
      >
        {key}
      </KeyboardButton>
    ))}

    <div />
    <KeyboardButton onClick={() => handleClick(0)} active={activeNumbers}>
      0
    </KeyboardButton>
    <BackspaceButton onClick={() => handleClickDelete()} />

    <Button
      {...className("ValidateButton", { active: activeValidateButton })}
      theme="primary"
      onClick={handleClickValidate}
    >
      OK
    </Button>
  </div>
);

type KeyboardButtonProps = {
  children: ReactNode;
  onClick: () => void;
  active: boolean;
};

/**
 *
 */
const KeyboardButton = ({ children, onClick, active }: KeyboardButtonProps) => {
  const [n, setN] = useState(0);
  return (
    <button
      key={n}
      {...className("KeyboardButton", { activeAnimation: n > 0, active })}
      onClick={() => {
        onClick();
        setN(n + 1);
      }}
    >
      {children}
    </button>
  );
};

type BackspaceButtonProps = {
  onClick: () => void;
};

/**
 *
 */
const BackspaceButton = ({ onClick }: BackspaceButtonProps) => (
  <button {...className("backspaceButton")} onClick={() => onClick()}>
    <DeleteIcon absoluteStrokeWidth strokeWidth={1.5} />
  </button>
);
