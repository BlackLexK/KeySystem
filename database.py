# database.py
import sqlite3
import os

DB_DIR = "KeySystem"
DB_PATH = os.path.join(DB_DIR, "D1.db")

def ensure_db_dir():
    if not os.path.isdir(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)

def get_connection():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_db():
    ensure_db_dir()
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS access_levels (
        access_id INTEGER PRIMARY KEY AUTOINCREMENT,
        level INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS roles (
        role_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT NOT NULL,
        access_id INTEGER,
        FOREIGN KEY (access_id) REFERENCES access_levels(access_id)
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER,
        last_name TEXT NOT NULL,
        first_name TEXT NOT NULL,
        middle_name TEXT,
        login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        FOREIGN KEY (role_id) REFERENCES roles(role_id)
    );

    CREATE TABLE IF NOT EXISTS action_types (
        tips_id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT NOT NULL,
        description TEXT,
        access_id INTEGER,
        FOREIGN KEY (access_id) REFERENCES access_levels(access_id)
    );

    CREATE TABLE IF NOT EXISTS keys (
        key_id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_number TEXT NOT NULL,
        room_id INTEGER,
        activity TEXT NOT NULL,
        FOREIGN KEY (room_id) REFERENCES rooms(room_id)
    );

    CREATE TABLE IF NOT EXISTS operations (
        operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id INTEGER,
        user_id INTEGER,         -- кто получил/вернул
        issued_by INTEGER,       -- кто выдал/подтвердил
        datetime TEXT NOT NULL,
        return_deadline TEXT,    -- срок возврата (может быть NULL)
        tips_id INTEGER,
        FOREIGN KEY (key_id) REFERENCES keys(key_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (issued_by) REFERENCES users(user_id),
        FOREIGN KEY (tips_id) REFERENCES action_types(tips_id)
    );

    CREATE TABLE IF NOT EXISTS violations (
        violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id INTEGER,    -- операция выдачи, по которой зафиксировано нарушение
        key_id INTEGER,
        user_id INTEGER,
        overdue_seconds INTEGER, -- на сколько секунд просрочил
        note TEXT,
        recorded_at TEXT,
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id),
        FOREIGN KEY (key_id) REFERENCES keys(key_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    # ДОБАВЛЕНИЕ АДМИНА ПРИ ПЕРВОМ ЗАПУСКЕ
    # 1 — создаем уровень доступа (если нет)
    cur.execute("SELECT COUNT(*) FROM access_levels")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO access_levels (level) VALUES (?)", [(1,), (2,), (3,), (4,), (5,)])

    cur.execute("SELECT COUNT(*) FROM roles")
    if cur.fetchone()[0] == 0:
        # role_name, access_id (map: employee->1, guard->4, admin->5 using access levels)
        # We'll map roles to access levels so that admin has highest (10), guard 4, employee 1-3
        # Using simple mapping:
        # employee role uses access level 3 by default here (can be changed)
        cur.executemany("INSERT INTO roles (role_name, access_id) VALUES (?, ?)",
                        [("Сотрудник", 1), ("Сотрудник_lvl2", 2), ("Сотрудник_lvl3", 3), ("Охранник", 4), ("Администратор", 5)])

    cur.execute("SELECT COUNT(*) FROM action_types")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO action_types (action_type) VALUES (?)", [(1,), (2,)])  # 1=issue,2=return

    # Create default admin user if not exists
    cur.execute("SELECT role_id FROM roles WHERE role_name = 'Администратор' LIMIT 1")
    # row = cur.fetchone()
    # admin_role_id = row[-1] if row else None

    cur.execute("SELECT user_id FROM users WHERE login = 'admin' LIMIT 1")
    if cur.fetchone() is None:
        # password stored in plain here for creation; models.add_user will hash normally
        # Insert admin with a temporary placeholder password 'admin123' hashed later by models if you prefer;
        # But we will insert plain and models.check will compare hashed value => to be consistent, we'll insert hashed password below in models initialization.
        # For safety, insert admin with password 'admin123' hashed using simple sha256 here:
        pwd = "admin123"
        cur.execute("SELECT role_id FROM roles WHERE role_name = 'Администратор'")
        admin_role_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO users (role_id, last_name, first_name, middle_name, login, password)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_role_id, "Админ", "Главный", "", "admin", pwd))
        print("Создан пользователь admin (пароль: admin123)")



    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db()
    print("DB created at:", DB_PATH)


