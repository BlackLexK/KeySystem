# services.py
from models import (
    get_user_by_login, get_user, get_room,
    get_key, get_last_operation_for_key,
    add_operation, update_key_activity, add_violation,
    get_access_level_by_role
)
from utils import hash_password
from datetime import datetime, timedelta

ACTION_ISSUE = 1
ACTION_RETURN = 2

def check_user_credentials(login, password_plain):
    row = get_user_by_login(login)
    if not row:
        return None

    # row содержит:
    # (user_id, role_id, last_name, first_name, middle_name, login, password)
    user_id = row[0]
    stored_password = row[6]  # может быть хэш, а может быть простой текст

    # 1) Хэшируем введённый пароль
    hashed_input = hash_password(password_plain)

    # 2) Сравниваем:
    #    - либо хэш совпал
    #    - либо пароль в БД хранится в открытом виде (старый вариант)
    if hashed_input == stored_password or password_plain == stored_password:
        return user_id

    return None

def get_user_access_level(user_id):
    u = get_user(user_id)
    if not u:
        return None
    role_id = u[1]
    level = get_access_level_by_role(role_id)
    return level

def can_issue_key(key_id, issued_by, recipient_user_id):
    key = get_key(key_id)
    if not key:
        return False, "Ключ не найден"

    room_id = key[2]
    room = get_room(room_id)
    if not room:
        return False, "Помещение не найдено"

    room_access = room[3]  # уровень доступа помещения

    # Уровень получателя ключа
    recipient_level = get_user_access_level(recipient_user_id)
    if recipient_level is None:
        return False, "Получатель не найден"

    # Уровень выдающего (для проверки админских прав)
    issuer_level = get_user_access_level(issued_by)
    if issuer_level is None:
        return False, "Выдающий не найден"

    # 1) Админ может выдать всегда
    if issuer_level < 4:
       return False, "Выдавать ключи может только охрана или администратор"    

    # 2) Проверка уровня доступа получателя (главная логика)
    if room_access is not None and recipient_level < room_access:
        return False, (
            f"У пользователя недостаточно уровня доступа.\n"
            f"Требуется уровень: {room_access}, у сотрудника: {recipient_level}"
        )

    # 3) Проверяем, что ключ не выдан
    last = get_last_operation_for_key(key_id)
    if last and last[6] == ACTION_ISSUE:
        return False, "Ключ уже выдан"

    return True, None


def issue_key(key_id, recipient_user_id, issued_by, due_hours=None, due_datetime_iso=None):
    ok, reason = can_issue_key(key_id, issued_by, recipient_user_id)
    if not ok:
        return False, reason
    # compute deadcodeline
    return_deadline = None
    if due_datetime_iso:
        try:
            # accept both "YYYY-MM-DD HH:MM:SS" and ISO
            datetime.fromisoformat(due_datetime_iso)
            return_deadline = due_datetime_iso
        except:
            return False, "Неверный формат даты срока возврата"
    elif due_hours:
        try:
            hours = float(due_hours)
            return_deadline = (datetime.now() + timedelta(hours=hours)).isoformat(sep=" ", timespec="seconds")
        except:
            return False, "Неверный формат часов срока"
    # update key status and add operation
    update_key_activity(key_id, "issued")
    opid = add_operation(key_id, recipient_user_id, issued_by, ACTION_ISSUE, return_deadline)
    return True, f"Ключ выдан (operation_id={opid}), срок: {return_deadline}"



def return_key(key_id, returning_user_id, processed_by):
    last = get_last_operation_for_key(key_id)
    if not last:
        return False, "По ключу нет операций"

    # last: operation_id, key_id, user_id, issued_by, datetime, return_deadline, tips_id
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

    # обновляем ключ
    update_key_activity(key_id, "available")

    # добавляем операцию возврата
    op_return_id = add_operation(
        key_id,
        returning_user_id,
        processed_by,
        ACTION_RETURN,
        None
    )

    # фиксируем нарушение БЕЗ заметки
    if overdue_seconds > 0:
        add_violation(
            op_issue_id,
            key_id,
            returning_user_id,
            overdue_seconds,
            ""   # заметка только вручную
        )

    return True, (
        f"Ключ принят. "
        f"Просрочка (сек): {overdue_seconds}"
    )




from models import update_user_password

def reset_user_password(admin_user_id: int, target_user_id: int, new_password: str):
    admin_level = get_user_access_level(admin_user_id)

    if admin_level is None or admin_level < 5:
        return False, "Недостаточно прав (требуется администратор)"

    if not new_password or len(new_password) < 4:
        return False, "Пароль слишком короткий"

    ok = update_user_password(target_user_id, new_password)
    if not ok:
        return False, "Не удалось обновить пароль"

    return True, "Пароль успешно сброшен"







