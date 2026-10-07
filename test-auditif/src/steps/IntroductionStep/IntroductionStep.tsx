import { useState } from "react";

import { NextButton, YearPicker, CenteredScreen, Accordion } from "@ui/common";

import { DeviceScreen } from "./DeviceScreen/DeviceScreen";
import { CalibrationScreen } from "./CalibrationScreen/CalibrationScreen";
import { CustomTest, useTestCustomization } from "./CustomTest/CustomTest";

import { sendGTMEvent } from '@next/third-parties/google'
import { IntroductionStep, StepComponentProps } from "../step.types";


import classNameModule from "@classname";
import styles from "./IntroductionStep.module.scss";
const className = classNameModule(styles);

/**
 *
 */
export const IntroductionStepComponent = ({
  step,
  data: dataInput,
  handleNext,
}: StepComponentProps<IntroductionStep>) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [data, setData] = useState<Record<string, any>>({
    gender: "female",
    birthyear: 1990,
    type: step.defaultType ?? "complete",
  });
  const [customTestIsOpen, setCustomTestIsOpen] = useState(false);

  const testCustomization = useTestCustomization();

  if (currentStepIndex === 2)
    return (
      <CenteredScreen screen_id="device">
        <DeviceScreen
          handleNext={() => {
            setCurrentStepIndex(3);
          }}
        />
      </CenteredScreen>
    );

  if (currentStepIndex === 3)
    return (
      <CenteredScreen screen_id="calibration">
        <CalibrationScreen
          handleNext={() => {
            handleNext(data);
          }}
        />
      </CenteredScreen>
    );

  if (currentStepIndex === 1)
    return (
      <CenteredScreen screen_id="personal-informations">
        <h1>Informations personnelles</h1>
        <p>
          Vos informations personnelles sont confidentielles. Elles seront
          uniquement utilisées pour le pré-diagnostic de votre audition et ne
          seront jamais partagées avec des tiers.
        </p>

        <PersonalInformations data={data} setData={setData} />

        <NextButton
          onClick={() => {

            sendGTMEvent({ event: 'test_informations_personnelles' })

            if (data.type === "vocal") setCurrentStepIndex(3);
            else setCurrentStepIndex(2);
          }}
          big
          theme="primary"
        >
          Suivant
        </NextButton>
      </CenteredScreen>
    );


  const showExtraText = dataInput.source === "web";

  return (
    <div {...className("IntroductionStep")} data-screen="introduction">
      {customTestIsOpen && (
        <CustomTest
          handleClose={() => setCustomTestIsOpen(false)}
          type={data.type}
          setType={(type) => {
            setData({ ...data, type });
          }}
          {...testCustomization}
        />
      )}

      <div {...className("body")}>
        <div {...className("illustration")}>
          <img src="/medias/images/introduction.jpg" />

          {dataInput.agentInformation && (
            <div {...className("agentInformation")}>
              Réalisé avec : {dataInput.agentInformation.prenom}{" "}
              {dataInput.agentInformation.nom[0].toUpperCase()}.
            </div>
          )}
        </div>
        <div {...className("content")}>
          <h1>Test Auditif</h1>

          <div {...className("explainationText")}>
            <h2>
              Prenez soin de votre audition pour une meilleure qualité de vie
            </h2>
            {
              showExtraText && (

                <>
                  <p>
                    Ce test conçu par des experts vous permet d’évaluer rapidement
                    votre capacité auditive. Il constitue une première étape pour
                    détecter d’éventuelles pertes auditives et agir le plus tôt
                    possible.
                  </p>

                  <h2>Pourquoi ce test est important :</h2>

                  <ol>
                    <li>
                      <strong>Identifier les problèmes le plus tôt possible</strong> :
                      Agir rapidement limite les impacts grâce à des solutions
                      adaptées.
                    </li>
                    <li>
                      <strong>Améliorer vos échanges</strong> : Une bonne audition
                      améliore les relations personnelles et professionnelles.
                    </li>
                    <li>
                      <strong>Protéger votre santé mentale</strong>  : Traiter la
                      perte auditive réduit les risques de troubles comme la démence
                      ou Alzheimer.
                    </li>
                    <li>
                      <strong>Sécurité accrue</strong>  : L’audition aide à détecter
                      les dangers (alarmes, circulation).
                    </li>
                    <li>
                      <strong>Profiter pleinement de chaque instant</strong> :
                      Profitez pleinement des conversations et des loisirs.
                    </li>
                  </ol>

                  <h2>Quels sont les risques d’une perte auditive non détectée :</h2>

                  <ul>
                    <li>Isolement social et repli sur soi.</li>
                    <li>Dépression et perte de confiance en soi.</li>
                    <li>
                      Difficultés professionnelles dues à une mauvaise compréhension.
                    </li>
                  </ul>

                  <p>
                    <strong>Important</strong> : Ce test est indicatif et ne remplace
                    pas un bilan médical. En cas de doute, consultez un
                    audioprothésiste ou un ORL. Vous devez avoir 18 ans ou plus pour le
                    réaliser.
                  </p>


                </>
              )
            }
            <p>
              <strong>Préparation</strong> : Trouvez un endroit calme pour
              effectuer le test. Utilisez des écouteurs ou un casque audio de
              préférence.
            </p>
          </div>


          {/* <p>
            Ce test est simple à réaliser, où que vous soyez et ne prendra que 5
            minutes.
          </p> */}
          <div {...className("actions")}>
            <NextButton
              onClick={() => {
                sendGTMEvent({ event: 'click_commencer_le_test' })
                setCurrentStepIndex(1);
              }}
              big
              theme="primary"
              button_id="start-test"
            >
              Commencer le test
            </NextButton>
            {step.customizable && (
              <NextButton
                onClick={() => {
                  setCustomTestIsOpen(true);
                }}
                big
                theme="outline"
                button_id="custom-test"
              >
                Tests spécifiques
              </NextButton>
            )}
          </div>

          <div {...className("instructions")}>
            <Accordion>
              <Accordion.Item label="Comment ça marche ?" id="how-it-works">
                <div {...className("label")}>
                  Préparez-vous au mieux pour votre test.
                </div>
                <ul>
                  <li>
                    <strong>
                      <span {...className("number")}>1</span>Préparation
                    </strong>
                    <span {...className("text")}>
                      Trouvez un endroit calme pour effectuer le test.
                      <br />
                      Utilisez des écouteurs ou un casque audio de préférence.
                    </span>
                  </li>
                  <li>
                    <strong>
                      <span {...className("number")}>2</span> Paramétrage
                    </strong>
                    <span {...className("text")}>
                      Ajustez le volume de votre appareil (nous vous
                      recommandons 50%).
                    </span>
                  </li>
                  <li>
                    <strong>
                      {" "}
                      <span {...className("number")}>3</span> Test
                    </strong>
                    <span {...className("text")}>
                      Suivez les instructions à l{"'"}
                      écran et répondez en conséquence.
                    </span>
                  </li>
                  <li>
                    <strong>
                      <span {...className("number")}>4</span>Résultats
                    </strong>
                    <span {...className("text")}>
                      À la fin du test, vos résultats apparaissent
                      instantanément.
                    </span>
                  </li>
                </ul>
              </Accordion.Item>
            </Accordion>

            <h2>Confidentialité</h2>
            <div>
              Nous respectons votre vie privée. Les données de votre test sont
              strictement confidentielles et ne seront jamais partagées sans
              votre consentement.
              <br />
              Test à objectif non médical et non substituable à une consultation
              réalisée par un professionnel de la santé auditive, médecin ORL ou
              audioprothésiste
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PersonalInformations = ({ data, setData }: PersonalInformationsProps) => {
  return (
    <div {...className("PersonalInformations")}>
      <div {...className("gender")}>
        <span
          {...className("background", {
            position: data.gender === "female" ? "left" : "right",
          })}
        ></span>
        <button
          data-button="gender-female"
          {...className({ active: data.gender === "female" })}
          onClick={() => {
            setData({
              ...data,
              gender: "female",
            });
          }}
        >
          Femme
        </button>
        <button
          data-button="gender-male"
          {...className({ active: data.gender === "male" })}
          onClick={() => {
            setData({
              ...data,
              gender: "male",
            });
          }}
        >
          Homme
        </button>
      </div>

      <div>
        <div {...className("label")}>Année de naissance</div>
        <YearPicker
          value={data.birthyear}
          onChange={(birthyear) => setData({ ...data, birthyear })}
        />
        {/* <input
          type="year"
          value={data.birthyear}
          onChange={(e) => {
            setData({
              ...data,
              birthyear: e.target.value,
            });
          }}
        /> */}
      </div>
    </div>
  );
};

type PersonalInformationsProps = {
  data: Record<string, any>;
  setData: (data: Record<string, any>) => void;
};
