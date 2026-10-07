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
