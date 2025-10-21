'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Bot, 
  Zap, 
  Shield, 
  Users, 
  FileText, 
  BarChart3,
  ArrowRight,
  CheckCircle,
  Star,
  MessageCircle,
  Mail,
  Phone,
  MapPin,
  Clock,
  Globe,
  Database,
  Lock,
  TrendingUp
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

/**
 * サービス紹介・ランディングページ
 * 
 * 当サービスの最初の画面として、以下の内容を表示します：
 * - サービス紹介
 * - 使い方・機能説明
 * - 問い合わせ情報
 * - ログイン・アカウント登録への導線
 * 
 * ログイン済みユーザーは自動的にダッシュボードにリダイレクトされます。
 */
export default function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // ログイン済みの場合はダッシュボードにリダイレクト
  React.useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* ヘッダー */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Bot className="h-8 w-8 text-primary" />
              <span className="text-xl font-bold text-gray-900">RAG AI Platform</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/login">
                <Button variant="outline">ログイン</Button>
              </Link>
              <Link href="/login?tab=register">
                <Button>アカウント登録</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* メインビジュアル */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 mb-6">
            AI チャットボット
            <span className="text-primary block">プラットフォーム</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            RAG（Retrieval-Augmented Generation）技術を活用した
            <br />
            高精度なAIチャットボットを簡単に構築・運用できます
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/login">
              <Button size="lg" className="w-full sm:w-auto">
                今すぐ始める
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="w-full sm:w-auto">
              デモを見る
            </Button>
          </div>
        </div>
      </section>

      {/* 特徴セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              なぜ選ばれるのか
            </h2>
            <p className="text-lg text-gray-600">
              企業のニーズに応える高機能なAIプラットフォーム
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Zap className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle>高速レスポンス</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  平均3秒以内の高速応答で、ユーザーエクスペリエンスを向上
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="h-6 w-6 text-green-600" />
                </div>
                <CardTitle>セキュリティ重視</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  マルチテナント対応、RBAC認可、データ分離で安全な運用
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Database className="h-6 w-6 text-purple-600" />
                </div>
                <CardTitle>RAG技術</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  最新のRAG技術で高精度な回答生成と文書検索を実現
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                  <Users className="h-6 w-6 text-orange-600" />
                </div>
                <CardTitle>マルチテナント</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  複数の組織・プロジェクトを安全に分離して管理
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="h-6 w-6 text-red-600" />
                </div>
                <CardTitle>詳細分析</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  利用状況、パフォーマンス、ユーザー行動の詳細分析
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                  <Lock className="h-6 w-6 text-indigo-600" />
                </div>
                <CardTitle>エンタープライズ対応</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  大規模組織向けのスケーラブルなアーキテクチャ
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* 使い方セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              簡単3ステップで開始
            </h2>
            <p className="text-lg text-gray-600">
              複雑な設定は不要。すぐにAIチャットボットを運用開始できます
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">アカウント作成</h3>
              <p className="text-gray-600">
                メールアドレスとパスワードで簡単にアカウントを作成
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">コンテンツアップロード</h3>
              <p className="text-gray-600">
                ナレッジベースとなる文書をアップロードしてAIに学習させます
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">チャット開始</h3>
              <p className="text-gray-600">
                AIチャットボットが文書に基づいた高精度な回答を提供
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 機能詳細セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              豊富な機能
            </h2>
            <p className="text-lg text-gray-600">
              企業の様々なニーズに対応する包括的な機能セット
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <h3 className="text-2xl font-semibold mb-6">管理機能</h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">ユーザー管理</h4>
                    <p className="text-sm text-gray-600">役割ベースのアクセス制御</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">テナント管理</h4>
                    <p className="text-sm text-gray-600">マルチテナント環境の構築</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">コンテンツ管理</h4>
                    <p className="text-sm text-gray-600">文書のアップロード・編集・削除</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">API管理</h4>
                    <p className="text-sm text-gray-600">APIキーの発行・管理</p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-semibold mb-6">分析機能</h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">利用統計</h4>
                    <p className="text-sm text-gray-600">質問数、ユーザー数、応答時間</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">パフォーマンス分析</h4>
                    <p className="text-sm text-gray-600">システム性能の詳細分析</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">ユーザー行動分析</h4>
                    <p className="text-sm text-gray-600">ユーザーの利用パターン分析</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium">レポート生成</h4>
                    <p className="text-sm text-gray-600">定期的なレポート自動生成</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 問い合わせセクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              お問い合わせ
            </h2>
            <p className="text-lg text-gray-600">
              ご質問やご相談がございましたら、お気軽にお問い合わせください
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Mail className="h-6 w-6 text-blue-600" />
                </div>
                <CardTitle>メールサポート</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  24時間以内に回答いたします
                </CardDescription>
                <p className="text-sm text-primary font-medium mt-2">
                  support@rag-ai-platform.com
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <Phone className="h-6 w-6 text-green-600" />
                </div>
                <CardTitle>電話サポート</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  平日 9:00-18:00
                </CardDescription>
                <p className="text-sm text-primary font-medium mt-2">
                  03-1234-5678
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <MessageCircle className="h-6 w-6 text-purple-600" />
                </div>
                <CardTitle>チャットサポート</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  リアルタイムでサポート
                </CardDescription>
                <p className="text-sm text-primary font-medium mt-2">
                  ログイン後利用可能
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-12 text-center">
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle>会社情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center space-x-2">
                  <MapPin className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    〒100-0001 東京都千代田区千代田1-1-1
                  </span>
                </div>
                <div className="flex items-center justify-center space-x-2">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    営業時間: 平日 9:00-18:00
                  </span>
                </div>
                <div className="flex items-center justify-center space-x-2">
                  <Globe className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    https://rag-ai-platform.com
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-primary">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            今すぐ始めませんか？
          </h2>
          <p className="text-xl text-primary-foreground mb-8">
            無料トライアルで、AIチャットボットの可能性を体験してください
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/login">
              <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                無料で始める
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Button variant="outline" size="lg" className="w-full sm:w-auto text-white border-white hover:bg-white hover:text-primary">
              デモを予約
            </Button>
          </div>
        </div>
      </section>

      {/* フッター */}
      <footer className="bg-gray-900 text-white py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Bot className="h-6 w-6" />
                <span className="text-lg font-bold">RAG AI Platform</span>
              </div>
              <p className="text-sm text-gray-400">
                企業向けAIチャットボットプラットフォーム
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-4">製品</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>機能一覧</li>
                <li>価格</li>
                <li>API</li>
                <li>統合</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">サポート</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>ヘルプセンター</li>
                <li>ドキュメント</li>
                <li>コミュニティ</li>
                <li>ステータス</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">会社</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>会社概要</li>
                <li>採用情報</li>
                <li>プレス</li>
                <li>パートナー</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2024 RAG AI Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}