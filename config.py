import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_key_123456")
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # HTTPS kullanılıyorsa True
    SESSION_COOKIE_SAMESITE = "Lax"
