"""
VirtuTune - Django Settings

仮想ギターと進捗管理機能を持つWebアプリケーション
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================================
# 環境変数設定
# =====================================================


def get_env_var(
    var_name: str, required: bool = False, default: str = None, cast: type = None
) -> str | None:
    """
    環境変数を取得する

    Args:
        var_name: 環境変数名
        required: 必須フラグ
        default: デフォルト値
        cast: 型変換関数

    Returns:
        環境変数の値、またはデフォルト値
    """
    from decouple import config

    if required and default is None:
        try:
            if cast:
                return config(var_name, cast=cast)
            return config(var_name)
        except Exception:
            from django.core.exceptions import ImproperlyConfigured

            raise ImproperlyConfigured(f"{var_name} is required but not set")
    if cast:
        return config(var_name, default=default, cast=cast)
    return config(var_name, default=default)


# =====================================================
# セキュリティ設定
# =====================================================

SECRET_KEY = get_env_var(
    "SECRET_KEY", required=True, default="django-insecure-development-key-only"
)
DEBUG = get_env_var("DEBUG", default=True, cast=bool)

# DEBUGモードの場合はすべてのホストを許可
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = get_env_var("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")

# セッション設定
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # ブラウザを閉じるとセッション無効

# パスワードリセット
PASSWORD_RESET_TIMEOUT = 3600  # 1時間（秒）


# =====================================================
# アプリケーション定義
# =====================================================

INSTALLED_APPS = [
    # Django組み込み
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # サードパーティ
    "django_extensions",
    "channels",
    "django_ratelimit",
    "django_celery_beat",  # Celery定期実行スケジューラー
    # アプリ
    "apps.core",
    "apps.guitar",
    "apps.progress",
    "apps.users",
    "apps.reminders",  # リマインダー機能
    "apps.game",
    "apps.ranking",
    "apps.mobile",
    "apps.websocket",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# =====================================================
# データベース設定
# =====================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =====================================================
# キャッシュ設定
# =====================================================

REDIS_URL = get_env_var("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "virtutune",
        "TIMEOUT": 300,
    }
}


# =====================================================
# 認証設定
# =====================================================

AUTH_USER_MODEL = "users.User"
LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "guitar"
LOGOUT_REDIRECT_URL = "users:login"


# =====================================================
# パスワードバリデーション
# =====================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# =====================================================
# 国際化設定
# =====================================================

LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True


# =====================================================
# 静的ファイル設定
# =====================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =====================================================
# Channels (WebSocket) 設定
# =====================================================

# テスト時はインメモリチャネルレイヤーを使用
import sys

if "pytest" in sys.modules or any(arg in sys.argv for arg in ["test", "pytest"]):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }


# =====================================================
# Celery 設定
# =====================================================

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


# =====================================================
# メール設定
# =====================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # 開発環境
EMAIL_HOST = get_env_var("EMAIL_HOST", default="localhost")
EMAIL_PORT = int(get_env_var("EMAIL_PORT", default="587"))
EMAIL_USE_TLS = get_env_var("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = get_env_var("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = get_env_var("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = get_env_var(
    "DEFAULT_FROM_EMAIL", default="noreply@virtutune.example.com"
)


# =====================================================
# セキュリティヘッダー（本番環境用）
# =====================================================

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1年
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# =====================================================
# デフォルト主キー
# =====================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
