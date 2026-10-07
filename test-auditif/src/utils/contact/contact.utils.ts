/**
 * Contact form shared by the client (form) and the server (server action).
 * The server always re-validates: never trust values coming from the browser.
 */

export type ContactFormData = {
  lastname: string;
  firstname: string;
  phone: string;
  email: string;
  /** Required: consent to process health data to send the results. */
  consentResults: boolean;
  /** Optional: consent to receive marketing communications (email / SMS). */
  consentCommunications: boolean;
};

export type ContactFormErrors = Partial<Record<keyof ContactFormData, string>>;

// Version of the consent texts displayed in the form, stored with the consent as proof.
export const CONSENT_VERSION = "2026-10";

const NAME_REGEX = /^[\p{L}][\p{L}' .-]{0,49}$/u;
const EMAIL_REGEX = /^[^\s@<>"]{1,64}@[^\s@<>"]{1,185}\.[^\s@<>"]{2,}$/;
// French numbers: 0X XX XX XX XX or +33 X XX XX XX XX (spaces, dots or dashes allowed).
const PHONE_REGEX = /^(?:0|\+33 ?)[1-9](?:[ .-]?\d{2}){4}$/;

/**
 * Trim and validate the contact form. Returns normalized data or errors.
 */
export function validateContactForm(input: unknown):
  | { data: ContactFormData; errors?: undefined }
  | { data?: undefined; errors: ContactFormErrors } {
  const raw = (input ?? {}) as Record<string, unknown>;
  const str = (key: string) =>
    typeof raw[key] === "string" ? (raw[key] as string).trim() : "";

  const data: ContactFormData = {
    lastname: str("lastname"),
    firstname: str("firstname"),
    phone: str("phone"),
    email: str("email").toLowerCase(),
    consentResults: raw["consentResults"] === true,
    consentCommunications: raw["consentCommunications"] === true,
  };

  const errors: ContactFormErrors = {};

  if (!NAME_REGEX.test(data.lastname)) errors.lastname = "Nom invalide";
  if (!NAME_REGEX.test(data.firstname)) errors.firstname = "Prénom invalide";
  if (!EMAIL_REGEX.test(data.email) || data.email.length > 254)
    errors.email = "Adresse e-mail invalide";
  if (data.phone && !PHONE_REGEX.test(data.phone))
    errors.phone = "Numéro de téléphone invalide";
  if (!data.consentResults)
    errors.consentResults =
      "Votre accord est nécessaire pour vous envoyer vos résultats";

  return Object.keys(errors).length ? { errors } : { data };
}

/**
 * Escape a value before inserting it into an HTML email.
 */
export function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
