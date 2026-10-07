"use client";

import { useState } from "react";

import { Button } from "@ui/common";
import { AudioGenerator, useAudioGenerator } from "@ui/test";

import classNameModule from "@classname";
import styles from "./AudioTest.module.scss";
const className = classNameModule(styles);

/**
 * AudioTest component for testing the audio.
 * 
 * Usage:
 * ```tsx
 * <AudioTest />
 * ```
 */
export const AudioTest = ({ }: AudioTestProps) => {
  const [currentSound, setCurrentSound] = useState(0);
  const audioGenerator = useAudioGenerator();
  const currentStep = steps[currentSound];

  return (
    <div {...className("AudioTest")}>
      <h1>Test audio</h1>
      <AudioGenerator
        key={currentSound}
        ref={audioGenerator.ref}
        frequency={currentStep.frequency}
        volume={0.5}
        autoPlay
        side="both"
      />

      <div {...className("actions")}>
        <Button onClick={() => handleNext(true)}>J{"'"}entend</Button>
        <Button onClick={() => handleNext(false)}>Je n{"'"}entend pas</Button>
      </div>
    </div>
  );

  function handleNext(result: boolean) {
    setCurrentSound(currentSound + 1);
  }
};

type AudioTestProps = {};

const steps = [
  {
    frequency: 500,
  },
  {
    frequency: 1000,
  },
  {
    frequency: 4000,
  },
];
