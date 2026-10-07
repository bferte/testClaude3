import { sendGTMEvent } from '@next/third-parties/google'

import { useState } from "react";

import { StepComponentProps } from "../step.types";
import { NextButton, FormField } from "@ui/common";
import { pushResult } from "@/database/push-result";

import classNameModule from "@classname";
import styles from "./PersonalInformationsStep.module.scss";
import { sendResultMail } from "@/utils/mail/sendMail";
const className = classNameModule(styles);

export const PersonalInformationsStep = ({ data }: StepComponentProps<any>) => {
  const [sent, setSent] = useState(false);

  const [formData, setFormData] = useState<Record<string, string>>({
    firstname: "",
    lastname: "",
    email: "",
    phone: "",
    postalCode: "",
  });

  if (sent) {
    return (
      <div {...className("PersonalInformationsStep")}>
        <h1>
          Nous avons le plaisir de vous confirmer la bonne reception de votre
          demande
        </h1>
        <p>Nous vous répondrons très prochainement</p>
      </div>
    );
  }

  return (
    <div {...className("PersonalInformationsStep")}>
      <div>
        <h1>Informations personnelles</h1>

        <form onSubmit={async e => {
          e.preventDefault();

          sendGTMEvent({ event: 'click_envoyer_informations' })
          pushResult(
            JSON.parse(JSON.stringify(data)),
            data.source,
            "",
            "",
            formData
          ).then(() => {
            console.log("RESULT SENT SUCCESSFULLY");
          });

          sendResultMail({
            firstname: formData.firstname,
            lastname: formData.lastname,
            phone: formData.phone,
            postalCode: formData.postalCode,
          }).then(() => {
            console.log("MAIL SENT SUCCESSFULLY");
          });


          setSent(true);
        }}>
          <FormField label="Nom de famille*">
            <input {...bind("lastname")} required />
          </FormField>

          <FormField label="Prénom*">
            <input {...bind("firstname")} required />
          </FormField>

          {/* <FormField label="E-mail">
          <input {...bind("email")} />
        </FormField> */}

          <FormField label="Téléphone*">
            <input {...bind("phone")} required type="tel" />
          </FormField>

          <FormField label="Code postal*">
            <input {...bind("postalCode")} required />
          </FormField>

          <div {...className("legal")}>
            Je consens qu’ATOL AUDITION SAS, AUDITION GROUP, ATOL SA et ATOL GROUP,
            ainsi que leur personnel habilité et leurs hébergeurs agréés de
            données de santé collectent, traitent et hébergent mes données à
            caractère personnel afin de recevoir des sms et email, des offres
            pourront également vous être adressées. Ces informations sont
            obligatoires pour la préparation de mes rendez-vous. Je consens
            également à la collecte de mes données personnelles pour recevoir des
            offres. Vous pouvez révoquez votre consentement et vous désabonner à
            tout moment, pour en savoir plus sur la politique de protection des
            personnelle{" "}
            <a href="https://www.atol.fr/donnees-personnelles">cliquer ICI</a>.
          </div>

          <div
            style={{ display: "flex", justifyContent: "center", marginTop: 30 }}
          >
            <NextButton

              theme="primary"
              big
            >
              Envoyer
            </NextButton>
          </div>

        </form>
      </div>
    </div>
  );

  function bind(name: string) {
    return {
      value: formData[name],
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        setFormData({ ...formData, [name]: e.target.value }),
    };
  }
};
