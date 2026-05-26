# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import models
import services
from utils import now_iso
import csv
from openpyxl import Workbook
from datetime import datetime


class KeyControlApp(tk.Tk):
    """
    Главное окно приложения. Открывается только после успешной авторизации.
    current_user_id -- ID вошедшего пользователя (int)
    """
    def __init__(self, current_user_id):
        super().__init__()
        self.current_user = current_user_id
        self.title("ИС учёта выдачи и возврата ключей")
        self.geometry("1000x620")

        # Верхняя строка — информация о пользователе (ФИО и роль)
        u = models.get_user(self.current_user)
        if u:
            fio = f"{u[2]} {u[3]}{(' ' + u[4]) if u[4] else ''}"
            role = models.get_role(u[1])
            role_name = role[1] if role else f"role_id={u[1]}"
            info = f"Пользователь: {fio}  |  Роль: {role_name}"
        else:
            info = f"Пользователь: {self.current_user}"
        self.statusbar = ttk.Label(self, text=info, anchor="w")
        self.statusbar.pack(fill=tk.X)

        # Вкладки
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # создаём вкладки
        self.tab_keys = ttk.Frame(self.nb)
        self.tab_rooms = ttk.Frame(self.nb)
        self.tab_users = ttk.Frame(self.nb)
        self.tab_issue = ttk.Frame(self.nb)
        self.tab_return = ttk.Frame(self.nb)
        self.tab_journal = ttk.Frame(self.nb)
        self.tab_viol = ttk.Frame(self.nb)

        self.nb.add(self.tab_keys, text="Ключи")
        self.nb.add(self.tab_rooms, text="Помещения")
        self.nb.add(self.tab_users, text="Сотрудники")
        self.nb.add(self.tab_issue, text="Выдача")
        self.nb.add(self.tab_return, text="Возврат")
        self.nb.add(self.tab_journal, text="Журнал операций")
        self.nb.add(self.tab_viol, text="Нарушения")

         #  ОГРАНИЧЕНИЕ: скрыть вкладки Выдача и Возврат для уровней 1–3 ===
        level = services.get_user_access_level(self.current_user) or 0
        if level < 4:
            try:
                self.nb.forget(self.tab_issue)
            except:
                pass
            try:
                self.nb.forget(self.tab_return)
            except:
                pass


        # строим содержимое вкладок
        self._build_keys_tab()
        self._build_rooms_tab()
        self._build_users_tab()
        self._build_issue_tab()
        self._build_return_tab()
        self._build_journal_tab()
        self._build_viol_tab()

        # применяем ограничения по доступу (активируем/деактивируем кнопки)
        self._apply_access_controls()

        # загрузка данных
        self.refresh_all()

        # меню (русское)
        menubar = tk.Menu(self)
        acc_menu = tk.Menu(menubar, tearoff=0)
        acc_menu.add_command(label="Выйти", command=self.on_logout)
        acc_menu.add_command(label="Закрыть", command=self.quit)
        menubar.add_cascade(label="Аккаунт", menu=acc_menu)
        menubar.add_command(label="Экспорт операций (Excel)", command=self.export_operations_excel)
        menubar.add_command(label="Экспорт нарушений (Excel)", command=self.export_violations_excel)
        self.config(menu=menubar)

    def _apply_access_controls(self):
        level = services.get_user_access_level(self.current_user) or 0

        ADMIN = 5
        GUARD = 4

        # ====== СОТРУДНИКИ ======
        if level < ADMIN:
            if hasattr(self, "btn_add_user"):
                self.btn_add_user.config(state=tk.DISABLED)
            if hasattr(self, "btn_delete_user"):
                self.btn_delete_user.config(state=tk.DISABLED)
        else:
            if hasattr(self, "btn_add_user"):
                self.btn_add_user.config(state=tk.NORMAL)
            if hasattr(self, "btn_delete_user"):
                self.btn_delete_user.config(state=tk.NORMAL)

        # ====== ПОМЕЩЕНИЯ ======
        if level < ADMIN:
            if hasattr(self, "btn_add_room"):
                self.btn_add_room.config(state=tk.DISABLED)
            if hasattr(self, "btn_delete_room"):
                self.btn_delete_room.config(state=tk.DISABLED)
        else:
            if hasattr(self, "btn_add_room"):
                self.btn_add_room.config(state=tk.NORMAL)
            if hasattr(self, "btn_delete_room"):
                self.btn_delete_room.config(state=tk.NORMAL)

        # ====== КЛЮЧИ ======
        # Добавить / удалить — только админ
        if level < ADMIN:
            if hasattr(self, "btn_add_key"):
                self.btn_add_key.config(state=tk.DISABLED)
            if hasattr(self, "btn_delete_key"):
                self.btn_delete_key.config(state=tk.DISABLED)
        else:
            if hasattr(self, "btn_add_key"):
                self.btn_add_key.config(state=tk.NORMAL)
            if hasattr(self, "btn_delete_key"):
                self.btn_delete_key.config(state=tk.NORMAL)

        # Статус ключа — охрана и админ
        if level < GUARD:
            if hasattr(self, "btn_mark_lost"):
                self.btn_mark_lost.config(state=tk.DISABLED)
            if hasattr(self, "btn_mark_found"):
                self.btn_mark_found.config(state=tk.DISABLED)
        else:
            if hasattr(self, "btn_mark_lost"):
                self.btn_mark_lost.config(state=tk.NORMAL)
            if hasattr(self, "btn_mark_found"):
                self.btn_mark_found.config(state=tk.NORMAL)






    # ------------------ Вкладка "Ключи" ------------------
    def _build_keys_tab(self):
        frame = self.tab_keys

        # --- Верхняя панель ---
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=4)

        ttk.Button(
            toolbar,
            text="Обновить",
            command=self.refresh_keys
        ).pack(side=tk.LEFT, padx=4)

        # СОХРАНЯЕМ кнопки
        self.btn_add_key = ttk.Button(
            toolbar,
            text="Добавить ключ",
            command=self.add_key_dialog
        )
        self.btn_add_key.pack(side=tk.LEFT, padx=4)

        self.btn_delete_key = ttk.Button(
            toolbar,
            text="Удалить ключ",
            command=self.delete_key
        )
        self.btn_delete_key.pack(side=tk.LEFT, padx=4)

        # --- Мини-вкладка "Статус ключа" ---
        self.loss_frame = ttk.Labelframe(frame, text="Статус ключа")
        self.loss_frame.pack(fill=tk.X, pady=6, padx=6)

        self.btn_mark_lost = ttk.Button(
            self.loss_frame,
            text="Отметить как утерянный",
            command=self.mark_key_lost
        )
        self.btn_mark_lost.pack(side=tk.LEFT, padx=5)

        self.btn_mark_found = ttk.Button(
            self.loss_frame,
            text="Вернуть в оборот",
            command=self.mark_key_found
        )
        self.btn_mark_found.pack(side=tk.LEFT, padx=5)

        # --- Таблица ---
        cols = ("ID", "Номер ключа", "Помещение", "Статус")
        self.tree_keys = ttk.Treeview(frame, columns=cols, show="headings")

        for c in cols:
            self.tree_keys.heading(c, text=c)
            self.tree_keys.column(c, width=180)

        self.tree_keys.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)



    def _get_selected_key_id(self):
        """Возвращает ID выбранного ключа из таблицы ключей."""
        sel = self.tree_keys.selection()
        if not sel:
            return None
        item = self.tree_keys.item(sel[0])
        return item["values"][0]  # первая колонка = ID


    def delete_key(self):
        key_id = self._get_selected_key_id()
        if key_id is None:
            messagebox.showwarning("Ошибка", "Выберите ключ.")
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранный ключ?"):
            return

        ok = models.delete_key(key_id)
        if not ok:
            messagebox.showerror("Ошибка", "Не удалось удалить ключ.")
            return

        messagebox.showinfo("Успех", "Ключ удалён.")
        self.refresh_keys()


    

    def mark_key_lost(self):
        """Отметить ключ как утерянный"""
        sel = self.tree_keys.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите ключ из списка", parent=self)
            return
        item = self.tree_keys.item(sel[0])["values"]
        key_id = item[0]

        ok = models.update_key_status(key_id, "lost")
        if ok:
            messagebox.showinfo("Готово", "Ключ отмечен как утерянный", parent=self)
        else:
            messagebox.showerror("Ошибка", "Не удалось изменить статус", parent=self)

        self.refresh_keys()


    def mark_key_found(self):
        """Вернуть ключ в оборот (найден)"""
        sel = self.tree_keys.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите ключ из списка", parent=self)
            return
        item = self.tree_keys.item(sel[0])["values"]
        key_id = item[0]

        ok = models.update_key_status(key_id, "available")
        if ok:
            messagebox.showinfo("Готово", "Ключ восстановлен и снова доступен", parent=self)
        else:
            messagebox.showerror("Ошибка", "Не удалось изменить статус", parent=self)

        self.refresh_keys()


    def refresh_keys(self):
        for it in self.tree_keys.get_children():
            self.tree_keys.delete(it)
        for row in models.list_keys():
            # row: (key_id, key_number, room_number, activity)
            self.tree_keys.insert("", tk.END, values=row)

    def add_key_dialog(self):
        level = services.get_user_access_level(self.current_user) or 0
        if level < 5:
            messagebox.showerror("Доступ закрыт", "Только администратор может добавлять ключи", parent=self)
            return

        # выбор помещения через список (не ввод id вручную)
        rooms = models.list_rooms()
        if not rooms:
            messagebox.showwarning("Внимание", "Сначала добавьте помещение", parent=self)
            return
        # диалог ввода номера ключа и выбора помещения
        kn = simpledialog.askstring("Добавление ключа", "Введите номер ключа (например A-101):", parent=self)
        if not kn:
            return
        # показать пользователю список помещений и позволить выбрать по id/номеру
        choices = "\n".join([f"{r[0]}: {r[1]}" for r in rooms])
        rid = simpledialog.askstring("Выбор помещения", f"Список помещений:\n{choices}\n\nВведите ID помещения из списка:", parent=self)
        if not rid:
            return
        try:
            rid_i = int(rid)
        except:
            messagebox.showerror("Ошибка", "Неверный ID помещения", parent=self)
            return
        kid = models.add_key(kn, rid_i, "available")
        messagebox.showinfo("ОК", f"Ключ добавлен (ID={kid})", parent=self)
        self.refresh_keys()





    # ------------------ Вкладка "Помещения" ------------------
    def _build_rooms_tab(self):
        frame = self.tab_rooms

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=4)

        # === КНОПКИ (сохраняем ссылки) ===
        self.btn_add_room = ttk.Button(
            toolbar,
            text="Добавить помещение",
            command=self.add_room_dialog
        )
        self.btn_add_room.pack(side=tk.LEFT, padx=4)

        self.btn_delete_room = ttk.Button(
            toolbar,
            text="Удалить помещение",
            command=self.delete_room
        )
        self.btn_delete_room.pack(side=tk.LEFT, padx=4)

        ttk.Button(
            toolbar,
            text="Обновить",
            command=self.refresh_rooms
        ).pack(side=tk.LEFT, padx=4)

        # === БЛОКИРОВКА ПО УРОВНЮ ДОСТУПА ===
        level = services.get_user_access_level(self.current_user)

        if level is None or level < 5:
            self.btn_add_room.config(state=tk.DISABLED)
            self.btn_delete_room.config(state=tk.DISABLED)

        # === ТАБЛИЦА ===
        cols = ("ID", "Номер", "Описание", "AccessID")
        self.tree_rooms = ttk.Treeview(frame, columns=cols, show="headings")

        for c in cols:
            self.tree_rooms.heading(c, text=c)
            self.tree_rooms.column(c, width=200)

        self.tree_rooms.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)


    def delete_room(self):
        selected = self.tree_rooms.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите помещение", parent=self)
            return

        item = self.tree_rooms.item(selected[0])
        room_id = item["values"][0]

        # проверка прав
        level = services.get_user_access_level(self.current_user) or 0
        if level < 5:
            messagebox.showerror("Доступ закрыт", "Удалять помещения может только администратор", parent=self)
            return

        # спросить подтверждение
        if not messagebox.askyesno("Подтверждение", f"Удалить помещение ID={room_id}?"):
            return

        # попытка удаления
        if models.delete_room(room_id):
            messagebox.showinfo("Готово", "Помещение удалено", parent=self)
            self.refresh_rooms()
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить помещение — возможно, к нему привязаны ключи", parent=self)


    def refresh_rooms(self):
        for it in self.tree_rooms.get_children():
            self.tree_rooms.delete(it)
        for row in models.list_rooms():
            # row: (room_id, room_number, description, access_id)
            self.tree_rooms.insert("", tk.END, values=row)

    def add_room_dialog(self):
        # только админ может добавлять помещения (проверка в apply_access_controls)
        level = services.get_user_access_level(self.current_user) or 0
        if level < 5:
            messagebox.showerror("Доступ закрыт", "Только администратор может добавлять помещения", parent=self)
            return
        rn = simpledialog.askstring("Добавление помещения", "Введите номер/название помещения:", parent=self)
        if not rn:
            return
        desc = simpledialog.askstring("Описание", "Краткое описание (опционально):", parent=self)
        access = simpledialog.askstring("Уровень доступа", "Введите требуемый уровень доступа (число) или оставьте пустым:", parent=self)
        access_id = int(access) if access else None
        rid = models.add_room(rn, desc or "", access_id)
        messagebox.showinfo("ОК", f"Помещение добавлено (ID={rid})", parent=self)
        self.refresh_rooms()





    # ------------------ Вкладка "Сотрудники" ------------------
    def _build_users_tab(self):
        frame = self.tab_users

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=4)

        # self.btn_add_user = ttk.Button(toolbar, text="Добавить сотрудника", command=self.add_user_dialog)
        # self.btn_add_user.pack(side=tk.LEFT, padx=4)

        # # кнопка удаления
        # ttk.Button(toolbar, text="Удалить сотрудника", command=self.delete_user).pack(side=tk.LEFT, padx=4)

        # ttk.Button(toolbar, text="Обновить", command=self.refresh_users).pack(side=tk.LEFT, padx=4)

        # level = services.get_user_access_level(self.current_user)

        self.btn_add_user = ttk.Button(
            toolbar,
            text="Добавить сотрудника",
            command=self.add_user_dialog
        )
        self.btn_add_user.pack(side=tk.LEFT, padx=4)

        self.btn_delete_user = ttk.Button(
            toolbar,
            text="Удалить сотрудника",
            command=self.delete_user
        )
        self.btn_delete_user.pack(side=tk.LEFT, padx=4)

        ttk.Button(toolbar, text="Обновить", command=self.refresh_users).pack(side=tk.LEFT, padx=4)

        level = services.get_user_access_level(self.current_user)

        # ЕДИНАЯ блокировка
        if level is None or level < 5:
            self.btn_add_user.config(state=tk.DISABLED)
            self.btn_delete_user.config(state=tk.DISABLED)

        

                # ===== ФИЛЬТР ПО ФИО =====
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(filter_frame, text="ФИО:").pack(side=tk.LEFT)

        self.user_fio_filter = ttk.Entry(filter_frame, width=30)
        self.user_fio_filter.pack(side=tk.LEFT, padx=4)

        # фильтрация при вводе
        self.user_fio_filter.bind(
            "<KeyRelease>",
            lambda e: self.refresh_users()
        )
        # ========================




        
        if level >= 5:  # администратор
            cols = ("ID", "ФИО", "ID роли", "Уровень доступа", "Логин", "Пароль")
        else:
            cols = ("ID", "ФИО", "ID роли", "Уровень доступа")
                
        self.tree_users = ttk.Treeview(
            frame,
            columns=cols,
            show="headings"
        )

        for c in cols:
            self.tree_users.heading(c, text=c)
            self.tree_users.column(c, width=200, anchor="w")

        # обработчик двойного клика
        self.tree_users.bind("<Double-1>", self.on_user_table_double_click)


        # вертикальная прокрутка (если ещё нет)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree_users.yview)
        self.tree_users.configure(yscrollcommand=vsb.set)

        # горизонтальная прокрутка (ТО, ЧТО НУЖНО)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree_users.xview)
        self.tree_users.configure(xscrollcommand=hsb.set)

        # размещение
        self.tree_users.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))
        hsb.pack(fill=tk.X, padx=6, pady=(0, 6))
        vsb.pack(side=tk.RIGHT, fill=tk.Y)



    def on_user_table_double_click(self, event):
        # Только администратор
        if services.get_user_access_level(self.current_user) < 5:
            return

        region = self.tree_users.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree_users.identify_column(event.x)
        # колонка "Пароль" = 6
        if column != "#6":
            return

        row_id = self.tree_users.identify_row(event.y)
        if not row_id:
            return

        user_id = int(self.tree_users.item(row_id, "values")[0])

        new_pwd = simpledialog.askstring(
            "Сброс пароля",
            "Введите новый пароль:",
            parent=self,
            show="*"
        )
        if not new_pwd:
            return

        ok, msg = services.reset_user_password(
            self.current_user,
            user_id,
            new_pwd
        )

        if ok:
            messagebox.showinfo("Успех", msg, parent=self)
        else:
            messagebox.showerror("Ошибка", msg, parent=self)



    def delete_user(self):
        level = services.get_user_access_level(self.current_user) or 0
        if level < 5:
            messagebox.showerror("Доступ закрыт", "Удалять сотрудников может только администратор", parent=self)
            return

        selected = self.tree_users.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите сотрудника", parent=self)
            return

        item = self.tree_users.item(selected[0])
        user_id = item["values"][0]

        if messagebox.askyesno("Подтверждение", f"Удалить сотрудника ID={user_id}?", parent=self):
            if models.delete_user(user_id):
                messagebox.showinfo("Готово", "Сотрудник удалён", parent=self)
                self.refresh_users()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить сотрудника", parent=self)


    def add_user_dialog(self):
        level = services.get_user_access_level(self.current_user) or 0
        if level < 5:
            messagebox.showerror("Доступ закрыт", "Только администратор может добавлять сотрудников", parent=self)
            return
        role = simpledialog.askinteger("Роль", "Введите role_id (существующая роль):", parent=self)
        if role is None:
            return
        ln = simpledialog.askstring("Фамилия", "Фамилия:", parent=self)
        fn = simpledialog.askstring("Имя", "Имя:", parent=self)
        mn = simpledialog.askstring("Отчество", "Отчество (опционально):", parent=self)
        login = simpledialog.askstring("Логин", "Логин (для входа):", parent=self)
        pwd = simpledialog.askstring("Пароль", "Пароль:", parent=self)
        if not (ln and fn and login and pwd):
            messagebox.showwarning("Ошибка", "Не все обязательные поля введены", parent=self)
            return
        uid = models.add_user(role, ln, fn, mn or "", login, pwd)
        messagebox.showinfo("ОК", f"Сотрудник добавлен (ID={uid})", parent=self)
        self.refresh_users()









    # ------------------ Вкладка "Выдача" ------------------
    def _build_issue_tab(self):
        frame = self.tab_issue
        lbl = ttk.Label(frame, text="Выдача ключа", font=("Arial", 12)); lbl.pack(anchor="w", padx=8, pady=6)
        form = ttk.Frame(frame); form.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(form, text="Ключ (ID или номер):").grid(row=0, column=0, sticky="w", pady=4)
        self.issue_key_entry = ttk.Entry(form, width=40); self.issue_key_entry.grid(row=0, column=1, pady=4)
        ttk.Label(form, text="ID получателя:").grid(row=1, column=0, sticky="w", pady=4)
        self.issue_user_entry = ttk.Entry(form, width=40); self.issue_user_entry.grid(row=1, column=1, pady=4)
        ttk.Label(form, text="Срок (часы или 'ГГГГ-MM-ДД ЧЧ:MM:CC'):", wraplength=400).grid(row=2, column=0, sticky="w", pady=4)
        self.issue_deadline_entry = ttk.Entry(form, width=40); self.issue_deadline_entry.grid(row=2, column=1, pady=4)
        ttk.Button(form, text="Выдать", command=self.on_issue_clicked).grid(row=3, column=0, columnspan=2, pady=8)

    def on_issue_clicked(self):
        if not self.current_user:
            messagebox.showwarning("Авторизация", "Пожалуйста, войдите в систему", parent=self)
            return
        key_ident = self.issue_key_entry.get().strip()
        if not key_ident:
            messagebox.showwarning("Ошибка", "Введите ID или номер ключа", parent=self)
            return
        # resolve key id
        if key_ident.isdigit():
            key_id = int(key_ident)
        else:
            row = models.find_key_by_number(key_ident)
            if not row:
                messagebox.showerror("Ошибка", "Ключ с таким номером не найден", parent=self)
                return
            key_id = row[0]
        try:
            recipient = int(self.issue_user_entry.get().strip())
        except:
            messagebox.showerror("Ошибка", "Неверный ID получателя", parent=self)
            return
        due = self.issue_deadline_entry.get().strip()
        if due == "":
            ok, msg = services.issue_key(key_id, recipient, self.current_user)
        else:
            try:
                hours = float(due)
                ok, msg = services.issue_key(key_id, recipient, self.current_user, due_hours=hours)
            except:
                ok, msg = services.issue_key(key_id, recipient, self.current_user, due_datetime_iso=due)
        messagebox.showinfo("Результат", msg, parent=self)
        self.refresh_all()










    # ------------------ Вкладка "Возврат" ------------------
    def _build_return_tab(self):
        frame = self.tab_return
        lbl = ttk.Label(frame, text="Прием (возврат) ключа", font=("Arial", 12)); lbl.pack(anchor="w", padx=8, pady=6)
        form = ttk.Frame(frame); form.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(form, text="Ключ (ID или номер):").grid(row=0, column=0, sticky="w", pady=4)
        self.return_key_entry = ttk.Entry(form, width=40); self.return_key_entry.grid(row=0, column=1, pady=4)
        ttk.Label(form, text="ID того, кто возвращает:").grid(row=1, column=0, sticky="w", pady=4)
        self.return_user_entry = ttk.Entry(form, width=40); self.return_user_entry.grid(row=1, column=1, pady=4)
        ttk.Button(form, text="Принять ключ", command=self.on_return_clicked).grid(row=2, column=0, columnspan=2, pady=8)

    def on_return_clicked(self):
        if not self.current_user:
            messagebox.showwarning("Авторизация", "Пожалуйста, войдите в систему", parent=self)
            return
        key_ident = self.return_key_entry.get().strip()
        if not key_ident:
            messagebox.showwarning("Ошибка", "Введите ID или номер ключа", parent=self)
            return
        if key_ident.isdigit():
            key_id = int(key_ident)
        else:
            row = models.find_key_by_number(key_ident)
            if not row:
                messagebox.showerror("Ошибка", "Ключ с таким номером не найден", parent=self)
                return
            key_id = row[0]
        try:
            returning_user = int(self.return_user_entry.get().strip())
        except:
            messagebox.showerror("Ошибка", "Неверный ID пользователя", parent=self)
            return
        ok, msg = services.return_key(key_id, returning_user, self.current_user)
        messagebox.showinfo("Результат", msg, parent=self)
        self.refresh_all()






    # ------------------ Вкладка "Журнал операций" ------------------
    def _build_journal_tab(self):
        frame = self.tab_journal
        toolbar = ttk.Frame(frame); toolbar.pack(fill=tk.X, pady=4)

                # ===== ФИЛЬТР =====
        filter_frame = ttk.LabelFrame(frame, text="Фильтр")
        filter_frame.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(filter_frame, text="С даты (YYYY-MM-DD):").grid(row=0, column=0, padx=4)
        self.j_from = ttk.Entry(filter_frame, width=12)
        self.j_from.grid(row=0, column=1)

        ttk.Label(filter_frame, text="По дату:").grid(row=0, column=2, padx=4)
        self.j_to = ttk.Entry(filter_frame, width=12)
        self.j_to.grid(row=0, column=3)

        ttk.Label(filter_frame, text="Пользователь (ФИО:").grid(row=0, column=4, padx=4)
        self.j_user = ttk.Entry(filter_frame, width=10)
        self.j_user.grid(row=0, column=5)

        ttk.Button(filter_frame, text="Применить", command=self.apply_journal_filter)\
            .grid(row=0, column=6, padx=6)
        
        ttk.Button(
            filter_frame,
            text="Сброс фильтра",
            command=self.reset_journal_filter
        ).grid(row=0, column=7, padx=6)


        ttk.Button(toolbar, text="Обновить журнал", command=self.refresh_journal).pack(side=tk.LEFT, padx=4)

        cols = ("ID", "Дата/время", "Срок возврата", "Тип", "Ключ", "Кому", "Выдал")
        self.tree_journal = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_journal.heading(c, text=c)
            self.tree_journal.column(c, width=140)
        self.tree_journal.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)


    def reset_journal_filter(self):
        self.j_from.delete(0, tk.END)
        self.j_to.delete(0, tk.END)
        self.j_user.delete(0, tk.END)
        self.refresh_journal()

    def refresh_journal(self):
        self.tree_journal.delete(*self.tree_journal.get_children())
        for r in models.list_operations(500):
            self.tree_journal.insert("", tk.END, values=r)

   

    def apply_journal_filter(self):
        from datetime import datetime

        date_from = self.j_from.get().strip()
        date_to = self.j_to.get().strip()
        user_text = self.j_user.get().strip().lower()

        date_from = datetime.fromisoformat(date_from) if date_from else None
        date_to = datetime.fromisoformat(date_to) if date_to else None

        self.tree_journal.delete(*self.tree_journal.get_children())

        for r in models.list_operations(500):
            # r = (id, dt, deadline, type, key, to_user_fio, by_user_fio)

            try:
                op_dt = datetime.fromisoformat(r[1])
            except ValueError:
                continue

            # ---- фильтр по дате
            if date_from and op_dt < date_from:
                continue
            if date_to and op_dt > date_to:
                continue

            # ---- фильтр по пользователю (ФИО)
            if user_text:
                to_user = (r[5] or "").lower()
                by_user = (r[6] or "").lower()

                if user_text not in to_user and user_text not in by_user:
                    continue

            self.tree_journal.insert("", tk.END, values=r)










    # ------------------ Вкладка "Нарушения" ------------------
    def _build_viol_tab(self):
        frame = self.tab_viol
        toolbar = ttk.Frame(frame); toolbar.pack(fill=tk.X, pady=4)
        
        filter_frame = ttk.LabelFrame(frame, text="Фильтр")
        filter_frame.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(filter_frame, text="С даты:").grid(row=0, column=0)
        self.v_from = ttk.Entry(filter_frame, width=12)
        self.v_from.grid(row=0, column=1)

        ttk.Label(filter_frame, text="По дату:").grid(row=0, column=2)
        self.v_to = ttk.Entry(filter_frame, width=12)
        self.v_to.grid(row=0, column=3)

        ttk.Label(filter_frame, text="Пользователь (ФИО:").grid(row=0, column=4)
        self.v_user = ttk.Entry(filter_frame, width=10)
        self.v_user.grid(row=0, column=5)

        ttk.Button(
            filter_frame,
            text="Применить",
            command=self.apply_violation_filter
        ).grid(row=0, column=6, padx=6)

        
        ttk.Button(
            filter_frame,
            text="Сброс фильтра",
            command=self.reset_violation_filter
        ).grid(row=0, column=7, padx=6)


                
        ttk.Button(toolbar, text="Обновить нарушения", command=self.refresh_violations).pack(side=tk.LEFT, padx=4)

        cols = ("ID","Время выдачи","Время возврата","Просрочка (с)","Заметка","Ключ","Пользователь")
        self.tree_viol = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            self.tree_viol.heading(c, text=c)
            self.tree_viol.column(c, width=140)
        self.tree_viol.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    
    def reset_violation_filter(self):
        self.v_from.delete(0, tk.END)
        self.v_to.delete(0, tk.END)
        self.v_user.delete(0, tk.END)
        self.refresh_violations()

    
    
    
    def refresh_violations(self):
        self.tree_viol.delete(*self.tree_viol.get_children())

        user_text = self.v_user.get().strip().lower()

        for r in models.list_violations():
            # r = (id, issue_time, return_time, overdue, note, key, user_fio)

            if user_text:
                if not r[6] or user_text not in r[6].lower():
                    continue

            self.tree_viol.insert("", tk.END, values=r)





            

    def apply_violation_filter(self):
        from datetime import datetime

        date_from = self.v_from.get().strip()
        date_to = self.v_to.get().strip()
        user_text = self.v_user.get().strip().lower()

        date_from = datetime.fromisoformat(date_from) if date_from else None
        date_to = datetime.fromisoformat(date_to) if date_to else None

        self.tree_viol.delete(*self.tree_viol.get_children())

        for r in models.list_violations():
            # r = (id, issue_time, return_time, overdue, note, key, user_fio)

            try:
                issue_dt = datetime.fromisoformat(r[1])
            except ValueError:
                continue

            # фильтр по дате
            if date_from and issue_dt < date_from:
                continue
            if date_to and issue_dt > date_to:
                continue

            # фильтр по ФИО
            if user_text:
                user_fio = (r[6] or "").lower()
                if user_text not in user_fio:
                    continue

            self.tree_viol.insert("", tk.END, values=r)




        




    

    # ------------------ Экспорт CSV ------------------
   
   
    # def export_operations_csv(self):
    #     ops = models.list_operations(10000)
    #     if not ops:
    #         messagebox.showinfo("Экспорт", "Операций нет для экспорта", parent=self)
    #         return
    #     path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Сохранить операции")
    #     if not path:
    #         return
    #     with open(path, "w", newline="", encoding="utf-8") as f:
    #         w = csv.writer(f)
    #         w.writerow(["ID операции","Дата/время","Срок возврата","Операция","Номер ключа","Пользователь","Выдавший"])
    #         for r in ops:
    #             w.writerow(r)
    #     messagebox.showinfo("Экспорт", f"Операции экспортированы в:\n{path}", parent=self)

    def export_violations_excel(self):
        rows = models.list_violations(10000)
        if not rows:
            messagebox.showinfo("Экспорт", "Нарушений нет", parent=self)
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel файл", "*.xlsx")],
            title="Сохранить нарушения"
        )
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Нарушения"

        # Заголовки — НА РУССКОМ
        ws.append([
            "ID нарушения",
            "Время выдачи",
            "Время возврата",
            "Просрочка (сек)",
            "Заметка",
            "Номер ключа",
            "Пользователь"
        ])

        for r in rows:
            ws.append(r)

        wb.save(path)
        messagebox.showinfo("Экспорт", f"Нарушения сохранены:\n{path}", parent=self)

    def export_operations_excel(self):
        rows = models.list_operations(10000)
        if not rows:
            messagebox.showinfo("Экспорт", "Операций нет", parent=self)
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Сохранить журнал операций"
        )
        if not path:
            return

        wb = Workbook()
        ws = wb.active
        ws.title = "Журнал операций"

        # Заголовки (РУССКИЕ)
        ws.append([
            "ID операции",
            "Дата и время",
            "Срок возврата",
            "Тип операции",
            "Ключ",
            "Кому выдан",
            "Кто выдал / принял"
        ])

        for r in rows:
            ws.append(r)

        wb.save(path)
        messagebox.showinfo("Экспорт", f"Журнал операций сохранён:\n{path}", parent=self)

        
    
    # def export_violations_csv(self):
    #     rows = models.list_violations(10000)
    #     if not rows:
    #         messagebox.showinfo("Экспорт", "Нарушений нет", parent=self)
    #         return
    #     path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="Сохранить нарушения")
    #     if not path:
    #         return
    #     with open(path, "w", newline="", encoding="utf-8") as f:
    #         w = csv.writer(f)
    #         w.writerow(["ID нарушения","recorded_at","Просрочено на","Заметки","Номер ключа","Пользователь"])
    #         for r in rows:
    #             w.writerow(r)
    #     messagebox.showinfo("Экспорт", f"Нарушения экспортированы в:\n{path}", parent=self)





    # ------------------ Общие обновления ------------------
    def refresh_all(self):
        self.refresh_keys(); self.refresh_rooms(); self.refresh_users(); self.refresh_journal(); self.refresh_violations()


    def refresh_users(self):
        for it in self.tree_users.get_children():
            self.tree_users.delete(it)

        level = services.get_user_access_level(self.current_user)

            # ===== ПОЛУЧАЕМ ФИЛЬТР ФИО =====
        fio_filter = ""
        if hasattr(self, "user_fio_filter"):
            fio_filter = self.user_fio_filter.get().lower().strip()

        for row in models.list_users_full():
            fio = f"{row[1]} {row[2]} {row[3]}".strip()

                # ===== ПРИМЕНЯЕМ ФИЛЬТР =====
            if fio_filter and fio_filter not in fio.lower():
                continue
            # ===========================

            if level >= 5:
                values = (
                    row[0],   # ID
                    fio,
                    row[5],   # role_id
                    row[6],   # access level
                    row[4],   # login
                    "Сброс пароля"
                )
            else:
                values = (
                    row[0],
                    fio,
                    row[5],
                    row[6]
                )

            self.tree_users.insert("", tk.END, values=values)

    def reset_user_filter(self):
        if hasattr(self, "user_fio_filter"):
            self.user_fio_filter.set("")
        self.refresh_users()



    def refresh_rooms(self):
        for it in self.tree_rooms.get_children():
            self.tree_rooms.delete(it)
        for r in models.list_rooms():
            self.tree_rooms.insert("", tk.END, values=r)

    def refresh_journal_tab(self):
        for it in self.tree_journal.get_children():
            self.tree_journal.delete(it)
        for r in models.list_operations(500):
            self.tree_journal.insert("", tk.END, values=r)

    def refresh_violations_tab(self):
        for it in self.tree_viol.get_children():
            self.tree_viol.delete(it)
        for r in models.list_violations():
            self.tree_viol.insert("", tk.END, values=r)





    # ------------------ Выход / разлогин ------------------
    def on_logout(self):
        # при выходе — закрываем окно и возвращаемся в окно входа
        self.destroy()
        # Запускаем окно входа снова
        from auth import LoginWindow
        root = tk.Tk()
        root.withdraw()
        def on_success(uid):
            app = KeyControlApp(uid)
            app.mainloop()
        LoginWindow(root, on_success)
        root.mainloop()
    



















    # def refresh_users(self):
    #     for it in self.tree_users.get_children():
    #         self.tree_users.delete(it)

    #     for row in models.list_users_full():
    #         fio = f"{row[1]} {row[2]} {row[3]}".strip()

    #         self.tree_users.insert(
    #             "",
    #             tk.END,
    #             values=(
    #                 row[0],        # ID
    #                 fio,           # ФИО
    #                 row[4],        # логин
    #                 row[5],        # role_id
    #                 row[6],        # access level
    #                 "Сбросить пароль"  # ← псевдокнопка
    #             )
    #         )