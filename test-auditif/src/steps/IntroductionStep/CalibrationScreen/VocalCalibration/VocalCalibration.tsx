import { sendGTMEvent } from "@next/third-parties/google";
import { useEffect, useRef, useState } from "react";

import { VerticalProgress } from "../VerticalProgress/VerticalProgress";
import { NextButton } from "@ui/common";
import { useAudioSystem } from "@hooks/audio";

import classNameModule from "@classname";
import styles from "./VocalCalibration.module.scss";
const className = classNameModule(styles);

type VocalCalibrationProps = {
  handleNext: () => void;
};

export const VocalCalibration = ({ handleNext }: VocalCalibrationProps) => {
  const [volume] = useState(0.25);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const audioSystem = useAudioSystem({
    audios: [
      {
        id: "noise",
        url: "/medias/vocal/noise.wav",
        canal: "default",
      },
      ...Array.from({ length: 9 }).map((_, index) => ({
        id: (index + 1).toString(),
        url: `/medias/vocal/${index + 1}.wav`,
        canal: "default",
      })),
    ],
  });

  useEffect(() => {
    audioSystem.setup().then(() => {
      audioSystem.setCanalVolume("default", 0.25);
      audioSystem.play("noise", { loop: true });

      intervalRef.current = setInterval(() => {
        const number = Math.floor(Math.random() * 9) + 1;

        audioSystem.play(number.toString());
      }, 1000);
    });

    localStorage.setItem("vocal-calibration-volume", volume.toString());

    return () => {
      audioSystem.stopAll();

      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <>
      <h1>Calibrage</h1>

      <p>
        Placez le curseur de volume de façon à entendre les chiffres prononcés
        de manière confortable.
      </p>

      {/* <CalibrationSound volume={volume} numbers /> */}
      <VerticalProgress
        initPosition={volume * 2}
        handleChange={(volume) => {
          audioSystem.setCanalVolume("default", volume / 2);

          localStorage.setItem(
            "vocal-calibration-volume",
            (volume / 2).toString()
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
