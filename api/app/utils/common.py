import re
import uuid
import hashlib
import secrets
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from functools import wraps
import asyncio
from contextlib import asynccontextmanager


class ValidationError(Exception):
    """バリデーションエラー"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ValidationUtils:
    """入力バリデーションユーティリティ"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """メールアドレスの形式チェック"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """パスワード強度チェック"""
        result = {
            'is_valid': True,
            'errors': [],
            'score': 0
        }
        
        if len(password) < 8:
            result['errors'].append('パスワードは8文字以上である必要があります')
            result['is_valid'] = False
        
        if not re.search(r'[A-Z]', password):
            result['errors'].append('大文字を含める必要があります')
            result['is_valid'] = False
        
        if not re.search(r'[a-z]', password):
            result['errors'].append('小文字を含める必要があります')
            result['is_valid'] = False
        
        if not re.search(r'\d', password):
            result['errors'].append('数字を含める必要があります')
            result['is_valid'] = False
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['errors'].append('特殊文字を含めることを推奨します')
        
        # スコア計算
        score = 0
        if len(password) >= 8:
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        if len(password) >= 12:
            score += 1
        
        result['score'] = score
        return result
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """ドメイン名の形式チェック"""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """ユーザー名の形式チェック（英数字とアンダースコアのみ）"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        pattern = r'^[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """URLの形式チェック"""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        """HTMLのサニタイズ（基本的なXSS対策）"""
        # 危険なタグと属性を除去
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form']
        dangerous_attributes = ['onclick', 'onload', 'onerror', 'onmouseover']
        
        for tag in dangerous_tags:
            html = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', html, flags=re.IGNORECASE | re.DOTALL)
            html = re.sub(f'<{tag}[^>]*/?>', '', html, flags=re.IGNORECASE)
        
        for attr in dangerous_attributes:
            html = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        
        return html
    
    @staticmethod
    def validate_file_size(size_bytes: int, max_size_mb: int = 50) -> bool:
        """ファイルサイズチェック"""
        max_size_bytes = max_size_mb * 1024 * 1024
        return size_bytes <= max_size_bytes
    
    @staticmethod
    def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
        """ファイル拡張子チェック"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in [ext.lower() for ext in allowed_extensions]


class StringUtils:
    """文字列操作ユーティリティ"""
    
    @staticmethod
    def generate_uuid() -> str:
        """UUID生成"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_api_key(prefix: str = "pk") -> str:
        """APIキー生成"""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """セキュアトークン生成"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_string(text: str, algorithm: str = "sha256") -> str:
        """文字列ハッシュ化"""
        if algorithm == "sha256":
            return hashlib.sha256(text.encode()).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """文字列切り詰め"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def slugify(text: str) -> str:
        """スラッグ化（URL用）"""
        # 日本語対応の簡易スラッグ化
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-').lower()


class DateTimeUtils:
    """日時操作ユーティリティ（日本時間対応）"""
    
    # 日本時間のタイムゾーン
    JST = timezone(timedelta(hours=9))
    
    @staticmethod
    def now() -> datetime:
        """現在時刻取得（日本時間）"""
        return datetime.now(DateTimeUtils.JST)
    
    @staticmethod
    def utc_now() -> datetime:
        """UTC現在時刻取得"""
        return datetime.utcnow().replace(tzinfo=timezone.utc)
    
    @staticmethod
    def to_jst(utc_dt: datetime) -> datetime:
        """UTC時刻を日本時間に変換"""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        return utc_dt.astimezone(DateTimeUtils.JST)
    
    @staticmethod
    def to_utc(jst_dt: datetime) -> datetime:
        """日本時間をUTC時刻に変換"""
        if jst_dt.tzinfo is None:
            jst_dt = jst_dt.replace(tzinfo=DateTimeUtils.JST)
        return jst_dt.astimezone(timezone.utc)
    
    @staticmethod
    def add_days(dt: datetime, days: int) -> datetime:
        """日数加算"""
        return dt + timedelta(days=days)
    
    @staticmethod
    def add_hours(dt: datetime, hours: int) -> datetime:
        """時間加算"""
        return dt + timedelta(hours=hours)
    
    @staticmethod
    def add_minutes(dt: datetime, minutes: int) -> datetime:
        """分加算"""
        return dt + timedelta(minutes=minutes)
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日時フォーマット"""
        return dt.strftime(format_str)
    
    @staticmethod
    def format_jst_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """日本時間で日時フォーマット"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        jst_dt = dt.astimezone(DateTimeUtils.JST)
        return jst_dt.strftime(format_str)
    
    @staticmethod
    def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
        """日時パース"""
        return datetime.strptime(date_str, format_str)
    
    @staticmethod
    def is_expired(dt: datetime) -> bool:
        """期限切れチェック（日本時間基準）"""
        now_jst = DateTimeUtils.now()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(DateTimeUtils.JST) < now_jst


class FileUtils:
    """ファイル操作ユーティリティ"""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """ファイル拡張子取得"""
        return filename.lower().split('.')[-1] if '.' in filename else ''
    
    @staticmethod
    def get_file_size_mb(size_bytes: int) -> float:
        """バイト数をMBに変換"""
        return round(size_bytes / (1024 * 1024), 2)
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """画像ファイル判定"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return FileUtils.get_file_extension(filename) in image_extensions
    
    @staticmethod
    def is_document_file(filename: str) -> bool:
        """文書ファイル判定"""
        doc_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
        return FileUtils.get_file_extension(filename) in doc_extensions


class EmailUtils:
    """メール送信ユーティリティ"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        from_email: str = "noreply@rag-chatbot.com",
        smtp_server: str = "localhost",
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> bool:
        """メール送信"""
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            if username and password:
                server.starttls()
                server.login(username, password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            logging.error(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str, reset_url: str) -> bool:
        """パスワードリセットメール送信"""
        subject = "パスワードリセットのお知らせ"
        body = f"""
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
        return EmailUtils.send_email(to_email, subject, body)


class RetryUtils:
    """リトライユーティリティ"""
    
    @staticmethod
    def retry_on_exception(
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        """リトライデコレータ"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt == max_retries:
                            raise e
                        
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                
                raise last_exception
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt == max_retries:
                            raise e
                        
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                
                raise last_exception
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator


class CacheUtils:
    """キャッシュユーティリティ"""
    
    @staticmethod
    def generate_cache_key(prefix: str, *args) -> str:
        """キャッシュキー生成"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    @staticmethod
    def generate_tenant_cache_key(tenant_id: str, key: str) -> str:
        """テナント別キャッシュキー生成"""
        return f"tenant:{tenant_id}:{key}"


class PaginationUtils:
    """ページネーションユーティリティ"""
    
    @staticmethod
    def calculate_offset(page: int, per_page: int) -> int:
        """オフセット計算"""
        return (page - 1) * per_page
    
    @staticmethod
    def calculate_total_pages(total_items: int, per_page: int) -> int:
        """総ページ数計算"""
        return (total_items + per_page - 1) // per_page
    
    @staticmethod
    def create_pagination_info(
        page: int,
        per_page: int,
        total_items: int,
        items: List[Any]
    ) -> Dict[str, Any]:
        """ページネーション情報作成"""
        total_pages = PaginationUtils.calculate_total_pages(total_items, per_page)
        
        return {
            "page": page,
            "per_page": per_page,
            "total": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "items": items
        }
