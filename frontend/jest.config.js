/**
 * Jest設定ファイル
 * 
 * Next.js 15用のJest設定です。
 * @next/jestが利用できないため、手動で設定します。
 */

// Jestのカスタム設定
const customJestConfig = {
  // テスト環境
  testEnvironment: 'jest-environment-jsdom',
  
  // セットアップファイル
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  
  // テストファイルのパターン（__tests__ディレクトリ内のファイルのみ）
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.[jt]s?(x)',
    '<rootDir>/src/**/__tests__/**/*.test.[jt]s?(x)',
  ],
  
  // テストファイルから除外するパターン
  testPathIgnorePatterns: [
    '/node_modules/',
    '/.next/',
    '/tests/', // PlaywrightのE2Eテストディレクトリを除外
  ],
  
  // カバレッジの収集対象
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/__tests__/**',
  ],
  
  // カバレッジの閾値
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  
  // モジュールの拡張子
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  
  // モジュールパスの解決
  moduleNameMapper: {
    // testsディレクトリのパスエイリアスを優先的に解決
    '^@/tests/(.*)$': '<rootDir>/tests/$1',
    // Next.jsのパスエイリアス（@/*）を解決
    '^@/(.*)$': '<rootDir>/src/$1',
    // CSSモジュールのモック
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // 画像ファイルのモック
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$': '<rootDir>/tests/__mocks__/fileMock.js',
  },
  
  // 変換設定
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', {
      presets: [
        ['next/babel', {
          'preset-react': {
            runtime: 'automatic',
          },
        }],
      ],
    }],
  },
  
  // モジュールの解決
  moduleDirectories: ['node_modules', '<rootDir>'],
}

module.exports = customJestConfig
