# main.py
import tkinter as tk
from database import create_db
import models
from auth import LoginWindow
from gui import KeyControlApp

def start_app():
    # создаём БД и справочники, если нужно
    create_db()
    models.insert_default_reference_data()

    # создаём невидимый корневой TK (используется для Toplevel окна входа)
    root = tk.Tk()
    root.withdraw()

    def on_success(user_id):
        # после успешного логина запускаем главное окно приложения
        app = KeyControlApp(user_id)
        app.mainloop()

    # открываем окно входа; оно вызовет on_success при успешном логине
    LoginWindow(root, on_success)
    root.mainloop()

if __name__ == "__main__":
    start_app()

# admin
# Kvartsev123
# Oliga