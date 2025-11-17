/**
 * 設定管理フローのE2Eテスト
 * 
 * 設定ページ表示、APIキー管理、チャンク設定、LLMモデル設定、Webhook設定の
 * エンドツーエンドテストを実装します。
 */

import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

test.describe('Settings Management', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理（テナント管理者として）
    await login(
      page,
      'yono1961@gmail.com',
      'P@ssw0rd',
      /http:\/\/localhost:3000\/(dashboard|settings)/,
      15000
    );
    
    // 設定ページに移動
    await page.goto('http://localhost:3000/settings');
    await expect(page).toHaveURL('http://localhost:3000/settings', { timeout: 5000 });
  });

  test('設定ページの表示', async ({ page }) => {
    // 設定ページが表示されることを確認
    await expect(page.locator('h1, h2')).toContainText(/設定/i, { timeout: 5000 });
  });

  test('APIキー管理セクションの表示', async ({ page }) => {
    // APIキー管理セクションが表示されることを確認
    // strict mode violationを避けるため、.first()を使用
    await expect(page.locator('text=/APIキー/i').first()).toBeVisible({ timeout: 5000 });
  });

  test('チャンク設定セクションの表示', async ({ page }) => {
    // チャンク設定セクションが表示されることを確認
    // 「チャンクサイズ」ラベルを確認（より具体的なセレクタ）
    await expect(page.locator('label:has-text("チャンクサイズ")')).toBeVisible({ timeout: 5000 });
  });

  test('LLMモデル設定セクションの表示', async ({ page }) => {
    // LLMモデル設定セクションが表示されることを確認
    // 「テナント設定 - LLMモデル」タイトルを確認（より具体的なセレクタ）
    await expect(page.locator('text=テナント設定 - LLMモデル')).toBeVisible({ timeout: 5000 });
  });
});

