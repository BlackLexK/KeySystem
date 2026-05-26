"""
Точка входа в приложение «ИС учёта выдачи и возврата ключей».

Создаёт базу данных, заполняет справочники и запускает
окно авторизации. После успешного входа открывается
главное окно приложения.

Запуск::

    python main.py

или после установки пакета::

    keycontrol
"""

import tkinter as tk
from database import create_db
import models
from auth import LoginWindow
from gui import KeyControlApp


def start_app():
    """
    Инициализирует базу данных и запускает приложение.

    Создаёт структуру БД (если не существует), заполняет
    справочные данные и открывает окно входа.

    :return: None
    """
    create_db()
    models.insert_default_reference_data()

    root = tk.Tk()
    root.withdraw()

    def on_success(user_id):
        """
        Callback, вызываемый после успешной авторизации.

        :param user_id: Идентификатор вошедшего пользователя.
        :type user_id: int
        """
        app = KeyControlApp(user_id)
        app.mainloop()

    LoginWindow(root, on_success)
    root.mainloop()


if __name__ == "__main__":
    start_app()
