/**
 * ConditionalLayoutコンポーネントのテスト
 * 
 * 条件付きレイアウトコンポーネントの動作を検証します。
 */

import React from 'react'
import { render, screen } from '@/tests/utils'
import { ConditionalLayout } from '../ConditionalLayout'

// usePathnameをモック
jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}))

describe('ConditionalLayout', () => {
  test('通常ページでのレイアウト表示', () => {
    render(
      <ConditionalLayout>
        <div>テストコンテンツ</div>
      </ConditionalLayout>
    )
    
    // コンテンツが表示されることを確認
    expect(screen.getByText('テストコンテンツ')).toBeInTheDocument()
  })

  test('ランディングページでのレイアウト表示', () => {
    jest.spyOn(require('next/navigation'), 'usePathname').mockReturnValue('/')
    
    render(
      <ConditionalLayout>
        <div>テストコンテンツ</div>
      </ConditionalLayout>
    )
    
    // コンテンツが表示されることを確認
    expect(screen.getByText('テストコンテンツ')).toBeInTheDocument()
  })
})

