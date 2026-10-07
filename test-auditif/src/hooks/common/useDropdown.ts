import { RefObject, useState } from "react";
import useClickOutside from "./useClickOutside";

/**
 * A helper hook to manage a dropdown menu.
 */
export function useDropdown<
  T extends HTMLElement = HTMLDivElement
>(): UseDropdownReturn<T> {
  const [isOpen, setIsOpen] = useState(false);
  const [rootRef] = useClickOutside<T>(() => setIsOpen(false), isOpen);
  return [isOpen, toggle, rootRef];

  function toggle() {
    setIsOpen((isOpen) => !isOpen);
  }
}

type UseDropdownReturn<T> = [boolean, () => void, RefObject<T>];
