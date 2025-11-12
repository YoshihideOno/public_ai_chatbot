import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ログイン - RAG AI Chatbot Platform",
  description: "RAG AI Chatbot Platform にログイン",
};

export default function LoginLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen bg-gray-50">
      {children}
    </div>
  );
}
