import { HeadphonesIcon, SpeakerIcon } from "lucide-react";
import { sendGTMEvent } from '@next/third-parties/google'

import classNameModule from "@classname";
import styles from "./DeviceScreen.module.scss";
const className = classNameModule(styles);

type DeviceScreenProps = {
  handleNext: () => void;
};

export const DeviceScreen = ({ handleNext }: DeviceScreenProps) => {
  return (
    <div {...className("DeviceScreen")}>
      <h1>Qu{"'"}utilisez-vous pour écouter ?</h1>

      <div {...className("devices")}>
        <button
          {...className("recommended")}
          onClick={() => {
            sendGTMEvent({ event: 'test_choix_écouter' })
            localStorage.setItem("device", "headphones");
            handleNext();
          }}
        >
          <div {...className("icon")}>
            <HeadphonesIcon size={80} absoluteStrokeWidth strokeWidth={2} />
          </div>
          <div {...className("label")}>
            <div>Casque / Ecouteurs</div>

            <div {...className("recommended")}>Recommandé</div>
          </div>
        </button>
        <button
          onClick={() => {

            sendGTMEvent({ event: 'test_choix_écouter' })

            localStorage.setItem("device", "speaker");
            handleNext();
          }}
        >
          <div {...className("icon")}>
            <SpeakerIcon size={80} absoluteStrokeWidth strokeWidth={2} />
          </div>
          <div {...className("label")}>Haut-parleurs</div>
        </button>
      </div>
    </div>
  );
};
