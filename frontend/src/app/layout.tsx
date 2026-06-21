import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Customer Support Copilot",
  description: "Enterprise Agentic Customer Support Copilot Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
