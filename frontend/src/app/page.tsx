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
  TrendingUp,
  Sparkles,
  Code,
  BookOpen,
  Settings,
  Upload,
  Key,
  HelpCircle,
  X,
  Target,
  Lightbulb
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { CodeBlock, CodeBlockWithTabs } from '@/components/ui/code-block';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

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
              <span className="text-xl font-bold text-gray-900">RAG AI Chatbot Platform</span>
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

      {/* AI Chatbotの紹介セクション - 他との違いを明確化 */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              AI Chatbotの紹介
            </h2>
            <p className="text-lg text-gray-600">
              RAG技術を活用した次世代のAIチャットボットプラットフォーム
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
            <div>
              <h3 className="text-2xl font-semibold mb-6 flex items-center">
                <Sparkles className="h-6 w-6 text-primary mr-2" />
                特長
              </h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium mb-1">RAG技術による高精度回答</h4>
                    <p className="text-sm text-gray-600">
                      自社のナレッジベースに基づいた正確で最新の情報を提供します。一般的なChatbotとは異なり、事前学習データに依存せず、常に最新の情報で回答します。
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium mb-1">マルチテナント対応</h4>
                    <p className="text-sm text-gray-600">
                      複数の組織やプロジェクトを完全に分離して管理。エンタープライズレベルのセキュリティとデータ分離を実現します。
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium mb-1">カスタマイズ可能なナレッジベース</h4>
                    <p className="text-sm text-gray-600">
                      PDF、HTML、Markdown、CSV、TXTなど様々な形式の文書をアップロードし、独自のナレッジベースを構築できます。
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="font-medium mb-1">複数LLM対応</h4>
                    <p className="text-sm text-gray-600">
                      OpenAI、Gemini、Anthropicなど複数のLLMプロバイダーに対応。用途に応じて最適なモデルを選択できます。
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-semibold mb-6 flex items-center">
                <Target className="h-6 w-6 text-primary mr-2" />
                他のChatbotと違うところ
              </h3>
              <div className="space-y-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <Star className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <h4 className="font-medium mb-1">自社データに基づいた回答</h4>
                          <p className="text-sm text-gray-600">
                            一般的なChatbotは汎用的な知識で回答しますが、当プラットフォームは自社の文書やデータに基づいて回答します。
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <Star className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <h4 className="font-medium mb-1">エンタープライズ対応</h4>
                          <p className="text-sm text-gray-600">
                            マルチテナント、RBAC認可、詳細な分析機能など、企業利用に必要な機能を包括的に提供します。
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex items-start space-x-3">
                        <Star className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <h4 className="font-medium mb-1">簡単な導入</h4>
                          <p className="text-sm text-gray-600">
                            APIキーがあれば無料でお試し可能。複雑な設定は不要で、すぐに運用を開始できます。
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>

          {/* 比較表 */}
          <Card className="mt-12">
            <CardHeader>
              <CardTitle>一般的なChatbot vs 当プラットフォーム</CardTitle>
              <CardDescription>
                主要な機能を比較しました
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>機能</TableHead>
                    <TableHead>一般的なChatbot</TableHead>
                    <TableHead className="bg-primary/10">当プラットフォーム</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">ナレッジベース</TableCell>
                    <TableCell>用意されたナレッジ</TableCell>
                    <TableCell className="bg-primary/5">
                      <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                      自社データに基づく
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">ナレッジカスタマイズ性</TableCell>
                    <TableCell>限定的</TableCell>
                    <TableCell className="bg-primary/5">
                      <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                      完全カスタマイズ可能
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">マルチテナント</TableCell>
                    <TableCell>
                      <X className="h-4 w-4 text-red-500 inline mr-2" />
                      非対応
                    </TableCell>
                    <TableCell className="bg-primary/5">
                      <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                      完全対応
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">セキュリティ</TableCell>
                    <TableCell>基本レベル</TableCell>
                    <TableCell className="bg-primary/5">
                      <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                      エンタープライズレベル
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">分析機能</TableCell>
                    <TableCell>基本的な統計</TableCell>
                    <TableCell className="bg-primary/5">
                      <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                      詳細な分析・レポート
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">導入コスト</TableCell>
                    <TableCell>比較的高額</TableCell>
                    <TableCell className="bg-primary/5">
                      <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                      APIキーがあれば無料お試し可能
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 特徴セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
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

      {/* 解決できる問題とユースケースセクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              何ができて、どんな問題を解決できるか
            </h2>
            <p className="text-lg text-gray-600">
              企業の様々な課題を解決するAIチャットボットソリューション
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
            <div>
              <h3 className="text-2xl font-semibold mb-6 flex items-center">
                <Target className="h-6 w-6 text-primary mr-2" />
                解決できる問題
              </h3>
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <MessageCircle className="h-5 w-5 text-blue-500 mr-2" />
                      顧客サポートの自動化
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">
                      24時間365日、顧客からの問い合わせに自動で対応。人的リソースを削減しながら、顧客満足度を向上させます。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <Database className="h-5 w-5 text-purple-500 mr-2" />
                      社内ナレッジベースの活用
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">
                      社内のマニュアル、規程書、FAQなどの情報を一元管理し、従業員が必要な情報を素早く検索・取得できます。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <Clock className="h-5 w-5 text-green-500 mr-2" />
                      24時間対応の実現
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">
                      営業時間外でも問い合わせに対応。グローバル企業でも時差を気にせず、世界中の顧客をサポートできます。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <Globe className="h-5 w-5 text-orange-500 mr-2" />
                      多言語対応
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">
                      現代のLLMモデル（GPT-4、Claude、Geminiなど）は多言語を理解できるため、
                      日本語のコンテンツを登録しておけば、英語や中国語など様々な言語で質問されても、
                      そのコンテンツを参照して適切な言語で回答できます。
                    </p>
                    <p className="text-sm text-gray-600">
                      例えば、日本語のFAQを登録しておけば、英語で「How do I return a product?」と質問されても、
                      日本語のFAQを参照して英語で回答を生成します。グローバル展開をサポートします。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <TrendingUp className="h-5 w-5 text-red-500 mr-2" />
                      カスタマーエクスペリエンスの向上
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">
                      即座に回答を提供することで、顧客の待ち時間を削減。満足度の向上とリピート率の改善につながります。
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>

            <div>
              <h3 className="text-2xl font-semibold mb-6 flex items-center">
                <Lightbulb className="h-6 w-6 text-primary mr-2" />
                応用例
              </h3>
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <FileText className="h-5 w-5 text-blue-500 mr-2" />
                      Webサイトの案内
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>用途:</strong> FAQ対応、サイトナビゲーション、サービス紹介
                    </p>
                    <p className="text-sm text-gray-600">
                      企業のWebサイトに埋め込み、訪問者からの質問に自動で回答。よくある質問への対応を自動化し、問い合わせ窓口の負荷を軽減します。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <Settings className="h-5 w-5 text-green-500 mr-2" />
                      製品Q&A
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>用途:</strong> 製品仕様の説明、使用方法の案内、トラブルシューティング
                    </p>
                    <p className="text-sm text-gray-600">
                      製品マニュアルや仕様書をナレッジベースとして登録し、顧客からの製品に関する質問に正確に回答。サポートコストを削減しながら、顧客満足度を向上させます。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <Users className="h-5 w-5 text-purple-500 mr-2" />
                      社内ヘルプデスク
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>用途:</strong> 社内規程の案内、ITサポート、人事制度の説明
                    </p>
                    <p className="text-sm text-gray-600">
                      社内のマニュアルや規程書を登録し、従業員からの問い合わせに自動対応。HR部門やIT部門の負荷を軽減します。
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <BookOpen className="h-5 w-5 text-orange-500 mr-2" />
                      教育・研修コンテンツの提供
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>用途:</strong> 研修資料の提供、学習サポート、知識の共有
                    </p>
                    <p className="text-sm text-gray-600">
                      教育コンテンツや研修資料を登録し、学習者からの質問に回答。24時間いつでも学習をサポートします。
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 使い方セクション - 使うための準備 */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              使うための準備
            </h2>
            <p className="text-lg text-gray-600">
              APIキーがあれば無料お試し可能。準備の大まかな流れをご紹介します
            </p>
            <p className="text-lg text-gray-600 mb-4">
              無料お試しは初めて質問した日から１ヶ月。
            </p>
            <Badge variant="outline" className="text-sm">
              <Key className="h-4 w-4 mr-1" />
              APIキーがあれば無料でお試し可能
            </Badge>
          </div>

          {/* 準備の流れ */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-16">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">1</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">アカウント登録</h3>
              <p className="text-gray-600 text-sm">
                メールアドレスとパスワードで簡単にアカウントを作成
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">2</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">APIキー登録</h3>
              <p className="text-gray-600 text-sm">
                LLMプロバイダーのAPIキーを設定
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">3</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">コンテンツ登録</h3>
              <p className="text-gray-600 text-sm">
                ナレッジベースとなる文書をアップロード
              </p>
            </div>

            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                <span className="text-2xl font-bold text-white">4</span>
              </div>
              <h3 className="text-xl font-semibold mb-4">Widget設置</h3>
              <p className="text-gray-600 text-sm">
                ウェブサイトにチャットウィジェットを設置
              </p>
            </div>
          </div>

          {/* 詳細手順 */}
          <div className="space-y-12">
            {/* アカウント登録 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-2xl">
                  <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-bold mr-4">
                    1
                  </div>
                  アカウント登録
                </CardTitle>
                <CardDescription>
                  操作手順を詳しくご説明します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ①
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">「アカウント登録」ボタンをクリック</h4>
                      <p className="text-sm text-gray-600">
                        ページ上部の「アカウント登録」ボタン、または「今すぐ始める」ボタンから登録ページにアクセスします。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ②
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">テナント情報を入力</h4>
                      <p className="text-sm text-gray-600">
                        テナント名、メールアドレス、パスワードを入力します。テナント名は組織やプロジェクト名として使用されます。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ③
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">メール認証</h4>
                      <p className="text-sm text-gray-600">
                        登録後、メールアドレスに認証メールが送信されます。メール内のリンクをクリックして認証を完了してください。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ④
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">ダッシュボードにアクセス</h4>
                      <p className="text-sm text-gray-600">
                        認証完了後、ダッシュボードにログインできます。
                      </p>
                    </div>
                  </div>
                </div>
                <div className="pt-4 border-t">
                  <Link href="/login?tab=register">
                    <Button>
                      アカウント登録ページへ
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* APIキー取得と設定 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-2xl">
                  <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-bold mr-4">
                    2
                  </div>
                  APIキー登録
                </CardTitle>
                <CardDescription>
                  利用可能なLLMモデルと設定方法
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-3 flex items-center">
                    <Key className="h-5 w-5 text-primary mr-2" />
                    利用可能なLLMモデル
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">OpenAI</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="text-sm space-y-1 text-gray-600">
                          <li>• gpt-4</li>
                          <li>• gpt-4-turbo</li>
                          <li>• gpt-3.5-turbo</li>
                          <li>• gpt-4o</li>
                          <li>• gpt-4o-mini</li>
                        </ul>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Gemini</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="text-sm space-y-1 text-gray-600">
                          <li>• gemini-pro</li>
                          <li>• gemini-pro-vision</li>
                          <li>• gemini-1.5-pro</li>
                          <li>• gemini-1.5-flash</li>
                        </ul>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Anthropic</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="text-sm space-y-1 text-gray-600">
                          <li>• claude-3-opus</li>
                          <li>• claude-3-sonnet</li>
                          <li>• claude-3-haiku</li>
                          <li>• claude-3-5-sonnet</li>
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ①
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">LLMプロバイダーでAPIキーを取得</h4>
                      <p className="text-sm text-gray-600">
                        OpenAI、Google（Gemini）、AnthropicのいずれかのサービスでAPIキーを取得します。各サービスの公式サイトから取得できます。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ②
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">設定画面でAPIキーを登録</h4>
                      <p className="text-sm text-gray-600">
                        ダッシュボードの「設定」→「APIキー」から、プロバイダー、モデル、APIキーを入力して登録します。複数のAPIキーを登録することも可能です。
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                      ③
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">APIキーの検証</h4>
                      <p className="text-sm text-gray-600">
                        登録時にAPIキーの有効性が自動的に検証されます。検証に成功すると、そのAPIキーを使用してチャットボットが動作します。
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* コンテンツ登録 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-2xl">
                  <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-bold mr-4">
                    3
                  </div>
                  コンテンツ登録
                </CardTitle>
                <CardDescription>
                  どんなコンテンツが良いか、登録操作手順をご説明します
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-3 flex items-center">
                    <Lightbulb className="h-5 w-5 text-primary mr-2" />
                    どんなコンテンツが良いか
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base flex items-center">
                          <FileText className="h-4 w-4 mr-2" />
                          推奨コンテンツ
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="text-sm space-y-2 text-gray-600">
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>FAQ、よくある質問集</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>製品マニュアル、仕様書</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>社内規程、ポリシー</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>技術文書、API仕様</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>研修資料、教育コンテンツ</span>
                          </li>
                        </ul>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base flex items-center">
                          <Upload className="h-4 w-4 mr-2" />
                          対応ファイル形式
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="text-sm space-y-2 text-gray-600">
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>PDF - 文書ファイル</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>HTML - Webページ</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>Markdown - 技術文書</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>CSV - 表形式データ</span>
                          </li>
                          <li className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                            <span>TXT - テキストファイル</span>
                          </li>
                        </ul>
                      </CardContent>
                    </Card>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 flex items-center">
                    <Settings className="h-5 w-5 text-primary mr-2" />
                    登録操作手順
                  </h4>
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                        ①
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">「コンテンツ」メニューから「新規作成」をクリック</h4>
                        <p className="text-sm text-gray-600">
                          ダッシュボードの左メニューから「コンテンツ」を選択し、「新規作成」ボタンをクリックします。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                        ②
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">ファイルをアップロードまたはURLを入力</h4>
                        <p className="text-sm text-gray-600">
                          ファイルをドラッグ&ドロップするか、ファイル選択ボタンからアップロードします。または、URLを入力してWebページからコンテンツを取得することもできます。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                        ③
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">タイトル、説明、タグを入力</h4>
                        <p className="text-sm text-gray-600">
                          コンテンツのタイトル、説明、タグを入力します。タグは検索や分類に使用されます。
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-primary font-semibold text-sm flex-shrink-0 mt-0.5">
                        ④
                      </div>
                      <div>
                        <h4 className="font-medium mb-1">アップロードとインデックス化</h4>
                        <p className="text-sm text-gray-600">
                          「作成」ボタンをクリックすると、ファイルがアップロードされ、自動的にベクトル化・インデックス化されます。処理が完了すると、チャットボットがそのコンテンツを参照できるようになります。
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Widget設置手順セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Widgetの設置手順
            </h2>
            <p className="text-lg text-gray-600">
              ソースコードを交えて具体的に説明します
            </p>
          </div>

          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center text-2xl">
                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-bold mr-4">
                  4
                </div>
                Widgetの設置手順
              </CardTitle>
              <CardDescription>
                ウェブサイトにチャットウィジェットを埋め込む方法をご説明します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-semibold mb-3 flex items-center">
                  <Code className="h-5 w-5 text-primary mr-2" />
                  基本的な設置方法（HTML）
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  最も簡単な方法は、HTMLファイルの&lt;/body&gt;タグの直前に以下のコードを貼り付けることです。
                </p>
                <CodeBlock
                  code={`<!-- チャットウィジェット埋め込みコード -->
<script>
  (function(w,d,s,o,f,js,fjs){
    w['RAGChatWidget']=o;w[o]=w[o]||function(){(w[o].q=w[o].q||[]).push(arguments)};
    js=d.createElement(s),fjs=d.getElementsByTagName(s)[0];
    js.id=o;js.src=f;js.async=1;fjs.parentNode.insertBefore(js,fjs);
  }(window,document,'script','ragChat','https://cdn.rag-chatbot.com/widget.js'));
  
  ragChat('init', {
    tenantId: 'YOUR_TENANT_ID',
    apiKey: 'YOUR_API_KEY',
    theme: 'light',
    position: 'bottom-right',
    initialMessage: 'こんにちは！何かお手伝いできることはありますか？' // オプション: 初期メッセージ
  });
</script>`}
                  language="html"
                />
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-700">
                    <strong>注意:</strong> <code className="bg-blue-100 px-1 rounded">YOUR_TENANT_ID</code> と <code className="bg-blue-100 px-1 rounded">YOUR_API_KEY</code> は、ダッシュボードの「埋め込みコード」セクションから取得した実際の値に置き換えてください。
                  </p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-3 flex items-center">
                  <Code className="h-5 w-5 text-primary mr-2" />
                  Next.js/Reactでの設置方法
                </h4>
                <p className="text-sm text-gray-600 mb-4">
                  Next.jsやReactアプリケーションでは、専用のコンポーネントを使用できます。
                </p>
                <CodeBlockWithTabs
                  tabs={[
                    {
                      label: 'Next.js (App Router)',
                      code: `// app/layout.tsx または任意のページ
import { ChatWidget } from '@/components/widget/ChatWidget';

export default function Layout({ children }) {
  return (
    <html>
      <body>
        {children}
        <ChatWidget
          tenantId={process.env.NEXT_PUBLIC_WIDGET_TENANT_ID}
          apiKey={process.env.NEXT_PUBLIC_WIDGET_API_KEY}
          theme="light"
          position="bottom-right"
          initialMessage="こんにちは！何かお手伝いできることはありますか？"
        />
      </body>
    </html>
  );
}`,
                      language: 'typescript'
                    },
                    {
                      label: 'React',
                      code: `// App.js または任意のコンポーネント
import { ChatWidget } from '@/components/widget/ChatWidget';

function App() {
  return (
    <div>
      {/* あなたのアプリケーションコンテンツ */}
      <ChatWidget
        tenantId="YOUR_TENANT_ID"
        apiKey="YOUR_API_KEY"
        theme="light"
        position="bottom-right"
        initialMessage="こんにちは！何かお手伝いできることはありますか？"
      />
    </div>
  );
}

export default App;`,
                      language: 'javascript'
                    },
                    {
                      label: '環境変数の設定',
                      code: `# .env.local (Next.js)
NEXT_PUBLIC_WIDGET_TENANT_ID=your_tenant_id
NEXT_PUBLIC_WIDGET_API_KEY=your_api_key
NEXT_PUBLIC_WIDGET_URL=https://cdn.rag-chatbot.com/widget.js

# .env (React)
REACT_APP_WIDGET_TENANT_ID=your_tenant_id
REACT_APP_WIDGET_API_KEY=your_api_key
REACT_APP_WIDGET_URL=https://cdn.rag-chatbot.com/widget.js`,
                      language: 'bash'
                    }
                  ]}
                />
              </div>

              <div>
                <h4 className="font-semibold mb-3 flex items-center">
                  <Settings className="h-5 w-5 text-primary mr-2" />
                  設定オプション
                </h4>
                <div className="space-y-3">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">テーマ設定</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CodeBlock
                        code={`ragChat('init', {
  tenantId: 'YOUR_TENANT_ID',
  apiKey: 'YOUR_API_KEY',
  theme: 'light',  // 'light' または 'dark'
  position: 'bottom-right',
  initialMessage: 'こんにちは！何かお手伝いできることはありますか？' // オプション
});`}
                        language="javascript"
                      />
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">位置設定</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CodeBlock
                        code={`ragChat('init', {
  tenantId: 'YOUR_TENANT_ID',
  apiKey: 'YOUR_API_KEY',
  theme: 'light',
  position: 'bottom-right',  // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
  initialMessage: 'こんにちは！何かお手伝いできることはありますか？' // オプション
});`}
                        language="javascript"
                      />
                    </CardContent>
                  </Card>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-3 flex items-center">
                  <CheckCircle className="h-5 w-5 text-primary mr-2" />
                  設置後の確認方法
                </h4>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>ページをリロードし、画面右下（または設定した位置）にチャットアイコンが表示されることを確認</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>チャットアイコンをクリックして、チャットウィンドウが開くことを確認</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>テストメッセージを送信し、AIからの応答が返ってくることを確認</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>ブラウザの開発者ツール（F12）でコンソールエラーがないか確認</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* AI Chatbotの使い方セクション */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              AI Chatbotの使い方
            </h2>
            <p className="text-lg text-gray-600">
              効果的にAIチャットボットを活用するためのガイド
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageCircle className="h-5 w-5 text-primary mr-2" />
                  基本的な使い方
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-sm text-gray-600">
                  <p>
                    <strong>1. チャットウィジェットを開く</strong><br />
                    ウェブサイト上のチャットアイコンをクリックして、チャットウィンドウを開きます。
                  </p>
                  <p>
                    <strong>2. 質問を入力</strong><br />
                    チャット入力欄に質問を入力し、送信ボタンをクリックまたはEnterキーを押します。
                  </p>
                  <p>
                    <strong>3. 回答を確認</strong><br />
                    AIがナレッジベースから関連情報を検索し、回答を生成します。通常、数秒以内に回答が表示されます。
                  </p>
                  <p>
                    <strong>4. 続けて質問</strong><br />
                    回答に対して追加の質問をすることで、より詳細な情報を得ることができます。
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lightbulb className="h-5 w-5 text-primary mr-2" />
                  質問のコツ
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span><strong>具体的な質問をする:</strong> 「製品について教えて」よりも「製品Xの価格は？」の方が正確な回答が得られます</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span><strong>文脈を含める:</strong> 「返品方法」とだけ聞くよりも「商品を返品する方法を教えて」と聞くと、より適切な回答が得られます</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span><strong>段階的に質問:</strong> 複雑な質問は、いくつかの小さな質問に分けると理解しやすくなります</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span><strong>関連キーワードを使用:</strong> ナレッジベースに含まれる用語を使うと、より正確な回答が得られます</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 text-primary mr-2" />
                  回答の精度向上方法
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-sm text-gray-600">
                  <p>
                    <strong>ナレッジベースの充実:</strong><br />
                    より多くの関連コンテンツを登録することで、AIが参照できる情報が増え、回答の精度が向上します。
                  </p>
                  <p>
                    <strong>タグ付けの活用:</strong><br />
                    コンテンツに適切なタグを付けることで、関連する情報を効率的に検索できます。
                  </p>
                  <p>
                    <strong>定期的な更新:</strong><br />
                    古い情報を更新し、新しい情報を追加することで、常に最新の正確な回答を提供できます。
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <HelpCircle className="h-5 w-5 text-primary mr-2" />
                  よくある質問（FAQ）
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-3 text-sm">
                  <div>
                    <p className="font-medium text-gray-900 mb-1">Q: 回答が正確でない場合はどうすればいいですか？</p>
                    <p className="text-gray-600">A: ナレッジベースに該当する情報が不足している可能性があります。関連するコンテンツを追加するか、既存のコンテンツを更新してください。</p>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 mb-1">Q: 複数の言語に対応できますか？</p>
                    <p className="text-gray-600">A: はい、複数のLLMモデルを活用することで、様々な言語での対応が可能です。各言語用のコンテンツを登録することで、多言語対応を実現できます。</p>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 mb-1">Q: チャット履歴は保存されますか？</p>
                    <p className="text-gray-600">A: ダッシュボードの「統計」セクションで、チャット履歴や利用状況を確認できます。詳細な分析も可能です。</p>
                  </div>
                </div>
              </CardContent>
            </Card>
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
                  support@synergysoft.jp
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <Phone className="h-6 w-6 text-green-600" />
                </div>
                <CardTitle>Google Meet サポート</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  平日 10:00-17:00
                </CardDescription>
                <p className="text-sm text-primary font-medium mt-2">
                  こちらより申込下さい
                </p>
              </CardContent>
            </Card>

            <Card className="text-center">
              <CardHeader>
                <div className="mx-auto w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <MessageCircle className="h-6 w-6 text-purple-600" />
                </div>
                <CardTitle>AIチャットボットサポート</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  リアルタイムでサポート
                </CardDescription>
                <p className="text-sm text-primary font-medium mt-2">
                  右下のゴールデンレトリバーをクリックしてください
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="mt-12 text-center">
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle>拠点情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center space-x-2">
                  <MapPin className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    〒036-8141 弘前市松原東2-2-6
                  </span>
                </div>
                <div className="flex items-center justify-center space-x-2">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    営業時間: 平日 10:00-17:00
                  </span>
                </div>
                <div className="flex items-center justify-center space-x-2">
                  <Globe className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">
                    https://synergysoft.jp
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
                <span className="text-lg font-bold">RAG AI Chatbot Platform</span>
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
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">サポート</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>ヘルプセンター</li>
                <li>ドキュメント</li>
                <li>コミュニティ</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-4">会社</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>私達について</li>
                <li>採用情報</li>
                <li>プレス</li>
                <li>パートナー</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2024 RAG AI Chatbot Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}