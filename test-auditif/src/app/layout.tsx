import type { Metadata } from "next";
import "./globals.css";
import { AccessibilityWrapper } from "@ui/common";
import { cookies } from "next/headers";
import { GoogleTagManager } from "@next/third-parties/google";

export const metadata: Metadata = {
  title: "ATOL - Test audio",
  description: "",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <head>
        <link rel="prefetch" href="/medias/vocal/noise.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/1.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/2.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/3.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/4.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/5.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/6.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/7.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/8.wav" as="audio" />
        <link rel="prefetch" href="/medias/vocal/9.wav" as="audio" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <AccessibilityWrapper
        cookieData={(await cookies()).get("accessiblity")?.value}
      >
        {children}
      </AccessibilityWrapper>
    </html>
  );
}
