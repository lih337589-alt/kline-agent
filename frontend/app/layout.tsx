import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppHeader } from "@/components/AppHeader";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "K线之上",
    template: "%s | K线之上",
  },
  description: "AI Multi-Agent Financial Research Platform",
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html lang="zh-CN">
      <body>
        <AppHeader />
        {children}
      </body>
    </html>
  );
}
