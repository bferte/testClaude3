"server only";

import uniqid from "uniqid";
import * as jose from "jose";

const SESSION_TOKEN_SECRET = process.env["SESSION_TOKEN_SECRET"];

export async function generateSessionToken(data: any) {
  if (!SESSION_TOKEN_SECRET) throw new Error("SESSION_TOKEN_SECRET is not set");
  const token = await new jose.SignJWT({
    ...data,
    id: uniqid(),
  })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("24h")
    .sign(new TextEncoder().encode(SESSION_TOKEN_SECRET));

  return token;
}

/**
 * Token returned to the browser after a result is saved. It allows the client
 * to attach his contact details to this result only (the id is not exposed).
 */
export async function generateResultToken(id_prospect: number) {
  if (!SESSION_TOKEN_SECRET) throw new Error("SESSION_TOKEN_SECRET is not set");

  return await new jose.SignJWT({ scope: "result", id_prospect })
    .setProtectedHeader({ alg: "HS256" })
    .setJti(uniqid())
    .setIssuedAt()
    .setExpirationTime("2h")
    .sign(new TextEncoder().encode(SESSION_TOKEN_SECRET));
}

export async function verifyResultToken(token: string) {
  if (!SESSION_TOKEN_SECRET) throw new Error("SESSION_TOKEN_SECRET is not set");

  try {
    const { payload } = await jose.jwtVerify(
      token,
      new TextEncoder().encode(SESSION_TOKEN_SECRET)
    );

    if (payload["scope"] !== "result" || !payload.jti) return null;
    if (typeof payload["id_prospect"] !== "number") return null;

    return { id_prospect: payload["id_prospect"], jti: payload.jti };
  } catch {
    return null;
  }
}

export async function verifySessionToken(token: string) {
  if (!SESSION_TOKEN_SECRET) throw new Error("SESSION_TOKEN_SECRET is not set");

  try {
    const { payload } = await jose.jwtVerify(
      token,
      new TextEncoder().encode(SESSION_TOKEN_SECRET)
    );

    return payload as {
      type: "shop" | "online";
      user_id: string;
      shop_id: string;
    };
  } catch {
    return null;
  }
}
