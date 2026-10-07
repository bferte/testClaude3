import { redirect } from "next/navigation";

import { generateSessionToken } from "@/utils/session/session";

type PageProps = {
  params: Promise<{
    shop_id: string;
    user_id: string;
  }>;
};

export default async function Page({ params }: PageProps) {
  const { shop_id, user_id } = await params;

  const token = await generateSessionToken({
    type: 'shop',
    user_id,
    shop_id
  });

  redirect(`/session/${token}`);
}
