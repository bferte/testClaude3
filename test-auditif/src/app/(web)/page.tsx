"use client";

import { useState } from "react";

import { AccessibilityButton, Logo } from "@ui/common";

import { Step } from "@/steps/step.types";
import { getStepComponent } from "@/steps/steps";
import { TestType } from "@/steps/IntroductionStep/CustomTest/CustomTest";

import classNameModule from "@classname";
import styles from "./page.module.scss";
const className = classNameModule(styles);

export default function Home() {
  const [data, setData] = useState<any>({
    source: "web",
  });

  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const steps = getSteps(data.introduction?.type);
  const currentStep = steps[currentStepIndex];
  const CurrentComponent = getStepComponent(currentStep.type);

  return (
    <main {...className("Page")}>
      <header>
        <AccessibilityButton hideQRCode />
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
    defaultType: "tonal",
    wording: "online",
  },
  {
    type: "questions",
    config: {
      questions: [
        {
          id: "1",
          content:
            "Avez-vous la sensation que les gens marmonnent/ chuchotent  lorsqu’ils parlent ?",
          image: "/medias/images/1.jpg",
        },
        {
          id: "2",
          content:
            "Votre entourage vous fait-il remarquer que le son de votre télévision est élevé ?",
          image: "/medias/images/7.jpg",
        },
        {
          id: "3",
          content: "Faites-vous souvent répéter vos proches ?",
          image: "/medias/images/8.jpg",
        },
        {
          id: "4",
          content:
            "Avez-vous besoin d’être face à la personne quand elle vous parle ?",
          image: "/medias/images/2.jpg",
        },
        {
          id: "5",
          content:
            "Avez-vous du mal à suivre une conversation lorsque vous êtes dans un environnement bruyant (restaurant, repas de famille, dans la rue) ?",
          image: "/medias/images/4.jpg",
        },
      ],
    },
  },
  {
    type: "tonal",
    config: {
      frequencies: [500, 1000, 4000],
    },
  },
  {
    type: "vocal",
    config: {
      steps: 12,
    },
  },
  {
    type: "result",
    form: true,
  },

  {
    type: "personalInformations",
  },
];
