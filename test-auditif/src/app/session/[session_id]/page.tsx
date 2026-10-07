import classNameModule from "@classname";
import styles from "./page.module.scss";
import { verifySessionToken } from "@/utils/session/session";
import PageClient from "./page.client";
import { cookies } from "next/headers";
import { GoogleTagManager } from "@next/third-parties/google";
const className = classNameModule(styles);

type PageProps = {
  params: Promise<{
    session_id: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { session_id } = await params;

  const sessionData = await verifySessionToken(session_id);

  if (!sessionData) return <TokenErrorScreen />;

  const agentInformation = await getUserInformations(
    sessionData.user_id,
    sessionData.shop_id
  );


  const cookiesStore = await cookies();

  if (cookiesStore.get(session_id)?.value === "true") {
    return <TokenErrorScreen />;
  }

  return (<>

    {process.env["LOCALE"] !== "true" && (
      <GoogleTagManager gtmId={process.env["GTM_ID"]!} dataLayer={{
        context: "shop",
        shop_id: sessionData.shop_id,
        user_id: sessionData.user_id,
      }} />
    )}
    <PageClient
      params={{
        shop_id: sessionData.shop_id,
        type: sessionData.type,
        user_id: sessionData.user_id,
        session_token: session_id,
        agentInformation,
      }}
    />
  </>
  );
}

const TokenErrorScreen = () => {
  return (
    <div {...className("TokenErrorScreen")}>
      Veuillez relancer le test via AS3.2 pour effectuer un nouveau test
    </div>
  );
};

async function getUserInformations(user_id: string, shop_id: string) {
  try {
    const headers = new Headers();
    headers.set("X-API-KEY", process.env["API_KEY"] ?? "");

    const response = await fetch(
      `${process.env["API_URL"]}/api/utilisateurs?code_magasin_atol=${shop_id}`,
      {
        headers,
      }
    );

    const data = (await response.json()) as UserInformation[];

    return data.find((user: any) => user.utilisateur_id === Number(user_id));
  } catch {
    return null;
  }
}

type UserInformation = {
  utilisateur_id: number;
  nom: string;
  prenom: string;
  login: string;
  email: string;
  matricule: string;
  connection_autorise: boolean;
  verrouille: boolean;
  specialites: string[];
};
