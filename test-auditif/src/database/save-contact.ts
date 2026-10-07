"use server";

import { headers } from "next/headers";

import { createConnection } from "./createConnection";
import { insertProspect } from "./prospect";
import { computeScore } from "@/steps/ResultStep/ResultStep.utils";
import { ResultData } from "@/steps/step.types";
import { verifyResultToken } from "@/utils/session/session";
import { sendResultMail } from "@/utils/mail/resultMail";
import { isRateLimited } from "@/utils/rateLimit/rateLimit";
import {
  CONSENT_VERSION,
  ContactFormErrors,
  validateContactForm,
} from "@/utils/contact/contact.utils";

export type SaveContactResponse =
  | { success: true }
  | { success: false; message: string; errors?: ContactFormErrors };

// Result tokens already used (one submission per test).
const usedTokens = new Set<string>();

/**
 * Attach the client contact details to his test result, store his consents
 * and send him his results by email.
 */
export async function saveContact(
  resultToken: string,
  form: unknown
): Promise<SaveContactResponse> {
  const ip =
    (await headers()).get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "unknown";

  if (isRateLimited(`contact:${ip}`, 5, 10 * 60 * 1000)) {
    return {
      success: false,
      message: "Trop de demandes, veuillez réessayer dans quelques minutes.",
    };
  }

  const { data, errors } = validateContactForm(form);
  if (!data) {
    return {
      success: false,
      message: "Veuillez corriger les champs indiqués.",
      errors,
    };
  }

  const token =
    typeof resultToken === "string" ? await verifyResultToken(resultToken) : null;

  if (!token) {
    return {
      success: false,
      message: "Votre session a expiré, veuillez refaire le test.",
    };
  }

  if (usedTokens.has(token.jti)) {
    return {
      success: false,
      message: "Vos résultats ont déjà été envoyés.",
    };
  }

  const connection = await createConnection();

  try {
    await connection.beginTransaction();

    const [test] = await connection.query(
      "SELECT reponse_questions, idope FROM tests_audition WHERE idprp = ? LIMIT 1",
      [token.id_prospect]
    );

    if (!test) throw new Error(`No test found for prospect ${token.id_prospect}`);

    const notation = computeScore(
      JSON.parse(test.reponse_questions) as ResultData
    ) as "good" | "medium" | "bad";

    // Consents are stored with the contact as proof (RGPD).
    const infoprospect = JSON.stringify({
      consentement_resultats: true,
      optin_communications: data.consentCommunications,
      version_consentement: CONSENT_VERSION,
      date_consentement: new Date().toISOString(),
    });

    const id_prospect = await insertProspect(
      data,
      Number(test.idope),
      infoprospect,
      connection
    );

    // Link the test to the prospect with contact details.
    await connection.query(
      "UPDATE tests_audition SET idprp = ? WHERE idprp = ?",
      [id_prospect, token.id_prospect]
    );

    const mail = await sendResultMail({
      email: data.email,
      firstname: data.firstname,
      notation,
    });

    if (!mail.success) throw new Error("Result mail not sent");

    await connection.commit();
    usedTokens.add(token.jti);

    return { success: true };
  } catch (err) {
    console.error("saveContact error:", err);
    await connection.rollback().catch(() => undefined);

    return {
      success: false,
      message:
        "Une erreur est survenue, vos résultats n'ont pas pu être envoyés. Veuillez réessayer.",
    };
  } finally {
    await connection.end();
  }
}
