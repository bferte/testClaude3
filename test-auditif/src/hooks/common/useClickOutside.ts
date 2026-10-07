import { useEffect, useRef } from "react";

/**
 * Used to detect click events outside of a specified element.
 */
function useClickOutside<T extends HTMLElement>(
  callback: () => void,
  active = true
) {
  const rootRef = useRef<T>(null);

  useEffect(() => {
    const clickOutsideEvent = (event: MouseEvent) => {
      if (!active || !rootRef.current) return;
      if (!rootRef.current.contains(event.target as Node)) callback();
    };

    window.addEventListener("mousedown", clickOutsideEvent);
    window.addEventListener("blur", callback);

    return () => {
      window.removeEventListener("mousedown", clickOutsideEvent);
      window.removeEventListener("blur", callback);
    };
  }, [active, rootRef]);

  return [rootRef];
}

export default useClickOutside;
