"""
Модуль моделей данных и CRUD-операций.

Содержит функции для работы с сущностями системы:
пользователи, роли, помещения, ключи, операции, нарушения.
Все функции работают с SQLite через модуль database.
"""

from database import get_connection
from utils import hash_password, now_iso


# --- Справочники / инициализация ---

def insert_default_reference_data():
    """
    Заполняет справочник типов операций, если он пуст.

    Добавляет записи: 1 — выдача, 2 — возврат.

    :return: None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM action_types")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO action_types (action_type) VALUES (?)",
            [(1,), (2,)]
        )
    conn.commit()
    conn.close()


# --- Пользователи ---

def add_user(role_id, last_name, first_name, middle_name, login, password_plain):
    """
    Добавляет нового пользователя в систему.

    :param role_id: Идентификатор роли пользователя.
    :type role_id: int
    :param last_name: Фамилия.
    :type last_name: str
    :param first_name: Имя.
    :type first_name: str
    :param middle_name: Отчество (может быть пустым).
    :type middle_name: str
    :param login: Уникальный логин для входа.
    :type login: str
    :param password_plain: Пароль в открытом виде (будет захеширован).
    :type password_plain: str
    :return: Идентификатор созданного пользователя.
    :rtype: int
    :raises sqlite3.IntegrityError: Если логин уже существует.
    """
    conn = get_connection()
    cur = conn.cursor()
    pwd_hash = hash_password(password_plain)
    cur.execute("""
        INSERT INTO users (role_id, last_name, first_name, middle_name, login, password)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (role_id, last_name, first_name, middle_name, login, pwd_hash))
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid


def get_user_by_login(login):
    """
    Возвращает пользователя по логину.

    :param login: Логин пользователя.
    :type login: str
    :return: Кортеж (user_id, role_id, last_name, first_name, middle_name, login, password)
             или None, если пользователь не найден.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, role_id, last_name, first_name, middle_name, login, password
        FROM users WHERE login = ?
    """, (login,))
    row = cur.fetchone()
    conn.close()
    return row


def get_user(user_id):
    """
    Возвращает пользователя по ID.

    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :return: Кортеж (user_id, role_id, last_name, first_name, middle_name, login)
             или None, если не найден.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, role_id, last_name, first_name, middle_name, login
        FROM users WHERE user_id = ?
    """, (user_id,))
    r = cur.fetchone()
    conn.close()
    return r


def list_users():
    """
    Возвращает список пользователей с ФИО и уровнем доступа.

    :return: Список кортежей (user_id, fio, role_id, access_level, login, password).
    :rtype: list[tuple]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            u.user_id,
            u.last_name || ' ' || u.first_name ||
                CASE WHEN u.middle_name != '' THEN ' ' || u.middle_name ELSE '' END AS fio,
            u.role_id,
            a.level AS access_level,
            u.login,
            u.password
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        LEFT JOIN access_levels a ON r.access_id = a.access_id
        ORDER BY u.user_id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def list_users_full():
    """
    Возвращает полные данные пользователей для отображения в таблице.

    :return: Список кортежей (user_id, last_name, first_name, middle_name, login, role_id, access_level).
    :rtype: list[tuple]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            u.user_id,
            u.last_name,
            u.first_name,
            u.middle_name,
            u.login,
            u.role_id,
            a.level
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.role_id
        LEFT JOIN access_levels a ON r.access_id = a.access_id
        ORDER BY u.user_id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def delete_user(user_id):
    """
    Удаляет пользователя по ID.

    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :return: True, если удаление успешно.
    :rtype: bool
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok


def update_user_password(user_id, new_password_plain):
    """
    Обновляет пароль пользователя.

    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :param new_password_plain: Новый пароль в открытом виде.
    :type new_password_plain: str
    :return: True, если обновление успешно.
    :rtype: bool
    """
    conn = get_connection()
    cur = conn.cursor()
    pwd_hash = hash_password(new_password_plain)
    cur.execute(
        "UPDATE users SET password = ? WHERE user_id = ?",
        (pwd_hash, user_id)
    )
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok


# --- Роли и уровни доступа ---

def get_role(role_id):
    """
    Возвращает роль по ID.

    :param role_id: Идентификатор роли.
    :type role_id: int
    :return: Кортеж (role_id, role_name, level) или None.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.role_id, r.role_name, a.level
        FROM roles r
        LEFT JOIN access_levels a ON r.access_id = a.access_id
        WHERE r.role_id = ?
    """, (role_id,))
    r = cur.fetchone()
    conn.close()
    return r


def get_access_level_by_role(role_id):
    """
    Возвращает числовой уровень доступа для роли.

    :param role_id: Идентификатор роли.
    :type role_id: int
    :return: Уровень доступа (1–5) или None.
    :rtype: int | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.level FROM roles r
        LEFT JOIN access_levels a ON r.access_id = a.access_id
        WHERE r.role_id = ?
    """, (role_id,))
    r = cur.fetchone()
    conn.close()
    return r[0] if r else None


# --- Помещения ---

def add_room(room_number, description="", access_id=None):
    """
    Добавляет новое помещение.

    :param room_number: Номер или название помещения.
    :type room_number: str
    :param description: Описание помещения.
    :type description: str
    :param access_id: Требуемый уровень доступа (опционально).
    :type access_id: int | None
    :return: Идентификатор созданного помещения.
    :rtype: int
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rooms (room_number, description, access_id) VALUES (?, ?, ?)",
        (room_number, description, access_id)
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def list_rooms():
    """
    Возвращает список всех помещений.

    :return: Список кортежей (room_id, room_number, description, access_id).
    :rtype: list[tuple]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT room_id, room_number, description, access_id FROM rooms ORDER BY room_id")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_room(room_id):
    """
    Возвращает помещение по ID.

    :param room_id: Идентификатор помещения.
    :type room_id: int
    :return: Кортеж (room_id, room_number, description, access_id) или None.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT room_id, room_number, description, access_id FROM rooms WHERE room_id = ?", (room_id,))
    r = cur.fetchone()
    conn.close()
    return r


