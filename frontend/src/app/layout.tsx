import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chameleon - Steal a Hackathon Project",
  description: "Discover and steal innovative hackathon projects using AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="dark bg-black text-white antialiased">
        {children}
      </body>
    </html>
  );
}
