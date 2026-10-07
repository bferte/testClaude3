"use client";

import { useState } from "react";

import { AccessibilityButton } from "@ui/common";

import { getStepComponent } from "@/steps/steps";
import classNameModule from "@classname";
import styles from "./page.module.scss";
import { Step } from "@/steps/step.types";
import { TestType } from "@/steps/IntroductionStep/CustomTest/CustomTest";
const className = classNameModule(styles);

export default function Home() {
  const [data, setData] = useState<any>({
    source: "shop",
  });

  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const steps = getSteps(data.introduction?.type);

  const currentStep = steps[currentStepIndex];
  const CurrentComponent = getStepComponent(currentStep.type);
  return (
    <main {...className("Page")}>
      <header>
        <AccessibilityButton />
      </header>

      <CurrentComponent
        key={currentStepIndex}
        step={currentStep}
        data={data}
        handleNext={(stepData) => {
          setData({
            ...data,
            [currentStep.type]: stepData,
          });
          setCurrentStepIndex(currentStepIndex + 1);
        }}
      />
    </main>
  );
}

const getSteps = (testType: TestType) => {
  if (testType === "tonal")
    return steps.filter((step) => step.type !== "vocal");

  if (testType === "vocal")
    return steps.filter((step) => step.type !== "tonal");

  return steps;
};

const steps: Step[] = [
  {
    type: "introduction",
    customizable: false,
    defaultType: "vocal",
    wording: "shop",
  },
  {
    type: "vocal",
    config: {
      steps: 5,
    },
  },
  {
    type: "result",
    form: false,
  },
];
