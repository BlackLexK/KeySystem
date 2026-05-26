"""
Модуль инициализации базы данных.

Создаёт SQLite базу данных со всеми необходимыми таблицами
и справочными данными (уровни доступа, роли, типы операций,
начальный администратор).
"""

import sqlite3
import os

#: Директория для хранения базы данных.
DB_DIR = os.environ.get("DB_DIR", "KeySystem")

#: Полный путь к файлу базы данных SQLite.
DB_PATH = os.environ.get("DB_PATH", os.path.join(DB_DIR, "D1.db"))


def ensure_db_dir():
    """
    Создаёт директорию для базы данных, если она не существует.

    :return: None
    """
    if not os.path.isdir(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)


def get_connection():
    """
    Возвращает подключение к SQLite базе данных.

    Автоматически создаёт директорию и включает поддержку
    внешних ключей (``PRAGMA foreign_keys = ON``).

    :return: Объект подключения sqlite3.Connection.
    :rtype: sqlite3.Connection
    """
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_db():
    """
    Создаёт структуру базы данных и заполняет справочники.

    Создает таблицы access_levels, roles, users, action_types,
    rooms, keys, operations, violations. Заполняет справочники
    уровней доступа, ролей и типов операций. Создает начального
    администратора (login: admin, password: admin123).

    :return: None
    :raises sqlite3.Error: При ошибках выполнения SQL.
    """
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
        user_id INTEGER,
        issued_by INTEGER,
        datetime TEXT NOT NULL,
        return_deadline TEXT,
        tips_id INTEGER,
        FOREIGN KEY (key_id) REFERENCES keys(key_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (issued_by) REFERENCES users(user_id),
        FOREIGN KEY (tips_id) REFERENCES action_types(tips_id)
    );

    CREATE TABLE IF NOT EXISTS violations (
        violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id INTEGER,
        key_id INTEGER,
        user_id INTEGER,
        overdue_seconds INTEGER,
        note TEXT,
        recorded_at TEXT,
        FOREIGN KEY (operation_id) REFERENCES operations(operation_id),
        FOREIGN KEY (key_id) REFERENCES keys(key_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    # Инициализация справочников
    cur.execute("SELECT COUNT(*) FROM access_levels")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO access_levels (level) VALUES (?)",
            [(1,), (2,), (3,), (4,), (5,)]
        )

    cur.execute("SELECT COUNT(*) FROM roles")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO roles (role_name, access_id) VALUES (?, ?)",
            [
                ("Сотрудник", 1),
                ("Сотрудник_lvl2", 2),
                ("Сотрудник_lvl3", 3),
                ("Охранник", 4),
                ("Администратор", 5),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM action_types")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO action_types (action_type) VALUES (?)",
            [(1,), (2,)]
        )

    # Создание начального администратора
    cur.execute("SELECT user_id FROM users WHERE login = 'admin' LIMIT 1")
    if cur.fetchone() is None:
        cur.execute("SELECT role_id FROM roles WHERE role_name = 'Администратор'")
        admin_role_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO users (role_id, last_name, first_name, middle_name, login, password)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_role_id, "Админ", "Главный", "", "admin", "admin123"))
        print("Создан пользователь admin (пароль: admin123)")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
    print("DB created at:", DB_PATH)
