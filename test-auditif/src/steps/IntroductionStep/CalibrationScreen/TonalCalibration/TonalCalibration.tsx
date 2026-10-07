import { useEffect, useState } from "react";
import { NextButton } from "@ui/common";
import { sendGTMEvent } from '@next/third-parties/google'

import { VerticalProgress } from "../VerticalProgress/VerticalProgress";

import { useAudioSystem } from "@hooks/audio";

type TonalCalibrationProps = {
  handleNext: () => void;
  device: "headphones" | "speaker";
};

export const TonalCalibration = ({
  handleNext,
  device,
}: TonalCalibrationProps) => {
  const [step, setStep] = useState(0);

  if (step === 3) {
    return <TonalMinimalStep handleNext={() => handleNext()} side="right" />;
  }

  if (step === 2) {
    return <TonalConfortStep handleNext={() => setStep(3)} side="right" />;
  }

  if (step === 1)
    return (
      <TonalMinimalStep
        handleNext={() => (device === "headphones" ? setStep(2) : handleNext())}
        side={device === "headphones" ? "left" : "both"}
      />
    );

  return (
    <TonalConfortStep
      handleNext={() => setStep(1)}
      side={device === "headphones" ? "left" : "both"}
    />
  );
};

type TonalConfortStep = {
  handleNext: () => void;
  side: "left" | "right" | "both";
};

const TonalConfortStep = ({ handleNext, side }: TonalConfortStep) => {
  const audioSystem = useAudioSystem({
    audios: [
      {
        id: "noise",
        url: "/medias/vocal/noise.wav",
        canal: "default",
      },
    ],
  });

  useEffect(() => {
    audioSystem.setup().then(() => {
      audioSystem.setCanalVolume("default", 0.25);
      audioSystem.play("noise", { loop: true });
    });

    localStorage.setItem(`tonal-calibration-confort-${side}-volume`, "0.25");

    return () => {
      audioSystem.stopAll();
    };
  }, []);

  return (
    <>
      <h1>Calibrage</h1>

      <p>Réglez le volume à un niveau confortable.</p>

      <VerticalProgress
        initPosition={0.5}
        handleChange={(volume) => {
          audioSystem.setCanalVolume("default", volume / 2);
          localStorage.setItem(
            `tonal-calibration-confort-${side}-volume`,
            volume.toString()
          );
        }}
      />

      <NextButton
        onClick={() => {
          sendGTMEvent({ event: 'test_calibrage' })
          handleNext();
        }}
        big
        theme="primary"
      >
        Suivant
      </NextButton>
    </>
  );
};

type TonalMinimalStepStep = {
  handleNext: () => void;
  side: "left" | "right" | "both";
};
const TonalMinimalStep = ({ handleNext, side }: TonalMinimalStepStep) => {
  const [volume, setVolume] = useState(0.5);

  useEffect(() => {
    localStorage.setItem(
      `tonal-calibration-min-${side}-volume`,
      volume.toString()
    );
  }, []);

  return (
    <>
      <h1>Calibrage</h1>
      <p>Réglez le volume au plus bas niveau audible.</p>

      <VerticalProgress
        initPosition={volume}
        handleChange={(volume) => {
          setVolume(volume);
          localStorage.setItem(
            `tonal-calibration-min-${side}-volume`,
            volume.toString()
          );
        }}
      />

      <NextButton
        onClick={() => {
          sendGTMEvent({ event: 'test_calibrage' })
          handleNext();
        }}
        big
        theme="primary"
      >
        Suivant
      </NextButton>
    </>
  );
};
