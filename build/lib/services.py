"""
Модуль бизнес-логики.

Содержит основные сервисные функции:
- Аутентификация пользователей
- Проверка прав доступа
- Выдача и возврат ключей
- Сброс паролей
- Расчёт просрочек и фиксация нарушений
"""

from models import (
    get_user_by_login, get_user, get_room,
    get_key, get_last_operation_for_key,
    add_operation, update_key_activity, add_violation,
    get_access_level_by_role, update_user_password
)
from utils import hash_password
from datetime import datetime, timedelta

#: Идентификатор типа операции "выдача".
ACTION_ISSUE = 1

#: Идентификатор типа операции "возврат".
ACTION_RETURN = 2


def check_user_credentials(login, password_plain):
    """
    Проверяет логин и пароль пользователя.

    Поддерживает проверку как хешированных, так и открытых паролей
    (для обратной совместимости).

    :param login: Логин пользователя.
    :type login: str
    :param password_plain: Пароль в открытом виде.
    :type password_plain: str
    :return: Идентификатор пользователя при успехе, иначе None.
    :rtype: int | None
    """
    row = get_user_by_login(login)
    if not row:
        return None

    user_id = row[0]
    stored_password = row[6]
    hashed_input = hash_password(password_plain)

    if hashed_input == stored_password or password_plain == stored_password:
        return user_id

    return None


def get_user_access_level(user_id):
    """
    Возвращает числовой уровень доступа пользователя.

    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :return: Уровень доступа (1–5) или None, если пользователь не найден.
    :rtype: int | None
    """
    u = get_user(user_id)
    if not u:
        return None
    role_id = u[1]
    level = get_access_level_by_role(role_id)
    return level


def can_issue_key(key_id, issued_by, recipient_user_id):
    """
    Проверяет возможность выдачи ключа.

    Выполняет следующие проверки:
    1. Ключ существует.
    2. Помещение существует.
    3. Выдающий имеет уровень доступа >= 4 (охранник/админ).
    4. Получатель имеет достаточный уровень доступа для помещения.
    5. Ключ не выдан в данный момент.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param issued_by: Идентификатор выдающего сотрудника.
    :type issued_by: int
    :param recipient_user_id: Идентификатор получателя ключа.
    :type recipient_user_id: int
    :return: Кортеж (can_issue: bool, reason: str | None).
    :rtype: tuple[bool, str | None]
    """
    key = get_key(key_id)
    if not key:
        return False, "Ключ не найден"

    room_id = key[2]
    room = get_room(room_id)
    if not room:
        return False, "Помещение не найдено"

    room_access = room[3]
    recipient_level = get_user_access_level(recipient_user_id)
    if recipient_level is None:
        return False, "Получатель не найден"

    issuer_level = get_user_access_level(issued_by)
    if issuer_level is None:
        return False, "Выдающий не найден"

    if issuer_level < 4:
        return False, "Выдавать ключи может только охрана или администратор"

    if room_access is not None and recipient_level < room_access:
        return False, (
            f"У пользователя недостаточно уровня доступа.\n"
            f"Требуется уровень: {room_access}, у сотрудника: {recipient_level}"
        )

    last = get_last_operation_for_key(key_id)
    if last and last[6] == ACTION_ISSUE:
        return False, "Ключ уже выдан"

    return True, None


def issue_key(key_id, recipient_user_id, issued_by, due_hours=None, due_datetime_iso=None):
    """
    Оформляет выдачу ключа.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param recipient_user_id: Идентификатор получателя.
    :type recipient_user_id: int
    :param issued_by: Идентификатор выдающего.
    :type issued_by: int
    :param due_hours: Срок возврата в часах (альтернатива due_datetime_iso).
    :type due_hours: float | None
    :param due_datetime_iso: Срок возврата в формате ISO (YYYY-MM-DD HH:MM:SS).
    :type due_datetime_iso: str | None
    :return: Кортеж (success: bool, message: str).
    :rtype: tuple[bool, str]
    """
    ok, reason = can_issue_key(key_id, issued_by, recipient_user_id)
    if not ok:
        return False, reason

    return_deadline = None
    if due_datetime_iso:
        try:
            datetime.fromisoformat(due_datetime_iso)
            return_deadline = due_datetime_iso
        except ValueError:
            return False, "Неверный формат даты срока возврата"
    elif due_hours:
        try:
            hours = float(due_hours)
            return_deadline = (datetime.now() + timedelta(hours=hours)).isoformat(
                sep=" ", timespec="seconds"
            )
        except ValueError:
            return False, "Неверный формат часов срока"

    update_key_activity(key_id, "issued")
    opid = add_operation(key_id, recipient_user_id, issued_by, ACTION_ISSUE, return_deadline)
    return True, f"Ключ выдан (operation_id={opid}), срок: {return_deadline}"


def return_key(key_id, returning_user_id, processed_by):
    """
    Оформляет возврат ключа.

    При просрочке возврата автоматически создаёт запись о нарушении.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param returning_user_id: Идентификатор возвращающего пользователя.
    :type returning_user_id: int
    :param processed_by: Идентификатор сотрудника, принимающего ключ.
    :type processed_by: int
    :return: Кортеж (success: bool, message: str).
    :rtype: tuple[bool, str]
    """
    last = get_last_operation_for_key(key_id)
    if not last:
        return False, "По ключу нет операций"

    if last[6] != ACTION_ISSUE:
        return False, "Последняя операция не выдача — возврат невозможен"

    op_issue_id = last[0]
    deadline = last[5]
    overdue_seconds = 0

    if deadline:
        try:
            dl = datetime.fromisoformat(deadline)
            now = datetime.now()
            if now > dl:
                delta = now - dl
                overdue_seconds = int(delta.total_seconds())
        except Exception:
            pass

    update_key_activity(key_id, "available")
    op_return_id = add_operation(
        key_id,
        returning_user_id,
        processed_by,
        ACTION_RETURN,
        None
    )

    if overdue_seconds > 0:
        add_violation(
            op_issue_id,
            key_id,
            returning_user_id,
            overdue_seconds,
            ""
        )

    return True, (
        f"Ключ принят. "
        f"Просрочка (сек): {overdue_seconds}"
    )


def reset_user_password(admin_user_id, target_user_id, new_password):
    """
    Сбрасывает пароль пользователя (только для администраторов).

    :param admin_user_id: Идентификатор администратора, выполняющего операцию.
    :type admin_user_id: int
    :param target_user_id: Идентификатор пользователя, чей пароль сбрасывается.
    :type target_user_id: int
    :param new_password: Новый пароль (минимум 4 символа).
    :type new_password: str
    :return: Кортеж (success: bool, message: str).
    :rtype: tuple[bool, str]
    """
    admin_level = get_user_access_level(admin_user_id)

    if admin_level is None or admin_level < 5:
        return False, "Недостаточно прав (требуется администратор)"

    if not new_password or len(new_password) < 4:
        return False, "Пароль слишком короткий"

    ok = update_user_password(target_user_id, new_password)
    if not ok:
        return False, "Не удалось обновить пароль"

    return True, "Пароль успешно сброшен"
