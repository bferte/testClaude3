import { ArrowLeftIcon, AudioLinesIcon, MicIcon } from "lucide-react";
import { Dispatch, SetStateAction, useState } from "react";

import { Button } from "@ui/common";

import classNameModule from "@classname";
import styles from "./CustomTest.module.scss";
const className = classNameModule(styles);

export type TestType = "complete" | "tonal" | "vocal";
type TestVoice = "man" | "woman" | "child";

export const useTestCustomization = () => {
  const [voice, setVoice] = useState<TestVoice>("man");

  return {
    voice,
    setVoice,
  };
};

type CustomTestProps = {
  handleClose: () => void;
  type: TestType;
  setType: Dispatch<SetStateAction<TestType>>;
  voice: TestVoice;
  setVoice: Dispatch<SetStateAction<TestVoice>>;
};

/**
 *
 */
export const CustomTest = ({
  handleClose,
  type,
  setType,
  voice,
  setVoice,
}: CustomTestProps) => {
  return (
    <div {...className("CustomTest")}>
      <Button
        onClick={handleClose}
        {...className("backButton")}
        theme="outline"
      >
        <ArrowLeftIcon size={15} absoluteStrokeWidth strokeWidth={2} />
        <span>Retour</span>
      </Button>
      <div>
        <div {...className("grid")}>
          <div
            {...className({ active: type === "complete" })}
            onClick={() => setType("complete")}
          >
            <div {...className("icon")}>
              <MicIcon size={80} absoluteStrokeWidth strokeWidth={2.5} />
            </div>
            <div>Test complet</div>
          </div>
          <div
            {...className({ active: type === "tonal" })}
            onClick={() => setType("tonal")}
          >
            <div {...className("icon")}>
              <AudioLinesIcon size={80} absoluteStrokeWidth strokeWidth={2.5} />
            </div>
            <div>Test tonal</div>
          </div>
          <div
            {...className({ active: type === "vocal" })}
            onClick={() => setType("vocal")}
          >
            <div {...className("icon")}>
              <MicIcon size={80} absoluteStrokeWidth strokeWidth={2.5} />
            </div>
            <div>Test vocal</div>
          </div>
        </div>

        {/* <h2>Configuration de la voix</h2>

        <div {...className("grid", "small")}>
          <div
            {...className({ active: voice === "man" })}
            onClick={() => setVoice("man")}
          >
            <div {...className("icon")}>
              <MicIcon size={50} absoluteStrokeWidth strokeWidth={2.5} />
            </div>
            <div>Voix homme</div>
          </div>
          <div
            {...className({ active: voice === "woman" })}
            onClick={() => setVoice("woman")}
          >
            <div {...className("icon")}>
              <MicIcon size={50} absoluteStrokeWidth strokeWidth={2.5} />
            </div>
            <div>Voix femme</div>
          </div>
          <div
            {...className({ active: voice === "child" })}
            onClick={() => setVoice("child")}
          >
            <div {...className("icon")}>
              <MicIcon size={50} absoluteStrokeWidth strokeWidth={2.5} />
            </div>
            <div>Voix enfant</div>
          </div>
        </div> */}
      </div>
    </div>
  );
};
