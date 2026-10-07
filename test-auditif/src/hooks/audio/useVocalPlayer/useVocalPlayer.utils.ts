/**
 *
 */
export const timeout = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Get calibration volume from local storage.
 * Calibration volume is set by the user at the beginning.
 */
export const getVocalCalibrationVolume = () => {
  const data = localStorage.getItem("vocal-calibration-volume");
  if (!data) throw new Error("vocal-calibration-volume not found");
  return parseFloat(data);
};