def delete_room(room_id):
    """
    Удаляет помещение и все связанные с ним ключи.

    :param room_id: Идентификатор помещения.
    :type room_id: int
    :return: True, если удаление успешно.
    :rtype: bool
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM keys WHERE room_id = ?", (room_id,))
        cur.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
        conn.commit()
        ok = cur.rowcount > 0
    except Exception as e:
        print("Ошибка delete_room:", e)
        ok = False
    conn.close()
    return ok


# --- Ключи ---

def add_key(key_number, room_id, activity="available"):
    """
    Добавляет новый ключ.

    :param key_number: Номер или обозначение ключа.
    :type key_number: str
    :param room_id: Идентификатор помещения.
    :type room_id: int
    :param activity: Статус ключа (``available``, ``issued``, ``lost``).
    :type activity: str
    :return: Идентификатор созданного ключа.
    :rtype: int
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO keys (key_number, room_id, activity) VALUES (?, ?, ?)",
        (key_number, room_id, activity)
    )
    conn.commit()
    kid = cur.lastrowid
    conn.close()
    return kid


def list_keys():
    """
    Возвращает список всех ключей с информацией о помещениях.

    :return: Список кортежей (key_id, key_number, room_number, activity).
    :rtype: list[tuple]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT k.key_id, k.key_number, r.room_number, k.activity
        FROM keys k LEFT JOIN rooms r ON k.room_id = r.room_id
        ORDER BY k.key_id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def find_key_by_number(key_number):
    """
    Ищет ключ по его номеру.

    :param key_number: Номер ключа.
    :type key_number: str
    :return: Кортеж (key_id, key_number, room_id, activity) или None.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key_id, key_number, room_id, activity FROM keys WHERE key_number = ?", (key_number,))
    r = cur.fetchone()
    conn.close()
    return r


def get_key(key_id):
    """
    Возвращает ключ по ID.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :return: Кортеж (key_id, key_number, room_id, activity) или None.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key_id, key_number, room_id, activity FROM keys WHERE key_id = ?", (key_id,))
    r = cur.fetchone()
    conn.close()
    return r


def update_key_activity(key_id, activity):
    """
    Обновляет статус ключа.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param activity: Новый статус (``available``, ``issued``, ``lost``).
    :type activity: str
    :return: None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE keys SET activity = ? WHERE key_id = ?", (activity, key_id))
    conn.commit()
    conn.close()


