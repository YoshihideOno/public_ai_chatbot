/**
 * 認証ヘルパー関数
 * 
 * E2Eテストで使用する認証関連のヘルパー関数を定義します。
 */

import { Page, expect } from '@playwright/test';

/**
 * ログイン処理
 * 
 * 指定された認証情報でログインを実行し、成功を確認します。
 * 
 * @param page PlaywrightのPageオブジェクト
 * @param email メールアドレス
 * @param password パスワード
 * @param expectedUrl ログイン成功後に遷移するURL（正規表現可）
 * @param timeout タイムアウト（ミリ秒）
 */
export async function login(
  page: Page,
  email: string,
  password: string,
  expectedUrl: string | RegExp = /http:\/\/localhost:3000\/(dashboard|contents|users|tenants|settings|stats)/,
  timeout: number = 15000
): Promise<void> {
  // ログインページに移動
  await page.goto('http://localhost:3000/login');
  
  // ページが完全に読み込まれるまで待機
  await page.waitForLoadState('networkidle');
  
  // ログインフォームに入力
  await page.fill('input[id="login-email"]', email);
  await page.fill('input[id="login-password"]', password);
  
  // 送信ボタンをクリック
  await page.click('button[type="submit"]');
  
  // ログイン処理の完了を待機
  // エラーメッセージが表示されるか、リダイレクトが発生するまで待機
  await page.waitForTimeout(2000);
  
  // 現在のURLを確認（ログイン成功の場合は既にリダイレクトされている可能性がある）
  const currentUrl = page.url();
  
  // 既に期待されるURLに遷移している場合は、エラーチェックをスキップ
  const isAlreadyRedirected = typeof expectedUrl === 'string' 
    ? currentUrl === expectedUrl
    : expectedUrl.test(currentUrl);
  
  if (!isAlreadyRedirected) {
    // エラーメッセージが表示されていないことを確認
    const errorMessage = page.locator('[role="alert"], .text-red-600, [data-slot="alert"]');
    const errorCount = await errorMessage.count();
    
    if (errorCount > 0) {
      const errorText = await errorMessage.first().textContent();
      
      // エラーメッセージが空でない場合のみエラーをスロー
      if (errorText && errorText.trim().length > 0) {
        // ネットワークエラーの場合は、より詳細な情報を取得
        if (errorText.includes('Network Error') || errorText.includes('ネットワークエラー')) {
          // ネットワークリクエストを確認
          const response = await page.waitForResponse(
            (response) => response.url().includes('/api/v1/auth/login'),
            { timeout: 5000 }
          ).catch(() => null);
          
          if (!response) {
            throw new Error(
              `ログインAPIへのリクエストがタイムアウトしました。` +
              `現在のURL: ${currentUrl}, ` +
              `エラーメッセージ: ${errorText}`
            );
          }
          
          const status = response.status();
          if (status !== 200) {
            const responseBody = await response.text().catch(() => '');
            throw new Error(
              `ログインAPIがエラーを返しました。` +
              `ステータス: ${status}, ` +
              `レスポンス: ${responseBody}, ` +
              `現在のURL: ${currentUrl}`
            );
          }
        }
        
        throw new Error(`ログインに失敗しました: ${errorText} (現在のURL: ${currentUrl})`);
      }
    }
  }
  
  // ダッシュボードまたは指定されたURLに遷移するまで待機
  if (typeof expectedUrl === 'string') {
    await expect(page).toHaveURL(expectedUrl, { timeout });
  } else {
    await expect(page).toHaveURL(expectedUrl, { timeout });
  }
}

/**
 * テスト用ユーザーを作成（API経由）
 * 
 * 注意: この関数はバックエンドAPIが利用可能であることを前提としています。
 * 
 * @param page PlaywrightのPageオブジェクト
 * @param email メールアドレス
 * @param password パスワード
 * @param username ユーザー名
 * @param tenantName テナント名
 * @param tenantDomain テナントドメイン
 */
export async function createTestUser(
  page: Page,
  email: string,
  password: string,
  username: string,
  tenantName: string,
  tenantDomain: string
): Promise<void> {
  // テナント登録ページに移動
  await page.goto('http://localhost:3000/login?tab=register');
  
  // テナント登録フォームに入力
  await page.fill('input[name="tenant_name"]', tenantName);
  await page.fill('input[name="tenant_domain"]', tenantDomain);
  await page.fill('input[name="admin_email"]', email);
  await page.fill('input[name="admin_username"]', username);
  await page.fill('input[name="admin_password"]', password);
  await page.fill('input[name="confirm_password"]', password);
  
  // 送信ボタンをクリック
  await page.click('button[type="submit"]');
  
  // 登録成功を待機（ログインページまたはダッシュボードに遷移）
  await page.waitForTimeout(3000);
  
  // エラーメッセージが表示されていないことを確認
  const errorMessage = page.locator('[role="alert"], .text-red-600, [data-slot="alert"]');
  const errorCount = await errorMessage.count();
  
  if (errorCount > 0) {
    const errorText = await errorMessage.first().textContent();
    throw new Error(`テストユーザーの作成に失敗しました: ${errorText}`);
  }
}

