"""
Модуль утилит для KeyControlApp.

Содержит вспомогательные функции для хеширования паролей
и работы с датами/временем.
"""

import hashlib
import datetime


def hash_password(password: str) -> str:
    """
    Возвращает SHA-256 хеш пароля.

    Используется для безопасного хранения паролей пользователей
    в базе данных. Хеширование одностороннее — восстановление
    исходного пароля невозможно.

    :param password: Пароль в открытом виде.
    :type password: str
    :return: SHA-256 хеш в виде шестнадцатеричной строки.
    :rtype: str
    :raises TypeError: Если password не является строкой.

    Пример использования::

        >>> hash_password("admin123")
        '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_iso() -> str:
    """
    Возвращает текущее дату и время в ISO формате.

    Формат: ``YYYY-MM-DD HH:MM:SS``. Используется для записи
    временных меток в журнал операций и нарушений.

    :return: Текущее время в ISO формате с разделителем-пробелом.
    :rtype: str

    Пример использования::

        >>> now_iso()
        '2024-01-15 09:30:45'
    """
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
