import { Connection } from "mariadb";

/**
 * Server-side helper (not a server action: never import it from a "use client" file).
 * Values are always passed as query parameters.
 */
export async function insertProspect(
  clientInformations: {
    firstname?: string;
    lastname?: string;
    phone?: string;
    email?: string;
    postalCode?: string;
  },
  id_ope: number,
  infoprospect: string,
  connection: Connection
) {
  const query = `
  INSERT INTO
    prospect
      (nom, prenom, tel, mail, codpos, infoprospect, idope)
    VALUES
      (?, ?, ?, ?, ?, ?, ?);
  `;

  const result = await connection.query(query, [
    clientInformations?.lastname ?? "",
    clientInformations?.firstname ?? "",
    clientInformations?.phone ?? "",
    clientInformations?.email ?? "",
    clientInformations?.postalCode ?? "",
    infoprospect,
    id_ope,
  ]);

  return Number(result.insertId);
}
