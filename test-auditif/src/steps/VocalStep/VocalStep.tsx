import { useEffect, useRef, useState } from "react";

import { Progress, NextButton, DebugMessage } from "@ui/common";

import { Keyboard } from "../../ui/common/Keyboard/Keyboard";
import { pickNumbers } from "./VocalStep.utils";
import { useVocalPlayer } from "@hooks/audio";
import { useResultTyping } from "./useResultTyping";
import { StepComponentProps, VocalStep } from "../step.types";

import classNameModule from "@classname";
import styles from "./VocalStep.module.scss";
const className = classNameModule(styles);

/**
 *
 */
export const VocalStepComponent = ({
  step,
  handleNext,
}: StepComponentProps<VocalStep>) => {
  const [index, setIndex] = useState(0);
  const indexRef = useRef<number>(index);
  const [started, setStarted] = useState(false);
  const rnbRef = useRef<number>(0);
  const resultDataRef = useRef<
    {
      rnb: number;
      result: boolean;
    }[]
  >([]);

  const [RNB, setRNB] = useState(rnbRef.current);

  const vocalPlayer = useVocalPlayer();
  const resultTyping = useResultTyping(validate);

  const currentNumbersRef = useRef<[number, number, number]>([0, 0, 0]);

  useEffect(() => {
    currentNumbersRef.current = pickNumbers();
  }, []);

  return started ? (
    <div {...className("VocalStep")} data-screen="vocal-test">
      <div {...className("progress")}>
        <Progress value={index + 1} max={step.config.steps} />
      </div>

      <header>
        <div {...className("text")}>
          <div {...className("mobileStep")}>
            {index + 1} / {step.config.steps}
          </div>
          <h2>Qu{"'"}entendez-vous ?</h2>
          <p>En cas de doute, choisissez un chiffre au hasard.</p>
        </div>

        <DebugMessage>
          <div>RNB : {RNB}</div>
        </DebugMessage>

        <div {...className("Typing")}>
          <div {...className({ active: resultTyping.typing.length === 0 })}>
            {resultTyping.typing[0]}
          </div>
          <div {...className({ active: resultTyping.typing.length === 1 })}>
            {resultTyping.typing[1]}
          </div>
          <div {...className({ active: resultTyping.typing.length === 2 })}>
            {resultTyping.typing[2]}
          </div>
        </div>
      </header>
      <div {...className("keyboard")}>
        <Keyboard
          activeNumbers={resultTyping.typing.length < 3}
          activeValidateButton={resultTyping.typing.length === 3}
          handleClick={(number) => {
            resultTyping.pushNumber(number);
          }}
          handleClickDelete={resultTyping.backTyping}
          handleClickValidate={() => {
            validate();
          }}
        />
      </div>
    </div>
  ) : (
    <div style={{ margin: "auto", padding: 20 }}>
      <h1>Test vocal</h1>
      <p
        style={{
          maxWidth: 600,
          margin: "10px auto 30px auto",
        }}
      >
        Ce test évalue votre capacité à comprendre la parole dans le bruit. Vous
        allez écouter une série de chiffres sur un bruit de fond.
      </p>

      <NextButton
        big
        theme="primary"
        onClick={() => {
          setStarted(true);
          play();
        }}
        {...className("NextButton")}
      >
        Démarrer
      </NextButton>
    </div>
  );

  async function play() {
    const numbers = currentNumbersRef.current;
    await vocalPlayer.playSequence(numbers, rnbRef.current);
  }

  async function validate() {
    const success = resultTyping.typing === currentNumbersRef.current.join("");

    resultTyping.reset();

    resultDataRef.current.push({
      rnb: rnbRef.current,
      result: success,
    });

    rnbRef.current += success ? (indexRef.current < 3 ? -4 : -2) : 2;
    setRNB(rnbRef.current);
    currentNumbersRef.current = pickNumbers();
    indexRef.current++;

    // Last step
    if (indexRef.current === step.config.steps) {
      handleNext(resultDataRef.current);
      return;
    }
    setIndex(indexRef.current);
    play();
  }
};
