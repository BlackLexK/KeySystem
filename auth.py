# auth.py
import tkinter as tk
from tkinter import ttk, messagebox
import services

class LoginWindow(tk.Toplevel):
    """
    Окно входа. Вызывает on_success(user_id) при успешной авторизации.
    Это окно создаётся из main.py; main.py передаёт коллбэк для запуска GUI.
    """
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.title("Вход в систему")
        self.geometry("360x180")
        self.resizable(False, False)
        self.grab_set()  # фокус ввода на этом окне

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Логин:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=6)
        self.login_entry = ttk.Entry(frm, width=30)
        self.login_entry.grid(row=0, column=1, pady=6)

        ttk.Label(frm, text="Пароль:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=6)
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
        login = self.login_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not login or not pwd:
            messagebox.showwarning("Внимание", "Введите логин и пароль", parent=self)
            return
        user_id = services.check_user_credentials(login, pwd)
        if user_id:
            # успешная авторизация
            messagebox.showinfo("Успех", "Вход выполнен", parent=self)
            self.grab_release()
            self.destroy()
            self.on_success(user_id)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль", parent=self)

    def on_cancel(self):
        # закрываем приложение полностью (если логин — основной вход)
        self.grab_release()
        self.destroy()

