/**
 *
 * oscillator -> gain -> destination
 */
export const generateOscillator = (
  frequency: number,
  volume: number,
  side: "left" | "right" | "both"
) => {
  const context = new AudioContext();

  const gain = context.createGain();
  gain.gain.value = Math.pow(volume, 2);
  const panner = context.createStereoPanner();
  panner.pan.value = side === "left" ? -1 : side === "both" ? 0 : 1;

  gain.connect(panner);
  panner.connect(context.destination);

  const oscillator = context.createOscillator();
  oscillator.connect(gain);
  oscillator.type = "sine";
  oscillator.frequency.value = frequency;
  oscillator.start();

  return { oscillator, gain, panner };
};
