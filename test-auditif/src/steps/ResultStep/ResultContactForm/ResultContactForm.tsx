import { sendGTMEvent } from "@next/third-parties/google";
import { useState } from "react";
import { MailIcon } from "lucide-react";

import { Button, FormField } from "@ui/common";
import { Checkbox } from "@ui/common/Checkbox/Checkbox";

import { saveContact } from "@/database/save-contact";
import {
  ContactFormData,
  ContactFormErrors,
  validateContactForm,
} from "@/utils/contact/contact.utils";

import classNameModule from "@classname";
import styles from "./ResultContactForm.module.scss";
const className = classNameModule(styles);

type ResultContactFormProps = {
  /** Token returned when the result was saved. Null while saving, undefined on error. */
  resultToken: string | null | undefined;
};

const EMPTY_FORM: ContactFormData = {
  lastname: "",
  firstname: "",
  phone: "",
  email: "",
  consentResults: false,
  consentCommunications: false,
};

/**
 * Optional form on the result screen: the client can receive his results by
 * email and opt in to marketing communications.
 */
export const ResultContactForm = ({ resultToken }: ResultContactFormProps) => {
  const [formData, setFormData] = useState<ContactFormData>(EMPTY_FORM);
  const [errors, setErrors] = useState<ContactFormErrors>({});
  const [status, setStatus] = useState<"idle" | "sending" | "sent">("idle");
  const [message, setMessage] = useState("");

  if (status === "sent") {
    return (
      <div {...className("ResultContactForm", "sent")} role="status">
        <MailIcon size={20} />
        <p>
          Vos résultats ont été envoyés à <strong>{formData.email}</strong>.
        </p>
      </div>
    );
  }

  const unavailable = resultToken === undefined;

  return (
    <form {...className("ResultContactForm")} onSubmit={handleSubmit} noValidate>
      <h2>Recevoir mes résultats par e-mail</h2>

      <div {...className("fields")}>
        <FormField label="Nom*">
          <input {...bind("lastname")} autoComplete="family-name" required />
          {errors.lastname && <FieldError>{errors.lastname}</FieldError>}
        </FormField>

        <FormField label="Prénom*">
          <input {...bind("firstname")} autoComplete="given-name" required />
          {errors.firstname && <FieldError>{errors.firstname}</FieldError>}
        </FormField>

        <FormField label="E-mail*">
          <input {...bind("email")} type="email" autoComplete="email" required />
          {errors.email && <FieldError>{errors.email}</FieldError>}
        </FormField>

        <FormField label="Téléphone">
          <input {...bind("phone")} type="tel" autoComplete="tel" />
          {errors.phone && <FieldError>{errors.phone}</FieldError>}
        </FormField>
      </div>

      <ConsentCheckbox
        checked={formData.consentResults}
        onChange={(checked) => update("consentResults", checked)}
      >
        J{"'"}accepte qu{"'"}ATOL AUDITION SAS traite mes coordonnées et les
        résultats de mon test auditif (données de santé) afin de me les envoyer
        par e-mail.*
      </ConsentCheckbox>
      {errors.consentResults && <FieldError>{errors.consentResults}</FieldError>}

      <ConsentCheckbox
        checked={formData.consentCommunications}
        onChange={(checked) => update("consentCommunications", checked)}
      >
        J{"'"}accepte de recevoir des informations et offres d{"'"}Atol Audition
        par e-mail et SMS (facultatif).
      </ConsentCheckbox>

      <p {...className("legal")}>
        * Champs obligatoires. Vous pouvez retirer votre consentement et vous
        désabonner à tout moment. Pour en savoir plus sur la gestion de vos
        données et vos droits :{" "}
        <a
          href="https://www.atol.fr/donnees-personnelles"
          target="_blank"
          rel="noopener noreferrer"
        >
          politique de protection des données
        </a>
        .
      </p>

      {message && (
        <p {...className("message")} role="alert">
          {message}
        </p>
      )}

      <Button
        theme="primary"
        big
        type="submit"
        button_id="send-results"
        disabled={status === "sending" || !resultToken}
      >
        <MailIcon size={15} />
        <span>
          {status === "sending" ? "Envoi en cours..." : "Recevoir mes résultats"}
        </span>
      </Button>

      {unavailable && (
        <p {...className("message")} role="alert">
          L{"'"}envoi des résultats est momentanément indisponible.
        </p>
      )}
    </form>
  );

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!resultToken || status === "sending") return;

    const validation = validateContactForm(formData);
    if (!validation.data) {
      setErrors(validation.errors);
      setMessage("");
      return;
    }

    setErrors({});
    setMessage("");
    setStatus("sending");
    sendGTMEvent({ event: "click_recevoir_resultats" });

    try {
      const response = await saveContact(resultToken, validation.data);

      if (response.success) {
        setStatus("sent");
        return;
      }

      setErrors(response.errors ?? {});
      setMessage(response.message);
    } catch {
      setMessage("Une erreur est survenue. Veuillez réessayer.");
    }

    setStatus("idle");
  }

  function update<K extends keyof ContactFormData>(
    name: K,
    value: ContactFormData[K]
  ) {
    setFormData((data) => ({ ...data, [name]: value }));
  }

  function bind(name: "lastname" | "firstname" | "phone" | "email") {
    return {
      name,
      value: formData[name],
      "aria-invalid": errors[name] ? true : undefined,
      onChange: (e: React.ChangeEvent<HTMLInputElement>) =>
        update(name, e.target.value),
    };
  }
};

const FieldError = ({ children }: { children: React.ReactNode }) => (
  <div {...className("error")}>{children}</div>
);

const ConsentCheckbox = ({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children: React.ReactNode;
}) => (
  <label {...className("consent")}>
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
    />
    <Checkbox checked={checked} />
    <span>{children}</span>
  </label>
);
