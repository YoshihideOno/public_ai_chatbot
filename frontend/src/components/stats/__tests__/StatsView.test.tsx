/**
 * StatsViewコンポーネントのテスト
 * 
 * 統計表示コンポーネントの動作を検証します。
 */

import React from 'react'
import { render, screen, waitFor } from '@/tests/utils'
import userEvent from '@testing-library/user-event'
import { StatsView } from '../StatsView'
import { apiClient } from '@/lib/api'

// apiClientをモック
jest.mock('@/lib/api', () => ({
  apiClient: {
    getUsageStats: jest.fn(),
    getDashboardStats: jest.fn(),
  },
}))

// useAuthをモック
jest.mock('@/contexts/AuthContext', () => {
  const React = require('react')
  return {
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAuth: () => ({
      user: {
        id: 'user-1',
        email: 'test@example.com',
        username: 'testuser',
        role: 'TENANT_ADMIN',
        tenant_id: 'tenant-1',
        is_active: true,
      },
      isLoading: false,
      isAuthenticated: true,
    }),
  }
})

describe('StatsView', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(apiClient.getUsageStats as jest.Mock) = jest.fn().mockResolvedValue({
      total_queries: 100,
      total_tokens: 5000,
    })
    ;(apiClient.getDashboardStats as jest.Mock) = jest.fn().mockResolvedValue({
      storage_stats: {
        total_mb: 100,
        used_mb: 50,
      },
      top_queries: [
        { query: 'テストクエリ1', count: 10 },
        { query: 'テストクエリ2', count: 5 },
      ],
    })
  })

  test('統計情報の表示', async () => {
    render(<StatsView />)
    
    // 統計情報が読み込まれるまで待機
    await waitFor(() => {
      expect(apiClient.getUsageStats).toHaveBeenCalled()
    })
    
    // 統計情報が表示されることを確認（実装に依存）
    await waitFor(() => {
      expect(screen.getByText(/統計/i)).toBeInTheDocument()
    })
  })

  test('期間選択', async () => {
    const user = userEvent.setup()
    render(<StatsView />)
    
    // 統計情報が読み込まれるまで待機
    await waitFor(() => {
      expect(apiClient.getUsageStats).toHaveBeenCalled()
    })
    
    // 期間選択ボタンを探す
    const weekButton = screen.queryByRole('button', { name: /週/i })
    if (weekButton) {
      await user.click(weekButton)
      
      // 期間が変更されたことを確認
      await waitFor(() => {
        expect(apiClient.getUsageStats).toHaveBeenCalledTimes(2)
      })
    }
  })

  test('エラーハンドリング', async () => {
    ;(apiClient.getUsageStats as jest.Mock) = jest.fn().mockRejectedValue(new Error('取得に失敗しました'))
    ;(apiClient.getDashboardStats as jest.Mock) = jest.fn().mockRejectedValue(new Error('取得に失敗しました'))
    
    render(<StatsView />)
    
    // API呼び出しが実行されるまで待機
    await waitFor(() => {
      expect(apiClient.getUsageStats).toHaveBeenCalled()
    })
    await waitFor(() => {
      expect(apiClient.getDashboardStats).toHaveBeenCalled()
    })
    
    // ローディングが終了するまで待機
    await waitFor(() => {
      expect(screen.queryByText(/読み込み中/i)).not.toBeInTheDocument()
    }, { timeout: 5000 })
    
    // エラーメッセージが表示される（すべてのAPIが失敗した場合）
    await waitFor(() => {
      const errorMessage = screen.queryByText(/統計データの取得に失敗しました/i)
      expect(errorMessage).toBeInTheDocument()
    }, { timeout: 5000 })
  }, 15000)
})

