/**
 * テストユーティリティ関数
 * 
 * テストで使用する共通のヘルパー関数を定義します。
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { AuthProvider } from '@/contexts/AuthContext'

/**
 * カスタムレンダラー（AuthProviderを含む）
 * 
 * 認証コンテキストが必要なコンポーネントのテストで使用します。
 * 
 * @param ui レンダリングするコンポーネント
 * @param options レンダリングオプション
 * @returns レンダリング結果とユーティリティ関数
 */
function renderWithAuth(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <AuthProvider>{children}</AuthProvider>
  }

  return render(ui, { wrapper: Wrapper, ...options })
}

/**
 * モックAPIレスポンスを作成
 * 
 * @param data レスポンスデータ
 * @param status ステータスコード
 * @returns モックレスポンス
 */
export function createMockResponse<T>(data: T, status: number = 200) {
  return {
    data,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: {},
    config: {},
  }
}

/**
 * モックAPIエラーを作成
 * 
 * @param message エラーメッセージ
 * @param status ステータスコード
 * @returns モックエラー
 */
interface MockApiError extends Error {
  response: {
    data: { error: { message: string } }
    status: number
    statusText: string
    headers: Record<string, unknown>
    config: Record<string, unknown>
  }
}

export function createMockError(message: string, status: number = 400) {
  const error: MockApiError = Object.assign(new Error(message), {
    response: {
      data: { error: { message } },
      status,
      statusText: 'Error',
      headers: {},
      config: {},
    },
  })
  return error
}

// カスタムレンダラーをエクスポート
export * from '@testing-library/react'
export { renderWithAuth as render }

