import hashlib
import datetime

def hash_password(password: str) -> str:
    """SHA-256 хеш пароля (простая, но приемлемая для учебного проекта)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def now_iso() -> str:
    """Текущее время в ISO формате (строка)."""
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
