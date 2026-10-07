import { GoogleTagManager } from "@next/third-parties/google";

export default function Layout({ children }: { children: React.ReactNode }) {

    return (
        <>
            {process.env["LOCALE"] !== "true" && (
                <GoogleTagManager gtmId={process.env["GTM_ID"]!} dataLayer={{
                    context: 'web'
                }} />
            )}
            {children}
        </>
    );
}

