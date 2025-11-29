"""
メール送信サービス（Resend）

このファイルはトランザクションメール送信を担当します。
領収書送信、使用量警告、月次レポート等の送信機能を提供します。
"""

from typing import Optional, Dict, Any
from app.core.config import settings
from app.utils.logging import BusinessLogger, ErrorLogger, logger

try:
    import resend  # type: ignore
except Exception:  # ランタイム依存を緩和
    resend = None  # type: ignore


class EmailService:
    """
    メール送信サービス
    
    Resend APIを使用してメール送信を行います。
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
            logger.warning("Resend未設定のためメール送信をスキップ")
            return False
        
        try:
            # Resend 2.x系の新しいAPIを使用
            params = {
                "from": settings.EMAIL_FROM_ADDRESS,  # 環境変数から取得
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # 新しいAPIでメール送信（非同期実行、タイムアウト設定付き）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(params)  # type: ignore
                ),
                timeout=30.0  # 30秒のタイムアウト
            )
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"領収書メール送信完了: {response.id}")
                return True
            else:
                logger.error("メール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            logger.error(f"メール送信失敗: {str(e)}")
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
            logger.warning("Resend未設定のためメール送信をスキップ")
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
                "from": settings.EMAIL_FROM_ADDRESS,  # 環境変数から取得
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            response = resend.Emails.send(params)  # type: ignore
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"パスワードリセットメール送信完了: {response.id}")
                return True
            else:
                logger.error("パスワードリセットメール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            logger.error(f"パスワードリセットメール送信失敗: {str(e)}")
            return False

    @staticmethod
    async def send_user_registration_email(to_email: str, username: str, confirmation_url: str) -> bool:
        """
        ユーザー登録確認メール送信
        
        引数:
            to_email: 送信先メールアドレス
            username: ユーザー名
            confirmation_url: 確認URL
        戻り値:
            bool: 送信成功可否
        """
        subject = "アカウント登録の確認"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-bottom: 20px;">アカウント登録の確認</h2>
                <p>こんにちは、{username}さん</p>
                <p>AI Chatbot Platformへのご登録ありがとうございます。</p>
                <p>アカウントを有効化するために、以下のリンクをクリックしてください：</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{confirmation_url}" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        アカウントを有効化
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    このリンクは24時間で期限切れになります。<br>
                    心当たりのない場合は、このメールを無視してください。
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    AI Chatbot Platform<br>
                    このメールは自動送信されています。
                </p>
            </div>
        </body>
        </html>
        """
        
        # 開発環境ではメール送信をスキップし、ログに確認URLを出力
        if settings.ENVIRONMENT == "development":
            logger.info(f"【開発環境】ユーザー登録確認メール送信（スキップ）")
            logger.info(f"送信先: {to_email}")
            logger.info(f"ユーザー名: {username}")
            logger.info(f"確認URL: {confirmation_url}")
            logger.info(f"↑ このURLをブラウザで開いてテストしてください")
            return True
        
        # 本番環境ではResend APIを使用
        if not settings.RESEND_API_KEY or resend is None:
            logger.warning("Resend未設定のためメール送信をスキップ")
            logger.debug(f"RESEND_API_KEY設定状況: {'設定あり' if settings.RESEND_API_KEY else '未設定'}")
            logger.debug(f"EMAIL_FROM_ADDRESS: {settings.EMAIL_FROM_ADDRESS}")
            logger.debug(f"resendモジュール: {'インポート成功' if resend else 'インポート失敗'}")
            return False
        
        try:
            params = {
                "from": settings.EMAIL_FROM_ADDRESS,  # 環境変数から取得
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # デバッグログ（LOG_LEVEL=debugの場合のみ出力）
            logger.debug(f"メール送信開始 - to: {to_email}, from: {settings.EMAIL_FROM_ADDRESS}")
            logger.debug(f"確認URL: {confirmation_url}")
            
            # 非同期でメール送信を実行（タイムアウト設定付き）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None, 
                    lambda: resend.Emails.send(params)  # type: ignore
                ),
                timeout=30.0  # 30秒のタイムアウト
            )
            
            logger.debug(f"Resend API Response: {response}")
            
            # レスポンスの検証を緩和（Resend APIは成功時に様々な形式を返す可能性がある）
            if response:
                # response.id がある場合はそれを使用、なければ response 自体をログ
                response_id = getattr(response, 'id', None) or str(response)
                logger.info(f"ユーザー登録確認メール送信完了: {response_id}")
                return True
            else:
                logger.error("ユーザー登録確認メール送信レスポンスが無効です")
                logger.debug(f"Invalid response: {response}")
                return False
                
        except asyncio.TimeoutError:
            logger.error(f"ユーザー登録確認メール送信タイムアウト（30秒）")
            return False
        except Exception as e:
            logger.error(f"ユーザー登録確認メール送信失敗: {str(e)}")
            logger.debug(f"Exception type: {type(e).__name__}")
            logger.debug(f"Exception details: {repr(e)}")
            import traceback
            logger.debug(f"Traceback:\n{traceback.format_exc()}")
            return False

    @staticmethod
    async def send_trial_reminder_email(
        to_email: str, 
        username: str, 
        tenant_name: str, 
        days_remaining: int, 
        trial_end_date
    ) -> bool:
        """
        お試し利用期間終了前のリマインダーメール送信
        
        引数:
            to_email: 送信先メールアドレス
            username: ユーザー名
            tenant_name: テナント名
            days_remaining: 残り日数
            trial_end_date: お試し利用終了日
        戻り値:
            bool: 送信成功可否
        """
        subject = f"お試し利用期間終了まで{days_remaining}日のお知らせ"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-bottom: 20px;">お試し利用期間終了のお知らせ</h2>
                <p>こんにちは、{username}さん</p>
                <p>{tenant_name}のお試し利用期間が<strong>{days_remaining}日後</strong>に終了します。</p>
                
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;">
                        <strong>終了日時:</strong> {trial_end_date.strftime('%Y年%m月%d日 %H:%M')}
                    </p>
                </div>
                
                <p>サービスを継続してご利用いただくには、サブスクリプションにご登録ください。</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL or 'http://localhost:3000'}/billing/plans" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        サブスクリプションに登録
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    お試し利用期間終了後は、サービスをご利用いただけません。<br>
                    ご不明な点がございましたら、お気軽にお問い合わせください。
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    AI Chatbot Platform<br>
                    このメールは自動送信されています。
                </p>
            </div>
        </body>
        </html>
        """
        
        # 開発環境ではメール送信をスキップし、ログに情報を出力
        if settings.ENVIRONMENT == "development":
            logger.info(f"【開発環境】リマインダーメール送信（スキップ）")
            logger.info(f"送信先: {to_email}")
            logger.info(f"ユーザー名: {username}")
            logger.info(f"テナント名: {tenant_name}")
            logger.info(f"残り日数: {days_remaining}日")
            logger.info(f"終了日: {trial_end_date}")
            return True
        
        # 本番環境ではResend APIを使用
        if not settings.RESEND_API_KEY or resend is None:
            logger.warning("Resend未設定のためメール送信をスキップ")
            return False
        
        try:
            params = {
                "from": settings.EMAIL_FROM_ADDRESS,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # 非同期でメール送信を実行（タイムアウト設定付き）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(params)  # type: ignore
                ),
                timeout=30.0  # 30秒のタイムアウト
            )
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"リマインダーメール送信完了: {response.id}")
                return True
            else:
                logger.error("リマインダーメール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            logger.error(f"リマインダーメール送信失敗: {str(e)}")
            return False

    @staticmethod
    async def send_content_processing_success_email(
        to_email: str,
        username: str,
        file_title: str,
        file_name: str,
        chunk_count: int
    ) -> bool:
        """
        コンテンツ処理成功メール送信
        
        引数:
            to_email: 送信先メールアドレス
            username: ユーザー名
            file_title: ファイルタイトル
            file_name: ファイル名
            chunk_count: チャンク数
        戻り値:
            bool: 送信成功可否
        """
        subject = "コンテンツ処理が完了しました"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #28a745; margin-bottom: 20px;">✓ コンテンツ処理が完了しました</h2>
                <p>こんにちは、{username}さん</p>
                <p>以下のファイルの処理が正常に完了しました：</p>
                
                <div style="background-color: white; border: 1px solid #dee2e6; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>ファイル名:</strong> {file_title}</p>
                    <p style="margin: 5px 0 0 0;"><strong>ファイル:</strong> {file_name}</p>
                    <p style="margin: 5px 0 0 0;"><strong>チャンク数:</strong> {chunk_count}</p>
                </div>
                
                <p>このファイルは検索可能になりました。チャットボットで質問できます。</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL or 'http://localhost:3000'}/contents" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        コンテンツ一覧を確認
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    AI Chatbot Platform<br>
                    このメールは自動送信されています。
                </p>
            </div>
        </body>
        </html>
        """
        
        # 開発環境ではメール送信をスキップし、ログに情報を出力
        if settings.ENVIRONMENT == "development":
            logger.info(f"【開発環境】コンテンツ処理成功メール送信（スキップ）")
            logger.info(f"送信先: {to_email}")
            logger.info(f"ユーザー名: {username}")
            logger.info(f"ファイル名: {file_title}")
            logger.info(f"ファイル: {file_name}")
            logger.info(f"チャンク数: {chunk_count}")
            return True
        
        # 本番環境ではResend APIを使用
        if not settings.RESEND_API_KEY or resend is None:
            logger.warning("Resend未設定のためメール送信をスキップ")
            return False
        
        try:
            params = {
                "from": settings.EMAIL_FROM_ADDRESS,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # 非同期でメール送信を実行（タイムアウト設定付き）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(params)  # type: ignore
                ),
                timeout=30.0  # 30秒のタイムアウト
            )
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"コンテンツ処理成功メール送信完了: {response.id}")
                return True
            else:
                logger.error("コンテンツ処理成功メール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            logger.error(f"コンテンツ処理成功メール送信失敗: {str(e)}")
            return False

    @staticmethod
    async def send_content_processing_failure_email(
        to_email: str,
        username: str,
        file_title: str,
        file_name: str,
        error_message: str
    ) -> bool:
        """
        コンテンツ処理失敗メール送信
        
        引数:
            to_email: 送信先メールアドレス
            username: ユーザー名
            file_title: ファイルタイトル
            file_name: ファイル名
            error_message: エラーメッセージ
        戻り値:
            bool: 送信成功可否
        """
        subject = "コンテンツ処理に失敗しました"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #dc3545; margin-bottom: 20px;">⚠ コンテンツ処理に失敗しました</h2>
                <p>こんにちは、{username}さん</p>
                <p>以下のファイルの処理中にエラーが発生しました：</p>
                
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>ファイル名:</strong> {file_title}</p>
                    <p style="margin: 5px 0 0 0;"><strong>ファイル:</strong> {file_name}</p>
                    <p style="margin: 10px 0 0 0;"><strong>エラー内容:</strong></p>
                    <p style="margin: 5px 0 0 0; color: #721c24;">{error_message}</p>
                </div>
                
                <p>ファイルを再アップロードするか、サポートにお問い合わせください。</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.APP_URL or 'http://localhost:3000'}/contents" 
                       style="background-color: #dc3545; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        コンテンツ一覧を確認
                    </a>
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    AI Chatbot Platform<br>
                    このメールは自動送信されています。
                </p>
            </div>
        </body>
        </html>
        """
        
        # 開発環境ではメール送信をスキップし、ログに情報を出力
        if settings.ENVIRONMENT == "development":
            logger.info(f"【開発環境】コンテンツ処理失敗メール送信（スキップ）")
            logger.info(f"送信先: {to_email}")
            logger.info(f"ユーザー名: {username}")
            logger.info(f"ファイル名: {file_title}")
            logger.info(f"ファイル: {file_name}")
            logger.info(f"エラー内容: {error_message}")
            return True
        
        # 本番環境ではResend APIを使用
        if not settings.RESEND_API_KEY or resend is None:
            logger.warning("Resend未設定のためメール送信をスキップ")
            return False
        
        try:
            params = {
                "from": settings.EMAIL_FROM_ADDRESS,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
            
            # 非同期でメール送信を実行（タイムアウト設定付き）
            import asyncio
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: resend.Emails.send(params)  # type: ignore
                ),
                timeout=30.0  # 30秒のタイムアウト
            )
            
            if response and hasattr(response, 'id'):
                BusinessLogger.info(f"コンテンツ処理失敗メール送信完了: {response.id}")
                return True
            else:
                logger.error("コンテンツ処理失敗メール送信レスポンスが無効です")
                return False
                
        except Exception as e:
            logger.error(f"コンテンツ処理失敗メール送信失敗: {str(e)}")
            return False


