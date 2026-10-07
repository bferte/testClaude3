"use server";

/**
 * Send a mail for company internal use
 */
import nodemailer from "nodemailer";

export interface EmailOptions {
  subject: string;
  html?: string;
  text?: string;
}

/**
 *
 */
export async function sendResultMail(data: {
  firstname: string;
  lastname: string;
  phone: string;
  postalCode: string;
}) {
  const object = `[Atol Audition] Un prospect souhaite être rappelé`;

  const htmlContent = `
    <div>
        <p>Bonjour,</p>
        <p>Un prospect à utiliser le test de dépistage Atol Mon Audition et souhaite être rappelé gratuitement.</p>
        <p>Pouvez-vous recontacter le prospect suivant :</p>
        <ul>
            <li>Nom : ${data.lastname}</li>
            <li>Prénom : ${data.firstname}</li>
            <li>Code postal : ${data.postalCode}</li>
            <li>Tel: ${data.phone}</li>
        </ul>
        <p><strong>Important :</strong> Le délai idéal pour rappeler un prospect est un rappel immédiat ou dans les 24 heures qui suivent la réception de ce mail. Ne passez pas à côté d'un potentiel nouveau patient.</p>
    </div>
    `;

  return await sendInternalMail({
    subject: object,
    html: htmlContent,
  });
}

async function sendInternalMail({ subject, html, text }: EmailOptions) {
  const transporter = nodemailer.createTransport({
    host: "in-v3.mailjet.com",
    port: 465,
    secure: true,
    auth: {
      user: process.env.MAILJET_API_KEY || "",
      pass: process.env.MAILJET_PASSWORD || "",
    },
  });

  const mailOptions = {
    from: "informations@audition.atol.fr",
    to: "servicecommande@auditiongp.com",
    subject,
    html,
    text,
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    return { success: true, messageId: info.messageId };
  } catch (error) {
    console.error("Error sending email:", error);
    return { success: false, error };
  }
}
