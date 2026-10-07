export type StepComponentProps<TStep extends Step> = {
  data: any;
  step: TStep;
  handleNext: (data: Record<string, any>) => void;
};

export type Step =
  | IntroductionStep
  | QuestionsStep
  | TonalStep
  | VocalStep
  | PersonalInformationsStep
  | ResultStep;

export type PersonalInformationsStep = {
  type: "personalInformations";
};

export type IntroductionStep = {
  type: "introduction";
  customizable?: boolean;
  defaultType?: "complete" | "tonal" | "vocal";
  wording: "shop" | "online";
  agentInformation?: any;
};

export type QuestionsStep = {
  type: "questions";
  config: {
    questions: { id: string; content: string; image?: string }[];
  };
};

export type TonalStep = {
  type: "tonal";
  config: {
    frequencies: number[];
  };
};

export type VocalStep = {
  type: "vocal";
  config: {
    steps: number;
  };
};

export type ResultStep = {
  type: "result";
  form: boolean;
};

export type ResultData = {
  introduction: {
    gender: "female" | "male";
    birthyear: number;
  };
  questions: {
    id: string;
    result: boolean;
  }[];
  tonal: {
    frequency: number;
    result: {
      volume: number;
      result: boolean;
    }[];
  }[];
  personalInformations: {
    firstname: string;
    lastname: string;
    email: string;
    phone: string;
  };
  vocal: {
    rnb: number;
    result: boolean;
  }[];
};
