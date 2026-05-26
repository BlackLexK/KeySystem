"""
Модуль авторизации.

Содержит класс LoginWindow — модальное окно входа в систему
с проверкой логина и пароля через сервис аутентификации.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import services


class LoginWindow(tk.Toplevel):
    """
    Модальное окно входа в систему.

    Отображает форму с полями для ввода логина и пароля.
    При успешной авторизации вызывает callback ``on_success(user_id)``
    и закрывается.

    :param master: Родительское окно tkinter.
    :type master: tk.Tk | tk.Toplevel
    :param on_success: Callback-функция, вызываемая при успешном входе.
                       Принимает один аргумент — идентификатор пользователя.
    :type on_success: callable

    Пример использования::

        def on_success(user_id):
            app = KeyControlApp(user_id)
            app.mainloop()

        root = tk.Tk()
        LoginWindow(root, on_success)
        root.mainloop()
    """

    def __init__(self, master, on_success):
        """
        Инициализирует окно входа.

        :param master: Родительское окно.
        :param on_success: Callback при успешном входе.
        """
        super().__init__(master)
        self.on_success = on_success
        self.title("Вход в систему")
        self.geometry("360x180")
        self.resizable(False, False)
        self.grab_set()

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Логин:", font=("Arial", 11)).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.login_entry = ttk.Entry(frm, width=30)
        self.login_entry.grid(row=0, column=1, pady=6)

        ttk.Label(frm, text="Пароль:", font=("Arial", 11)).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.pwd_entry = ttk.Entry(frm, show="*", width=30)
        self.pwd_entry.grid(row=1, column=1, pady=6)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        btn_login = ttk.Button(btn_frame, text="Войти", command=self.try_login)
        btn_login.pack(side=tk.LEFT, padx=5)
        btn_cancel = ttk.Button(btn_frame, text="Отмена", command=self.on_cancel)
        btn_cancel.pack(side=tk.LEFT, padx=5)

        self.login_entry.focus_set()

    def try_login(self):
        """
        Пытается выполнить вход с введёнными данными.

        При успехе вызывает ``on_success(user_id)`` и закрывает окно.
        При неудаче показывает сообщение об ошибке.

        :return: None
        """
        login = self.login_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not login or not pwd:
            messagebox.showwarning("Внимание", "Введите логин и пароль", parent=self)
            return
        user_id = services.check_user_credentials(login, pwd)
        if user_id:
            messagebox.showinfo("Успех", "Вход выполнен", parent=self)
            self.grab_release()
            self.destroy()
            self.on_success(user_id)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль", parent=self)

    def on_cancel(self):
        """
        Закрывает окно входа без авторизации.

        :return: None
        """
        self.grab_release()
        self.destroy()
