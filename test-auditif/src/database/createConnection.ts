import mariadb from "mariadb";
import { Pool } from "mariadb";

let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) {
    pool = mariadb.createPool({
      host: process.env["DB_HOST"],
      user: process.env["DB_USER"],
      password: process.env["DB_PASSWORD"],
      database: process.env["DB_NAME"],
    });
  }
  return pool;
}

export async function createConnection() {
  const pool = getPool();
  return await pool.getConnection();
}
