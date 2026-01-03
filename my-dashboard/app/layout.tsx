import type { Metadata } from "next";
import { Geist, Geist_Mono, Borel } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const borel = Borel({
  variable: "--font-borel",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Analytics webapp",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${borel.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
