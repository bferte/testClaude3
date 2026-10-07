"use server";

import { ResultData } from "@/steps/step.types";
import { createConnection } from "./createConnection";
import { Connection } from "mariadb";
import { insertProspect } from "./prospect";
import { generateResultToken } from "@/utils/session/session";

const SHOP_TEST_OPE_ID = 3;
const WEB_TEST_OPE_ID = 2;

enum SOURCE {
  WEB = "web",
  SHOP = "shop",
}

/**
 *
 */
export async function pushResult(
  data: ResultData,
  source: SOURCE,
  id_vendeur: string,
  id_magasin: string,
  clientInformations: {
    firstname?: string;
    lastname?: string;
    phone?: string;
    email?: string;
    postalCode?: string;
  }
) {
  const connection = await createConnection();

  try {
    const id_prospect = await insertProspect(
      clientInformations,
      source === SOURCE.SHOP ? SHOP_TEST_OPE_ID : WEB_TEST_OPE_ID,
      "",
      connection
    );

    await insertResult(
      id_prospect,
      id_vendeur,
      id_magasin,
      source === SOURCE.SHOP ? SHOP_TEST_OPE_ID : WEB_TEST_OPE_ID,
      JSON.stringify({
        questions: data.questions,
        tonal: data.tonal,
        vocal: data.vocal,
        informations: data.introduction,
      }),
      "",
      connection
    );

    return { resultToken: await generateResultToken(id_prospect) };
  } catch (Err) {
    console.error("Error : ", Err);
    throw new Error(Err as string);
  } finally {
    await connection.end();
  }
}

/**
 *
 */
async function insertResult(
  id_prospect: number,
  id_vendeur: string,
  id_mag: string,
  id_ope: number,
  reponse_questions: string,
  test: string,
  connection: Connection
) {
  const query = `
  INSERT INTO
    tests_audition
      (idprp, id_vendeur, id_mag, idope, reponse_questions, test)
    VALUES
      (?, ?, ?, ?, ?, ?);
  `;

  const values = [
    id_prospect,
    id_vendeur || null,
    id_mag || null,
    id_ope,
    reponse_questions,
    "",
  ];

  await connection.query(query, values);
}
