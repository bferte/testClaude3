import { useEffect, useRef } from "react";

import { boundsValue, trackPointerMove } from "./VerticalProgress.utils";

import classNameModule from "@classname";
import styles from "./VerticalProgress.module.scss";
const className = classNameModule(styles);

type VerticalProgressProps = {
  initPosition: number;
  handleChange: (volume: number) => void;
};

/**
 * Set a value between 0 and 1.
 * Initial value is 0.
 */
export const VerticalProgress = ({
  initPosition,
  handleChange,
}: VerticalProgressProps) => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    moveCursorAtRatio(initPosition);
  }, []);

  return (
    <div {...className("VerticalProgressContainer")}>
      <div
        {...className("VerticalProgress")}
        ref={rootRef}
        onMouseDown={(e) => {
          e.preventDefault();

          trackPointerMove(moveCursor);
        }}
        onClick={(e) => moveCursor(e.clientY)}
        onTouchStart={(e) => {
          e.preventDefault();
          trackPointerMove(moveCursor);
        }}
      >
        <div ref={cursorRef} />
      </div>
    </div>
  );

  /**
   *
   */
  function getPositionCurrentValue(clientY: number) {
    const rootElement = rootRef.current;
    const cursorElement = cursorRef.current;
    if (!rootElement || !cursorElement) return 0;

    // User cursor corresponds to the center of the progress bar cursor.
    // Then we substract the cursor height/2 to contain the cursor inside the progress bar.
    const startPosition =
      rootElement.getBoundingClientRect().top +
      cursorElement.getBoundingClientRect().height / 2;

    // We substract the cursor height to contain the cursor inside the progress bar.
    const maxHeight =
      rootElement.getBoundingClientRect().height -
      cursorElement.getBoundingClientRect().height;

    const ratio =
      boundsValue(clientY - startPosition, 0, maxHeight) / maxHeight;

    return 1 - ratio;
  }

  /**
   *
   */
  function moveCursorAtRatio(ratio: number) {
    const cursorElement = cursorRef.current;
    if (!cursorElement) return;

    cursorElement.style.top = `${getCursorPositionForRatio(ratio)}px`;
  }

  /**
   * Compute real cursor position from ratio.
   */
  function getCursorPositionForRatio(ratio: number) {
    const rootElement = rootRef.current;
    const cursorElement = cursorRef.current;
    if (!rootElement || !cursorElement) return 0;

    // We substract the cursor height to contain the cursor inside the progress bar.
    const maxHeight =
      rootElement.getBoundingClientRect().height -
      cursorElement.getBoundingClientRect().height;

    return maxHeight * (1 - ratio);
  }

  function moveCursor(clientY: number) {
    const currentValue = getPositionCurrentValue(clientY);

    moveCursorAtRatio(currentValue);
    handleChange(currentValue);
  }
};
