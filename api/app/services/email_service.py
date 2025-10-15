"""
メール送信サービス（Resend）

このファイルはトランザクションメール送信を担当します。
領収書送信、使用量警告、月次レポート等の送信機能を提供します。
"""

from typing import Optional, Dict, Any
from app.core.config import settings
from app.utils.logging import BusinessLogger, ErrorLogger

try:
    import resend  # type: ignore
except Exception:  # ランタイム依存を緩和
    resend = None  # type: ignore


class EmailService:
    """
    メール送信サービス
    
    Resend APIを用いてメール送信を行います。
    """

    def __init.subclass__:
        pass

    @staticmethod
    async def send_receipt_email(to_email: str, subject: str, html: str) -> bool:
        """
        領収書メール送信
        
        引数:
            to_email: 送信先メールアドレス
            subject: 件名
            html: HTML本文
        戻り値:
            bool: 送信成功可否
        """
        if not settings.RESEND_API_KEY or resend is None:
            ErrorLogger.error("Resend未設定のためメール送信をスキップ")
            return False
        try:
            resend.api_key = settings.RESEND_API_KEY  # type: ignore
            # 実運用ではasync対応のクライアントorスレッド/タスクで実行
            resend.Emails.send(  # type: ignore
                {
                    "from": "billing@rag-ai.com",
                    "to": to_email,
                    "subject": subject,
                    "html": html,
                }
            )
            BusinessLogger.info("領収書メール送信完了")
            return True
        except Exception as e:
            ErrorLogger.error(f"メール送信失敗: {str(e)}")
            return False


