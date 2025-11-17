/**
 * Playwright設定ファイル
 * 
 * E2Eテストの実行設定を定義します。
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright設定
 * 
 * テスト実行環境、ブラウザ、タイムアウトなどの設定を行います。
 */
export default defineConfig({
  // テストディレクトリ
  testDir: './tests',
  
  // テストファイルのパターン（.spec.tsのみ）
  testMatch: /.*\.spec\.ts$/,
  
  // タイムアウト設定
  timeout: 30 * 1000, // 各テストのタイムアウト（30秒）
  expect: {
    timeout: 5 * 1000, // expectアサーションのタイムアウト（5秒）
  },
  
  // 並列実行の設定
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 1, // 進捗を見やすくするため1つずつ実行
  
  // レポーター設定（進捗を可視化）
  reporter: [
    ['list'], // リスト形式で進捗を表示
    ['html', { outputFolder: 'playwright-report', open: 'never' }], // HTMLレポートを生成（サーバーは起動しない）
  ],
  
  // 共有設定
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    // アクションのタイムアウト（クリック、入力など）
    actionTimeout: 10 * 1000, // 10秒
    // ナビゲーションのタイムアウト
    navigationTimeout: 30 * 1000, // 30秒
  },

  // プロジェクト設定（複数のブラウザでテストを実行）
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Debian/Ubuntuでの実行を考慮した設定
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
          ],
        },
      },
    },
  ],

  // Webサーバーの設定（開発サーバーを起動）
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000, // サーバー起動のタイムアウト（120秒）
    stdout: 'pipe',
    stderr: 'pipe',
  },
});

