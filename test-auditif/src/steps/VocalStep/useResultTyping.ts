import { useEffect, useState } from "react";

/**
 * Manage result typing during vocal test.
 */
export function useResultTyping(handleEnter: () => void) {
  const [typing, setTyping] = useState("");

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const NUMBERS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

      if (NUMBERS.includes(e.key)) pushNumber(Number(e.key));

      if (e.key === "Backspace") {
        setTyping((typing) => typing.slice(0, -1));
      }

      if (e.key === "Enter") {
        e.preventDefault();
        if (typing.length === 3) handleEnter();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [typing]);

  function pushNumber(number: number) {
    setTyping((typing) => {
      if (typing.length === 3) return typing;

      return typing + number;
    });
  }

  return {
    typing,
    pushNumber,
    backTyping: () => setTyping((typing) => typing.slice(0, -1)),
    reset: () => setTyping(""),
  };
}