def update_key_status(key_id, new_status):
    """
    Обновляет статус ключа (обёртка с обработкой ошибок).

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param new_status: Новый статус.
    :type new_status: str
    :return: True, если обновление успешно.
    :rtype: bool
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE keys SET activity = ? WHERE key_id = ?", (new_status, key_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def delete_key(key_id):
    """
    Удаляет ключ по ID.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :return: True, если удаление успешно.
    :rtype: bool
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM keys WHERE key_id = ?", (key_id,))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok


# --- Операции ---

def add_operation(key_id, user_id, issued_by, tips_id, return_deadline=None):
    """
    Добавляет операцию (выдачи или возврата) в журнал.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param user_id: Идентификатор пользователя (получателя/возвращающего).
    :type user_id: int
    :param issued_by: Идентификатор сотрудника, оформившего операцию.
    :type issued_by: int
    :param tips_id: Тип операции (1 — выдача, 2 — возврат).
    :type tips_id: int
    :param return_deadline: Срок возврата (ISO формат), опционально.
    :type return_deadline: str | None
    :return: Идентификатор созданной операции.
    :rtype: int
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO operations (key_id, user_id, issued_by, datetime, return_deadline, tips_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (key_id, user_id, issued_by, now_iso(), return_deadline, tips_id))
    conn.commit()
    opid = cur.lastrowid
    conn.close()
    return opid


def get_last_operation_for_key(key_id):
    """
    Возвращает последнюю операцию для указанного ключа.

    :param key_id: Идентификатор ключа.
    :type key_id: int
    :return: Кортеж операции или None.
    :rtype: tuple | None
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT operation_id, key_id, user_id, issued_by, datetime, return_deadline, tips_id
        FROM operations
        WHERE key_id = ?
        ORDER BY operation_id DESC
        LIMIT 1
    """, (key_id,))
    r = cur.fetchone()
    conn.close()
    return r


def list_operations(limit=200):
    """
    Возвращает список операций с детализацией.

    :param limit: Максимальное количество записей.
    :type limit: int
    :return: Список кортежей (operation_id, datetime, return_deadline,
             operation_type, key_number, user_name, issuer_name).
    :rtype: list[tuple]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            o.operation_id,
            o.datetime,
            o.return_deadline,
            CASE o.tips_id
                WHEN 1 THEN 'Выдача'
                WHEN 2 THEN 'Возврат'
                ELSE 'Неизвестно'
            END AS operation_type,
            k.key_number,
            u.last_name || ' ' || u.first_name AS user_name,
            issuer.last_name || ' ' || issuer.first_name AS issuer_name
        FROM operations o
        LEFT JOIN keys k ON o.key_id = k.key_id
        LEFT JOIN users u ON o.user_id = u.user_id
        LEFT JOIN users issuer ON o.issued_by = issuer.user_id
        ORDER BY o.operation_id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# --- Нарушения ---

def add_violation(operation_id, key_id, user_id, overdue_seconds, note=""):
    """
    Добавляет запись о нарушении (просрочка возврата ключа).

    :param operation_id: Идентификатор операции выдачи.
    :type operation_id: int
    :param key_id: Идентификатор ключа.
    :type key_id: int
    :param user_id: Идентификатор пользователя, нарушившего срок.
    :type user_id: int
    :param overdue_seconds: Время просрочки в секундах.
    :type overdue_seconds: int
    :param note: Примечание к нарушению.
    :type note: str
    :return: Идентификатор созданной записи о нарушении.
    :rtype: int
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO violations (operation_id, key_id, user_id, overdue_seconds, note, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (operation_id, key_id, user_id, overdue_seconds, note, now_iso()))
    conn.commit()
    vid = cur.lastrowid
    conn.close()
    return vid


def list_violations(limit=200):
    """
    Возвращает список нарушений с детализацией.

    :param limit: Максимальное количество записей.
    :type limit: int
    :return: Список кортежей (violation_id, issued_at, returned_at,
             overdue_seconds, note, key_number, user_name).
    :rtype: list[tuple]
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            v.violation_id,
            o.datetime AS issued_at,
            o.return_deadline AS returned_at,
            v.overdue_seconds,
            v.note,
            k.key_number,
            u.last_name || ' ' || u.first_name AS user_name
        FROM violations v
        LEFT JOIN operations o ON v.operation_id = o.operation_id
        LEFT JOIN keys k ON v.key_id = k.key_id
        LEFT JOIN users u ON v.user_id = u.user_id
        ORDER BY v.violation_id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
