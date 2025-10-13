import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'お問い合わせ - AIチャットボット',
  description: 'AIチャットボットに関するお問い合わせフォーム',
};

export default function Contact() {
  return (
    <div className='min-h-screen bg-gray-50 py-8'>
      <div className='container mx-auto px-4 max-w-4xl'>
        <div className='bg-white rounded-lg shadow-md p-8'>
          <h1 className='text-3xl font-bold text-gray-800 mb-6'>
            お問い合わせ
          </h1>

          <div className='space-y-8'>
            <section>
              <h2 className='text-xl font-semibold text-gray-800 mb-4'>
                お問い合わせ方法
              </h2>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
                <div className='bg-blue-50 p-6 rounded-lg border border-blue-200'>
                  <h3 className='font-semibold text-blue-800 mb-3 flex items-center'>
                    <svg
                      className='w-5 h-5 mr-2'
                      fill='none'
                      stroke='currentColor'
                      viewBox='0 0 24 24'
                    >
                      <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        strokeWidth={2}
                        d='M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
                      />
                    </svg>
                    メールでのお問い合わせ
                  </h3>
                  <p className='text-gray-600 mb-3'>
                    技術的な質問やご要望は、以下のメールアドレスまでお送りください。
                  </p>
                  <a
                    href='mailto:support@ai-chatbot.example.com'
                    className='text-blue-600 hover:text-blue-800 font-medium'
                  >
                    support@ai-chatbot.example.com
                  </a>
                </div>

                <div className='bg-green-50 p-6 rounded-lg border border-green-200'>
                  <h3 className='font-semibold text-green-800 mb-3 flex items-center'>
                    <svg
                      className='w-5 h-5 mr-2'
                      fill='none'
                      stroke='currentColor'
                      viewBox='0 0 24 24'
                    >
                      <path
                        strokeLinecap='round'
                        strokeLinejoin='round'
                        strokeWidth={2}
                        d='M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z'
                      />
                    </svg>
                    チャットでのサポート
                  </h3>
                  <p className='text-gray-600 mb-3'>
                    簡単な質問は、アプリ内のチャット機能をご利用ください。
                  </p>
                  <a
                    href='/'
                    className='text-green-600 hover:text-green-800 font-medium'
                  >
                    チャットを開始する →
                  </a>
                </div>
              </div>
            </section>

            <section>
              <h2 className='text-xl font-semibold text-gray-800 mb-4'>
                よくある質問
              </h2>
              <div className='space-y-4'>
                <div className='border-l-4 border-orange-500 pl-4'>
                  <h3 className='font-semibold text-gray-800 mb-2'>
                    Q. AIチャットボットはどのような質問に答えてくれますか？
                  </h3>
                  <p className='text-gray-600'>
                    A.
                    一般的な知識、技術的な質問、日常的な相談など、幅広いトピックに対応しています。
                    ただし、医療や法律に関する重要な判断が必要な場合は、専門家にご相談ください。
                  </p>
                </div>

                <div className='border-l-4 border-orange-500 pl-4'>
                  <h3 className='font-semibold text-gray-800 mb-2'>
                    Q. 利用料金はかかりますか？
                  </h3>
                  <p className='text-gray-600'>
                    A. 現在はベータ版として無料でご利用いただけます。
                    将来的な料金体系については、正式リリース時にご案内いたします。
                  </p>
                </div>

                <div className='border-l-4 border-orange-500 pl-4'>
                  <h3 className='font-semibold text-gray-800 mb-2'>
                    Q. プライバシーは保護されますか？
                  </h3>
                  <p className='text-gray-600'>
                    A. はい、お客様のプライバシーを最優先に考えています。
                    会話内容は適切に管理され、第三者と共有されることはありません。
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className='text-xl font-semibold text-gray-800 mb-4'>
                お問い合わせフォーム
              </h2>
              <div className='bg-gray-100 p-6 rounded-lg'>
                <p className='text-gray-600 mb-4'>
                  詳細なお問い合わせは、以下のフォームをご利用ください。
                </p>
                <form className='space-y-4'>
                  <div>
                    <label
                      htmlFor='name'
                      className='block text-sm font-medium text-gray-700 mb-1'
                    >
                      お名前 *
                    </label>
                    <input
                      type='text'
                      id='name'
                      name='name'
                      required
                      className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500'
                    />
                  </div>

                  <div>
                    <label
                      htmlFor='email'
                      className='block text-sm font-medium text-gray-700 mb-1'
                    >
                      メールアドレス *
                    </label>
                    <input
                      type='email'
                      id='email'
                      name='email'
                      required
                      className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500'
                    />
                  </div>

                  <div>
                    <label
                      htmlFor='subject'
                      className='block text-sm font-medium text-gray-700 mb-1'
                    >
                      件名 *
                    </label>
                    <input
                      type='text'
                      id='subject'
                      name='subject'
                      required
                      className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500'
                    />
                  </div>

                  <div>
                    <label
                      htmlFor='message'
                      className='block text-sm font-medium text-gray-700 mb-1'
                    >
                      メッセージ *
                    </label>
                    <textarea
                      id='message'
                      name='message'
                      rows={5}
                      required
                      className='w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500'
                    ></textarea>
                  </div>

                  <button
                    type='submit'
                    className='w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-colors'
                  >
                    送信する
                  </button>
                </form>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
