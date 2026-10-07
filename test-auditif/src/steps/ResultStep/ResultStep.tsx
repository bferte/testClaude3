import { sendGTMEvent } from '@next/third-parties/google'
import Image from "next/image";
import { Button, DebugMessage } from "@ui/common";
import { PhoneIcon, PinIcon, RefreshCcwIcon } from "lucide-react";
import { computeScore } from "./ResultStep.utils";
import { ResultStep, StepComponentProps } from "../step.types";
import { useEffect, useState } from "react";
import { pushResult } from "@/database/push-result";
import { useParams, useRouter } from "next/navigation";

import Cookies from "js-cookie";

import { ResultContactForm } from "./ResultContactForm/ResultContactForm";

// import { ResultBar } from "./ResultBar/ResultBar";
import classNameModule from "@classname";
import styles from "./ResultStep.module.scss";
const className = classNameModule(styles);

export const ResultStepComponent = ({
  data,
  step,
  handleNext,
}: StepComponentProps<ResultStep>) => {
  const notation: string = computeScore(data);

  // null while the result is being saved, undefined if saving failed.
  const [resultToken, setResultToken] = useState<string | null | undefined>(
    null
  );

  const params = useParams<{
    shop_id: string;
    user_id: string;
  }>();

  useEffect(() => {
    sendGTMEvent({ event: 'thank_you_page_test' })
  }, [])

  useEffect(() => {
    if (data.session_token) {
      Cookies.set(data.session_token, "true", {
        expires: 365,
      });
    }

    pushResult(data, data.source, data.user_id, data.shop_id, {
      lastname: data.introduction?.lastname,
      firstname: data.introduction?.firstname,
    })
      .then(({ resultToken }) => setResultToken(resultToken))
      .catch(() => setResultToken(undefined));
  }, []);

  return (
    <div {...className("ResultStepComponent")} data-screen="result">
      <div {...className("image")}>
        <Image
          src="/medias/images/2.jpg"
          alt=""
          objectFit="cover"
          layout="fill"
          style={{ width: "100%", height: "100%" }}
        />

        {params?.shop_id && (
          <Button
            {...className("newSession")}
            theme="default"
            onClick={() => {
              window.location.reload();
            }}
            button_id="new-test"
          >
            <RefreshCcwIcon size={15} />
            <span>Nouveau test</span>
          </Button>
        )}
      </div>

      <div {...className("content")}>
        <div></div>
        <div {...className("result")}>
          <h1>Merci d{"'"}avoir réalisé notre test</h1>

          {/* <ResultBar notation={notation} /> */}

          <DebugMessage>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </DebugMessage>

          {notation === "bad" ? (
            <p {...className("resultText", notation)}>
              Les résultats du test semblent indiquer que vous avez une perte
              auditive importante.
            </p>
          ) : notation === "medium" ? (
            <p {...className("resultText", notation)}>
              Les résultats du test semblent indiquer que votre audition soit
              fragile.
              <br />
              Il est possible que vous présentiez une perte auditive.
            </p>
          ) : (
            <p {...className("resultText", notation)}>
              Les résultats du test semblent indiquer que votre audition est{" "}
              <strong>normale</strong>.
            </p>
          )}

          {notation === "medium" ? (
            <p>
              La perte auditive est un phénomène normal et peut être améliorée
              facilement, nos audioprothésistes diplômés d’Etat sont là pour
              vous accompagner et choisir la solution adaptée à vos besoins.
            </p>
          ) : notation === "bad" ? (
            <p>
              La perte auditive est un phénomène normal et peut être améliorée
              facilement, nos audioprothésistes diplômés d’Etat sont là pour
              vous accompagner et choisir la solution adaptée à vos besoins.
            </p>
          ) : null}

          <h2>Conseils</h2>

          <p>
            {notation === "good"
              ? "Continuez à prendre soin de vos oreilles en les protégeant et refaites un test tous les ans."
              : "Nous vous recommandons de prendre rendez-vous avec nous pour un test auditif professionnel en magasin."}
          </p>

          <ResultContactForm resultToken={resultToken} />

          {step.form && (
            <div {...className("actions")}>
              <Button
                theme="primary"
                big
                center
                button_id="ask-call"
                onClick={() => {
                  sendGTMEvent({ event: 'click_rappeler' })
                  handleNext({})
                }}
              >
                <PhoneIcon size={15} />
                <span>Être rappelé gratuitement</span>
              </Button>
              <a
                href="https://magasins.atol.fr/?f%5Bservices%5D=49"
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => {
                  sendGTMEvent({ event: 'click_trouver_centre' })
                }}
              >
                <Button theme="outline" big center button_id="find-center">
                  <PinIcon size={15} />
                  <span>Trouver un centre</span>
                </Button>
              </a>
            </div>
          )}

          <div {...className("CenterPath")}>
            <h2>Le parcours auditif dans un centre Atol Audition</h2>
            <div {...className("steps")}>
              <div>
                <div {...className("circle")}>1</div>
                <div {...className("text")}>RDV Bilan auditif offert</div>
              </div>

              <div>
                <div {...className("circle")}>2</div>
                <div {...className("text")}>
                  Aide à la prise de RDV chez l{"'"}ORL
                </div>
              </div>

              <div>
                <div {...className("circle")}>3</div>
                <div {...className("text")}>Choix de la solution</div>
              </div>

              <div>
                <div {...className("circle")}>4</div>
                <div {...className("text")}>Essai gratuit</div>
              </div>

              <div>
                <div {...className("circle")}>5</div>
                <div {...className("text")}>Réglages</div>
              </div>

              <div>
                <div {...className("circle")}>6</div>
                <div {...className("text")}>Suivi & garanties</div>
              </div>
            </div>
          </div>
        </div>

        <div {...className("legal")}>
          <p>
            Les résultats de ce test sont donnés à titre indicatif. En cas de
            doute sur votre audition, il est important de consulter un
            professionnel de la santé auditive, médecin ORL ou audioprothésiste.
          </p>
        </div>
      </div>
    </div>
  );
};
