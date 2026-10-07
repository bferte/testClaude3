export function boundsValue(value: number, min: number, max: number) {
  return Math.max(min, Math.min(value, max));
}

/**
 * Called when the pointer is down on the root element.
 * Track movements until the pointer is up.
 */
export function trackPointerMove(callback: (clientY: number) => void) {
  function onTouchMove(e: TouchEvent) {
    e.preventDefault();
    const touch = e.touches[0];
    callback(touch.clientY);
  }

  function clean() {
    window.removeEventListener("touchmove", onTouchMove);
    window.removeEventListener("touchend", clean);
    window.removeEventListener("pointermove", onMouseMove);
    window.removeEventListener("pointerup", clean);
  }

  function onMouseMove(e: MouseEvent) {
    e.preventDefault();

    callback(e.clientY);
  }

  window.addEventListener("touchmove", onTouchMove);
  window.addEventListener("touchend", clean);
  window.addEventListener("pointermove", onMouseMove);
  window.addEventListener("pointerup", clean);
}
