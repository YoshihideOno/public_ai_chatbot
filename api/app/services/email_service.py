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

    def __init__(self):
        """初期化"""
        if resend and settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY

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
            # Resend 2.x系の新しいAPIを使用
            params = {
                "from": "billing@rag-ai.com",
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # 新しいAPIでメール送信
            response = resend.Emails.send(params)  # type: ignore
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"領収書メール送信完了: {response.id}")
                return True
            else:
                ErrorLogger.error("メール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            ErrorLogger.error(f"メール送信失敗: {str(e)}")
            return False

    @staticmethod
    async def send_password_reset_email(to_email: str, reset_token: str, reset_url: str) -> bool:
        """
        パスワードリセットメール送信
        
        引数:
            to_email: 送信先メールアドレス
            reset_token: リセットトークン
            reset_url: リセットURL
        戻り値:
            bool: 送信成功可否
        """
        if not settings.RESEND_API_KEY or resend is None:
            ErrorLogger.error("Resend未設定のためメール送信をスキップ")
            return False
        
        subject = "パスワードリセットのお知らせ"
        html = f"""
        <html>
        <body>
            <h2>パスワードリセット</h2>
            <p>以下のリンクをクリックしてパスワードをリセットしてください：</p>
            <p><a href="{reset_url}?token={reset_token}">パスワードリセット</a></p>
            <p>このリンクは1時間で期限切れになります。</p>
            <p>心当たりのない場合は、このメールを無視してください。</p>
        </body>
        </html>
        """
        
        try:
            params = {
                "from": "noreply@rag-ai.com",
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            response = resend.Emails.send(params)  # type: ignore
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"パスワードリセットメール送信完了: {response.id}")
                return True
            else:
                ErrorLogger.error("パスワードリセットメール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            ErrorLogger.error(f"パスワードリセットメール送信失敗: {str(e)}")
            return False


