/**
 * Email sent to the client with his test results.
 * Server-side only: the content is built from the result stored in database,
 * never from data sent by the browser.
 */
import { escapeHtml } from "@/utils/contact/contact.utils";
import { sendMail } from "./mailer";

type Notation = "good" | "medium" | "bad";

const RESULT_TEXTS: Record<Notation, { result: string; advice: string }> = {
  good: {
    result:
      "Les résultats du test semblent indiquer que votre audition est <strong>normale</strong>.",
    advice:
      "Continuez à prendre soin de vos oreilles en les protégeant et refaites un test tous les ans.",
  },
  medium: {
    result:
      "Les résultats du test semblent indiquer que votre audition soit fragile. Il est possible que vous présentiez une perte auditive.",
    advice:
      "Nous vous recommandons de prendre rendez-vous avec nous pour un test auditif professionnel en magasin.",
  },
  bad: {
    result:
      "Les résultats du test semblent indiquer que vous avez une perte auditive importante.",
    advice:
      "Nous vous recommandons de prendre rendez-vous avec nous pour un test auditif professionnel en magasin.",
  },
};

export async function sendResultMail({
  email,
  firstname,
  notation,
}: {
  email: string;
  firstname: string;
  notation: Notation;
}) {
  const texts = RESULT_TEXTS[notation];

  const html = `
    <p>Bonjour ${escapeHtml(firstname)},</p>
    <p>Merci d'avoir réalisé le test auditif Atol Audition. Voici vos résultats :</p>
    <p style="padding:15px;border-radius:8px;background:#f4f4f4;">${texts.result}</p>
    <p>${texts.advice}</p>
    <p>
      Nos audioprothésistes diplômés d'État vous accueillent pour un bilan auditif offert :
      <a href="https://magasins.atol.fr/?f%5Bservices%5D=49">trouver un centre Atol Audition</a>.
    </p>
    <p style="font-size:12px;color:#666;">
      Les résultats de ce test sont donnés à titre indicatif et ne remplacent pas un bilan
      réalisé par un professionnel de la santé auditive, médecin ORL ou audioprothésiste.
      <br />
      Vous recevez cet e-mail car vous avez demandé à recevoir vos résultats. Pour exercer vos
      droits sur vos données : <a href="https://www.atol.fr/donnees-personnelles">www.atol.fr/donnees-personnelles</a>.
    </p>
  `;

  return await sendMail({
    to: email,
    subject: "Vos résultats du test auditif Atol Audition",
    html,
  });
}
