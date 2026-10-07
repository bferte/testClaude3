"use client";

import { useState } from "react";

import { AccessibilityButton, Logo } from "@ui/common";

import { getStepComponent } from "@/steps/steps";

import { TestType } from "@/steps/IntroductionStep/CustomTest/CustomTest";
import { Step } from "@/steps/step.types";


import classNameModule from "@classname";
import styles from "./page.module.scss";
const className = classNameModule(styles);

const ALLOWED_SHOP_IDS = [
  "ATO300901",
  "ATO301601",
  "ATO302501",
  "ATO303501",
  "ATO304901",
  "ATO306201",
  "ATO306301",
  "ATO518801",
  "ATO294901",
  "ATO265001",
  "ATO206103",
  "ATO206101",
  "ATO515601",
  "ATO293801",
  "ATO502801",
  "ATO083001",
  "ATO518801",
  "ATO300601",
  "ATO300901",
  "ATO301101",
  "ATO301201",
  "ATO301301",
  "ATO301402",
  "ATO301501",
  "ATO301601",
  "ATO302001",
  "ATO302201",
  "ATO302501",
  "ATO302601",
  "ATO302701",
  "ATO302801",
  "ATO302901",
  "ATO303001",
  "ATO303101",
  "ATO303501",
  "ATO303502",
  "ATO303601",
  "ATO303801",
  "ATO303901",
  "ATO304001",
  "ATO304101",
  "ATO304301",
  "ATO304302",
  "ATO304401",
  "ATO304501",
  "ATO304502",
  "ATO304503",
  "ATO304504",
  "ATO304505",
  "ATO304506",
  "ATO304601",
  "ATO304701",
  "ATO304801",
  "ATO304901",
  "ATO305001",
  "ATO305101",
  "ATO305201",
  "ATO305401",
  "ATO305501",
  "ATO305601",
  "ATO305701",
  "ATO305901",
  "ATO306001",
  "ATO306101",
  "ATO306201",
  "ATO306301",
  "ATO306302",
  "ATO306401",
  "ATO306501",
  "ATO306601",
  "ATO306701",
  "ATO306801",
  "ATO306901",
  "ATO307001",
  "ATO307101",
  "ATO307401",
  "ATO300901",
  "ATO272001",
  "ATO513901",
  "ATO514001",
  "ATO510901",
  "ATO294901",
  "ATO261901",
  "ATO509901",
  "ATO265001",
  "ATO294601",
  "ATO517901",
  "ATO519701",
  "ATO286301",
  "ATO262101",
  "ATO295601",
  "ATO277001",
  "ATO228001",
  "ATO512101",
  "ATO089101",
  "ATO089105",
  "ATO089106",
  "ATO089102",
  "ATO089108",
  "ATO089114",
  "ATO510301",
  "ATO277501",
  "ATO260801",
  "ATO511201",
  "ATO298601",
  "ATO525701",
  "ATO292501",
  "ATO256503",
  "ATO297301",
  "ATO527001",
  "ATO526201",
  "ATO293801",
  "ATO502801",
  "ATO514701",
  "ATO220202",
  "ATO236801",
  "ATO528401",
  "ATO271701",
  "ATO528001",
  "ATO228201",
  "ATO206103",
  "ATO206102",
  "ATO206101",
  "ATO400101",
  "ATO507901",
  "ATO298701",
  "ATO510501",
];

export default function Home({ params }: { params: { shop_id: string } }) {
  const [data, setData] = useState<any>({
    source: params.shop_id,
  });

  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const steps = getSteps(data.introduction?.type);

  const currentStep = steps[currentStepIndex];
  const CurrentComponent = getStepComponent(currentStep.type);

  // if (!ALLOWED_SHOP_IDS.includes(params.shop_id))
  //   return (
  //     <div {...className("NotAllowed")}>
  //       <div>
  //         <p>
  //           Vous souhaitez développer l’audition dans votre magasin d’optique ?
  //           Veuillez contacter le service Atol Audition au{" "}
  //           <a href="tel:0345046024">03 45 04 60 24</a>
  //         </p>
  //       </div>
  //     </div>
  //   );

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
