/**
 * Server-side mail transport (not a server action: never import it from a
 * "use client" file, and never export it from a "use server" file).
 */
import nodemailer from "nodemailer";

export const MAIL_FROM = "informations@audition.atol.fr";

export async function sendMail(options: {
  to: string;
  subject: string;
  html?: string;
  text?: string;
}) {
  const transporter = nodemailer.createTransport({
    host: "in-v3.mailjet.com",
    port: 465,
    secure: true,
    auth: {
      user: process.env.MAILJET_API_KEY || "",
      pass: process.env.MAILJET_PASSWORD || "",
    },
  });

  try {
    const info = await transporter.sendMail({ from: MAIL_FROM, ...options });
    return { success: true, messageId: info.messageId };
  } catch (error) {
    console.error("Error sending email:", error);
    return { success: false, error };
  }
}
