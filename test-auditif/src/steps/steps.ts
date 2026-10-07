import { Step, StepComponentProps } from "./step.types";

import { TonalStepComponent } from "./TonalStep/TonalStep";
import { VocalStepComponent } from "./VocalStep/VocalStep";
import { ResultStepComponent } from "./ResultStep/ResultStep";
import { QuestionsStepComponent } from "./QuestionsStep/QuestionsStep";
import { IntroductionStepComponent } from "./IntroductionStep/IntroductionStep";
import { PersonalInformationsStep } from "./PersonalInformationsStep/PersonalInformationsStep";

const stepsMap: Record<
  Step["type"],
  React.ComponentType<StepComponentProps<any>>
> = {
  tonal: TonalStepComponent,
  vocal: VocalStepComponent,
  result: ResultStepComponent,
  questions: QuestionsStepComponent,
  introduction: IntroductionStepComponent,
  personalInformations: PersonalInformationsStep,
};

export const getStepComponent = (
  type: Step["type"]
): React.ComponentType<StepComponentProps<any>> => {
  return stepsMap[type];
};
