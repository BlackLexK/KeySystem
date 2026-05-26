# models.py
from database import get_connection
from utils import hash_password, now_iso

# --- reference / bootstrap helpers ---
def insert_default_reference_data():
    conn = get_connection()
    cur = conn.cursor()
    # ensure action_types exist (1 issue, 2 return)
    cur.execute("SELECT COUNT(*) FROM action_types")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO action_types (action_type) VALUES (?)", [(1,), (2,)])
    conn.commit()
    conn.close()



# --- USERS ---
def add_user(role_id, last_name, first_name, middle_name, login, password_plain):
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, role_id, last_name, first_name, middle_name, login, password FROM users WHERE login = ?", (login,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, role_id, last_name, first_name, middle_name, login FROM users WHERE user_id = ?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return r

def list_users():
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


def delete_user(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok


def update_user_password(user_id: int, new_password_plain: str) -> bool:
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










# --- ROLES / ACCESS ---
def get_role(role_id):
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





# --- ROOMS ---
def add_room(room_number, description="", access_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO rooms (room_number, description, access_id) VALUES (?, ?, ?)", (room_number, description, access_id))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def list_rooms():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT room_id, room_number, description, access_id FROM rooms ORDER BY room_id")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_room(room_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT room_id, room_number, description, access_id FROM rooms WHERE room_id = ?", (room_id,))
    r = cur.fetchone()
    conn.close()
    return r

def delete_room(room_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 1. Удаляем все ключи, связанные с помещением
        cur.execute("DELETE FROM keys WHERE room_id = ?", (room_id,))

        # 2. Удаляем само помещение
        cur.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
        conn.commit()

        ok = cur.rowcount > 0
    except Exception as e:
        print("Ошибка delete_room:", e)
        ok = False

    conn.close()
    return ok



def list_users_full():
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









# --- KEYS ---
def add_key(key_number, room_id, activity="available"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO keys (key_number, room_id, activity) VALUES (?, ?, ?)", (key_number, room_id, activity))
    conn.commit()
    kid = cur.lastrowid
    conn.close()
    return kid

def list_keys():
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key_id, key_number, room_id, activity FROM keys WHERE key_number = ?", (key_number,))
    r = cur.fetchone()
    conn.close()
    return r

def get_key(key_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key_id, key_number, room_id, activity FROM keys WHERE key_id = ?", (key_id,))
    r = cur.fetchone()
    conn.close()
    return r

def update_key_activity(key_id, activity):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE keys SET activity = ? WHERE key_id = ?", (activity, key_id))
    conn.commit()
    conn.close()

def update_key_status(key_id: int, new_status: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE keys SET activity = ? WHERE key_id = ?", (new_status, key_id))
        conn.commit()
        return True
    except:
        return False

def delete_key(key_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM keys WHERE key_id = ?", (key_id,))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    return ok



# --- OPERATIONS / LOGS ---
def add_operation(key_id, user_id, issued_by, tips_id, return_deadline=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO operations (key_id, user_id, issued_by, datetime, return_deadline, tips_id) VALUES (?, ?, ?, ?, ?, ?)",
                (key_id, user_id, issued_by, now_iso(), return_deadline, tips_id))
    conn.commit()
    opid = cur.lastrowid
    conn.close()
    return opid

def get_last_operation_for_key(key_id):
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





# --- VIOLATIONS ---
def add_violation(operation_id, key_id, user_id, overdue_seconds, note=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO violations (operation_id, key_id, user_id, overdue_seconds, note, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
                (operation_id, key_id, user_id, overdue_seconds, note, now_iso()))
    conn.commit()
    vid = cur.lastrowid
    conn.close()
    return vid


def list_violations(limit=200):
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






