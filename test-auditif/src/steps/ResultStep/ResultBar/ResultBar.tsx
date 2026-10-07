import classNameModule from "@classname";
import styles from "./ResultBar.module.scss";
import { ChevronDownIcon } from "lucide-react";
const className = classNameModule(styles);

type ResultBarProps = {
  notation: string;
};

export const ResultBar = ({ notation }: ResultBarProps) => {
  return (
    <div {...className("ResultBar")}>
      {["bad", "medium", "good"].map((resultNotation) => (
        <div
          key={resultNotation}
          {...className(resultNotation, {
            active: notation === resultNotation,
          })}
        >
          {notation === resultNotation && (
            <div {...className("cursor")}>
              <ChevronDownIcon size={30} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
