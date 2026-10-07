
import { sendGTMEvent } from '@next/third-parties/google'

import Image from "next/image";
import { useRef, useState } from "react";

import { QuestionsStep, StepComponentProps } from "../step.types";
import { Button, Progress, ScreenLayout } from "@ui/common";

import classNameModule from "@classname";
import styles from "./QuestionsStep.module.scss";
const className = classNameModule(styles);

export const QuestionsStepComponent = ({
  step: {
    config: { questions },
  },
  handleNext,
}: StepComponentProps<QuestionsStep>) => {
  const [index, setIndex] = useState(0);
  const resultRef = useRef<
    Array<{ id: string; text: string; result: boolean }>
  >([]);

  return (
    <>
      <div {...className("progress")}>
        <Progress value={index + 1} max={questions.length} />

        <div {...className("progressLabel")}>
          Question {Math.min(questions.length, index + 1)} sur{" "}
          {questions.length}
        </div>
      </div>
      <ScreenLayout
        screen_id="questions"
        buttons={
          <>
            <Button
              button_id="yes"
              big
              theme="primary"
              onClick={() => {
                sendGTMEvent({ event: `test_question_${index + 1}` })
                handleNextQuestion(true)
              }}
            >
              Oui
            </Button>
            <Button
              button_id="no"
              big
              theme="primary"
              onClick={() => {
                sendGTMEvent({ event: `test_question_${index + 1}` })
                handleNextQuestion(false)
              }}
            >
              Non
            </Button>
          </>
        }
      >
        {questions[index]?.image && (
          <Image
            {...className("image")}
            width={920}
            height={500}
            src={questions[index]?.image}
            alt=""
            style={{
              objectFit: "cover",
            }}
          />
        )}
        <div
          {...className("question")}
          key={index}
          data-question={questions[index]?.content}
        >
          {questions[index]?.content}
        </div>
      </ScreenLayout>
    </>
  );

  function handleNextQuestion(result: boolean) {
    resultRef.current.push({
      id: questions[index]!.id,
      text: questions[index]?.content,
      result,
    });

    if (index === questions.length - 1) {
      handleNext(resultRef.current);
    }

    setIndex(index + 1);
  }
};
