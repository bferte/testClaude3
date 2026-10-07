"use client";

import {
  CSSProperties,
  Dispatch,
  ReactNode,
  SetStateAction,
  createContext,
  useContext,
  useState,
  useEffect,
} from "react";

import Cookies from "js-cookie";

import { Poppins } from "next/font/google";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const accessibilityContext = createContext<AccessibilityContextData>({
  dyslexic: false,
  inversedContrast: false,
  largFonts: false,
  setAccessibilityData: (data) => data,
});

type AccessibilityContextData = {
  setAccessibilityData: Dispatch<SetStateAction<AccessibilityData>>;
} & AccessibilityData;

type AccessibilityData = {
  dyslexic: boolean;
  inversedContrast: boolean;
  largFonts: boolean;
};

export const useAccessibilityContext = () => useContext(accessibilityContext);

export function AccessibilityWrapper({
  children,
  cookieData,
}: {
  children: ReactNode;
  cookieData?: string;
}) {
  const [accessibilityData, setAccessibilityData] = useState<AccessibilityData>(
    getAccessibilityFromCookie()
  );

  function getAccessibilityFromCookie() {
    if (cookieData) return JSON.parse(cookieData);

    const cookie = Cookies.get("accessiblity");
    if (cookie) {
      return JSON.parse(cookie);
    }
    return {
      dyslexic: false,
      inversedContrast: false,
      largFonts: false,
    };
  }

  useEffect(() => {
    Cookies.set("accessiblity", JSON.stringify(accessibilityData), {
      expires: 365,
      path: "/",
    });
  }, [accessibilityData]);

  return (
    <accessibilityContext.Provider
      value={{ ...accessibilityData, setAccessibilityData }}
    >
      <body
        style={
          {
            fontSize: accessibilityData.largFonts ? 22 : 16,
            fontFamily: accessibilityData.dyslexic
              ? "OpenDyslexic"
              : poppins.style.fontFamily,
            "--title-font-family": accessibilityData.dyslexic
              ? "OpenDyslexic"
              : poppins.style.fontFamily,
            "--background": accessibilityData.inversedContrast
              ? "33, 33, 33"
              : "238, 238, 238",
            "--background-alt": accessibilityData.inversedContrast
              ? "39, 39, 39"
              : "255, 255, 255",
            "--background-alt-hover": accessibilityData.inversedContrast
              ? "46, 46, 46"
              : "255, 255, 255",
            "--text": accessibilityData.inversedContrast
              ? "238, 238, 238"
              : "33, 33, 33",
            "--light": accessibilityData.inversedContrast
              ? "44, 44, 44"
              : "238, 238, 238",
            "--primary": "19, 56, 108",
            "--primary-hover": accessibilityData.inversedContrast
              ? "32, 74, 134"
              : "11, 41, 82",
          } as CSSProperties
        }
      >
        {children}
      </body>
    </accessibilityContext.Provider>
  );
}
