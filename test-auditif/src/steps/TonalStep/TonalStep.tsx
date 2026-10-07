import { sendGTMEvent } from '@next/third-parties/google'

import { useEffect, useRef, useState } from "react";
import { Volume2Icon } from "lucide-react";

import { Button, Progress, NextButton, ScreenLayout } from "@ui/common";
import { AudioGenerator, AudioWave } from "@ui/test";

import { StepComponentProps, TonalStep } from "../step.types";

import { getVocalCalibrationVolume } from "@hooks/audio";

import classNameModule from "@classname";
import styles from "./TonalStep.module.scss";
const className = classNameModule(styles);

export const TonalStepComponent = ({
  step,
  handleNext,
}: StepComponentProps<TonalStep>) => {
  const [currentFrequencyIndex, setCurrentFrequencyIndex] = useState<
    number | null
  >(null);

  const calibrationVolumeRef = useRef(0);

  const [currentSide, setCurrentSide] = useState<"left" | "right" | "both">(
    "left"
  );

  useEffect(() => {
    calibrationVolumeRef.current = getVocalCalibrationVolume();
  }, []);

  useEffect(() => {
    const device = localStorage.getItem("device");
    setCurrentSide(device === "headphones" ? "left" : "both");
  }, []);

  const dataRef = useRef<
    {
      frequency: number;
      result: boolean[];
      side: "left" | "right" | "both";
    }[]
  >([]);

  return (
    <>
      {currentFrequencyIndex === null ? (
        <div style={{ margin: "auto", padding: 20 }} data-screen="tonal-test">
          <h1>Test Tonal</h1>

          <p style={{ marginBottom: 30, maxWidth: 600 }}>
            Ce test évalue votre audition en vous faisant écouter des sons de
            différentes fréquences (graves à aigus) et intensités (faibles à
            fortes).
          </p>

          <div style={{ display: "flex" }}>
            <NextButton
              button_id="start-test"
              big
              theme="primary"
              onClick={() => {
                sendGTMEvent({ event: 'test_tonal_start' })
                setCurrentFrequencyIndex(0);
              }}
              {...className("NextButton")}
            >
              Démarrer
            </NextButton>
          </div>
        </div>
      ) : (
        <>
          <div {...className("progress")}>
            <Progress
              value={
                currentFrequencyIndex +
                1 +
                (currentSide === "right" ? step.config.frequencies.length : 0)
              }
              max={
                step.config.frequencies.length *
                (currentSide === "both" ? 1 : 2)
              }
            />

            {currentSide !== "both" && (
              <div>Oreille {currentSide === "left" ? "gauche" : "droite"}</div>
            )}
          </div>

          <FrequencyTest
            key={currentFrequencyIndex}
            side={currentSide}
            calibrationVolume={calibrationVolumeRef.current}
            frequency={step.config.frequencies[currentFrequencyIndex]}
            handleNext={(result) => {
              dataRef.current.push({
                frequency: step.config.frequencies[currentFrequencyIndex],
                result,
                side: currentSide,
              });

              if (
                currentFrequencyIndex ===
                step.config.frequencies.length - 1
              ) {
                if (currentSide === "left") {
                  setCurrentSide("right");

                  setCurrentFrequencyIndex(0);
                } else {
                  handleNext(dataRef.current);
                }

                return;
              }

              setCurrentFrequencyIndex(currentFrequencyIndex + 1);
            }}
          />
        </>
      )}
    </>
  );
};

type FrequencyTestProps = {
  frequency: number;
  handleNext: (result: any) => void;
  side: "left" | "right" | "both";
  calibrationVolume: number;
};

const FrequencyTest = ({
  side,
  frequency,
  handleNext,
  calibrationVolume,
}: FrequencyTestProps) => {
  const [volume, setVolume] = useState(4);
  const dataRef = useRef<boolean[]>([]);

  return (
    <ScreenLayout
      buttons={
        <>
          <Button
            big
            theme="primary"
            onClick={() => {
              handleClick(true)
            }}
            button_id="yes"
          >
            Oui
          </Button>
          <Button
            big
            theme="primary"
            onClick={() => {
              handleClick(false)
            }}
            button_id="no"
          >
            Non
          </Button>
        </>
      }
    >
      <div {...className("FrequencyTest")}>
        <h1>Entendez-vous le son ?</h1>
        <div {...className("animation")}>
          <AudioWave />
        </div>
        <AudioGenerator
          frequency={frequency}
          volume={(volume * calibrationVolume) / 5}
          autoPlay
          key={volume}
          side={side}
        />
        <div {...className("volume")}>
          <Volume2Icon size={30} />

          {Array.from({ length: 7 }).map((_, index) => (
            <div key={index} {...className({ active: volume >= index + 1 })}>
              <span></span>
            </div>
          ))}
        </div>
      </div>
    </ScreenLayout>
  );

  function handleClick(result: boolean) {
    dataRef.current.push(result);

    if (new Set(dataRef.current).size === 2 || volume <= 1 || volume >= 7) {
      sendGTMEvent({ event: 'test_tonal_during' })
      handleNext(dataRef.current);
      return;
    }

    if (result) {
      setVolume(volume - 1);
    } else {
      setVolume(volume + 1);
    }
  }
};
