import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "このアプリについて - AIチャットボット",
  description: "AIチャットボットアプリケーションの詳細情報",
};

export default function About() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="bg-white rounded-lg shadow-md p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">
            このアプリについて
          </h1>
          
          <div className="space-y-6 text-gray-600">
            <section>
              <h2 className="text-xl font-semibold text-gray-800 mb-3">
                AIチャットボットとは
              </h2>
              <p className="leading-relaxed">
                このアプリケーションは、最新のAI技術を活用したチャットボットサービスです。
                自然な会話を通じて、様々な質問にお答えし、お手伝いをさせていただきます。
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-800 mb-3">
                主な機能
              </h2>
              <ul className="list-disc list-inside space-y-2">
                <li>自然な日本語での会話</li>
                <li>様々なトピックに関する質問対応</li>
                <li>リアルタイムでの回答生成</li>
                <li>ユーザーフレンドリーなインターフェース</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-800 mb-3">
                技術スタック
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-100 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-800 mb-2">フロントエンド</h3>
                  <ul className="text-sm space-y-1">
                    <li>• Next.js 15.5.4</li>
                    <li>• React 19.1.0</li>
                    <li>• TypeScript</li>
                    <li>• Tailwind CSS</li>
                  </ul>
                </div>
                <div className="bg-gray-100 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-800 mb-2">バックエンド</h3>
                  <ul className="text-sm space-y-1">
                    <li>• PostgreSQL 13</li>
                    <li>• Docker & Docker Compose</li>
                    <li>• Node.js 20</li>
                  </ul>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-800 mb-3">
                今後の予定
              </h2>
              <p className="leading-relaxed">
                より高度なAI機能の追加、多言語対応、カスタマイズ機能の実装などを予定しています。
                ユーザーの皆様からのフィードバックを大切に、継続的に改善を重ねていきます。
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
