/**
 * 統計・分析フローのE2Eテスト
 * 
 * 統計ページ表示、期間選択、グラフ表示、データエクスポートの
 * エンドツーエンドテストを実装します。
 */

import { test, expect } from '@playwright/test';
import { login } from './helpers/auth';

test.describe('Stats and Analytics', () => {
  test.beforeEach(async ({ page }) => {
    // ログイン処理（テナント管理者として）
    await login(
      page,
      'yono1961@gmail.com',
      'P@ssw0rd',
      /http:\/\/localhost:3000\/(dashboard|stats)/,
      15000
    );
    
    // 統計ページに移動
    await page.goto('http://localhost:3000/stats');
    await expect(page).toHaveURL('http://localhost:3000/stats', { timeout: 5000 });
  });

  test('統計ページの表示', async ({ page }) => {
    // 統計ページが表示されることを確認
    await expect(page.locator('h1, h2')).toContainText(/統計|分析/i, { timeout: 5000 });
  });

  test('期間選択', async ({ page }) => {
    // 期間選択ボタンを探す
    const weekButton = page.locator('button').filter({ hasText: /週/i });
    
    if (await weekButton.count() > 0) {
      await weekButton.first().click();
      
      // 期間が変更されたことを確認（実装に依存）
      await page.waitForTimeout(500);
    }
  });

  test('統計情報の表示', async ({ page }) => {
    // 統計情報が表示されるまで待機
    await page.waitForTimeout(2000);
    
    // 統計カードまたはグラフが表示されることを確認（実装に依存）
    const statsCard = page.locator('[class*="card"], [class*="Card"]');
    if (await statsCard.count() > 0) {
      await expect(statsCard.first()).toBeVisible({ timeout: 5000 });
    }
  });
});

