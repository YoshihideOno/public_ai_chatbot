import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "パスワードリセット - RAG AI Platform",
  description: "RAG AI Platform パスワードリセット",
};

export default function PasswordResetLayout({
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
