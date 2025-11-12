/**
 * ロガーユーティリティ
 * 
 * 日時付きの構造化ログ出力を提供します。
 * バックエンドのログ形式と統一し、運用・監視を容易にします。
 * 
 * 使用方法:
 *   import { logger } from '@/utils/logger';
 *   logger.info('処理開始', { userId: '123' });
 *   logger.error('エラー発生', error);
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  service: string;
  environment: string;
  data?: unknown;
}

class Logger {
  private serviceName: string = 'rag-chatbot-frontend';
  private environment: string;

  constructor() {
    this.environment = process.env.NODE_ENV || 'development';
  }

  /**
   * タイムスタンプをISO形式でフォーマット（JST対応）
   * 
   * 戻り値:
   *   string: ISO形式のタイムスタンプ（YYYY-MM-DDTHH:mm:ss.sss+09:00）
   */
  private formatTimestamp(): string {
    const now = new Date();
    // JST（UTC+9）に変換
    const jstOffset = 9 * 60; // 9時間を分に変換
    const jstTime = new Date(now.getTime() + (jstOffset * 60 * 1000));
    return jstTime.toISOString().replace('Z', '+09:00');
  }

  /**
   * ログエントリをフォーマット
   * 
   * 引数:
   *   level: ログレベル
   *   message: ログメッセージ
   *   data: 追加データ（オプション）
   * 
   * 戻り値:
   *   string: JSON形式のログエントリ
   */
  private formatLog(level: LogLevel, message: string, data?: unknown): string {
    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level,
      message,
      service: this.serviceName,
      environment: this.environment,
      ...(data && { data }),
    };
    return JSON.stringify(entry);
  }

  /**
   * エラーオブジェクトをシリアライズ可能な形式に変換
   * 
   * 引数:
   *   error: エラーオブジェクト
   * 
   * 戻り値:
   *   object: シリアライズ可能なエラー情報
   */
  private serializeError(error: unknown): unknown {
    if (error instanceof Error) {
      return {
        name: error.name,
        message: error.message,
        stack: error.stack,
        ...(error instanceof Error && 'cause' in error && { cause: error.cause }),
      };
    }
    return error;
  }

  /**
   * DEBUGレベルでログを出力
   * 開発環境でのみ出力されます。
   * 
   * 引数:
   *   message: ログメッセージ
   *   data: 追加データ（オプション）
   */
  debug(message: string, data?: unknown): void {
    if (this.environment === 'development') {
      console.debug(this.formatLog('debug', message, data));
    }
  }

  /**
   * INFOレベルでログを出力
   * 
   * 引数:
   *   message: ログメッセージ
   *   data: 追加データ（オプション）
   */
  info(message: string, data?: unknown): void {
    console.log(this.formatLog('info', message, data));
  }

  /**
   * WARNレベルでログを出力
   * 
   * 引数:
   *   message: ログメッセージ
   *   data: 追加データ（オプション）
   */
  warn(message: string, data?: unknown): void {
    console.warn(this.formatLog('warn', message, data));
  }

  /**
   * ERRORレベルでログを出力
   * 
   * 引数:
   *   message: ログメッセージ
   *   error: エラーオブジェクト（オプション）
   */
  error(message: string, error?: unknown): void {
    const errorData = error ? this.serializeError(error) : undefined;
    console.error(this.formatLog('error', message, errorData));
  }
}

export const logger = new Logger();

