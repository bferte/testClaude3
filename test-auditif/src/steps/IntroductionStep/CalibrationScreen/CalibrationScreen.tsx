import { useEffect, useState } from "react";

import { VocalCalibration } from "./VocalCalibration/VocalCalibration";
import { TonalCalibration } from "./TonalCalibration/TonalCalibration";

export const CalibrationScreen = ({ handleNext }: CalibrationScreenProps) => {
  const [step, setStep] = useState(0);

  const [device, setDevice] = useState<"headphones" | "speaker">("headphones");

  useEffect(() => {
    setDevice(
      (localStorage.getItem("device") ?? "headphones") as
        | "headphones"
        | "speaker"
    );
  }, []);

  if (step === 1) {
    return <TonalCalibration device={device} handleNext={handleNext} />;
  }

  return <VocalCalibration handleNext={() => handleNext()} />;
};

type CalibrationScreenProps = {
  handleNext: () => void;
};
