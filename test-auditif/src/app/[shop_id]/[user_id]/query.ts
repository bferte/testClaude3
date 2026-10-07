import { createConnection } from "@/database/createConnection";

export async function shopCodeExists(code: string) {
  const connection = await createConnection();
  try {
    const query = `
      SELECT * FROM shop WHERE code = '${code}'`;

    const result = await connection.query(query);

    return result.length > 0;
  } catch {
    return false;
  } finally {
    await connection.end();
  }
}
