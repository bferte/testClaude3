"use client";

import { useState } from "react";

import { AccessibilityButton, Logo } from "@ui/common";

import { getStepComponent } from "@/steps/steps";

import { TestType } from "@/steps/IntroductionStep/CustomTest/CustomTest";
import { Step } from "@/steps/step.types";

import classNameModule from "@classname";
import styles from "./page.module.scss";
const className = classNameModule(styles);

export default function PageClient({
  params,
}: {
  params: {
    shop_id: string;
    type: string;
    user_id: string;
    session_token: string;
    agentInformation?: any;
  };
}) {
  const [data, setData] = useState<any>({
    source: params.type,
    shop_id: params.shop_id,
    user_id: params.user_id,
    type: params.type,
    session_token: params.session_token,
    agentInformation: params.agentInformation,
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

      <Logo />
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
      steps: 23,
    },
  },
  {
    type: "result",
    form: false,
  },
];
