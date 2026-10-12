"""
Student Database Management System
------------------------------------
Features:
  - Login (username/password, stored hashed in SQLite)
  - Add Student
  - Search Student (by ID or Name)
  - Update Student Records
  - Delete Student Records
  - Generate Reports (summary + exportable text report)

Tech stack: Python 3, Tkinter (GUI), SQLite3 (database)

Run:
    python student_database_system.py

Default login (created automatically on first run):
    username: admin
    password: admin123
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import datetime
import os

DB_FILE = "student_database.db"


# ----------------------------------------------------------------------
# DATABASE LAYER
# ----------------------------------------------------------------------
class Database:
    def __init__(self, db_file=DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._seed_default_user()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                course TEXT,
                email TEXT,
                phone TEXT,
                grade TEXT,
                date_added TEXT
            )
        """)
        self.conn.commit()

    def _seed_default_user(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            self.create_user("admin", "admin123")

    @staticmethod
    def _hash(password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def create_user(self, username, password):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, self._hash(password)),
        )
        self.conn.commit()

    def verify_login(self, username, password):
        cur = self.conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row is None:
            return False
        return row[0] == self._hash(password)

    def change_credentials(self, current_username, current_password, new_username, new_password):
        """
        Verifies current_username/current_password, then updates to new_username/new_password.
        Returns (success: bool, message: str).
        """
        if not self.verify_login(current_username, current_password):
            return False, "Current username or password is incorrect."

        cur = self.conn.cursor()

        # If changing username, make sure the new one isn't already taken by someone else
        if new_username != current_username:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cur.fetchone()[0] > 0:
                return False, "That username is already taken."

        cur.execute(
            "UPDATE users SET username = ?, password_hash = ? WHERE username = ?",
            (new_username, self._hash(new_password), current_username),
        )
        self.conn.commit()
        return True, "Credentials updated successfully."

    # ---------------- CRUD ----------------
    def add_student(self, roll_no, name, age, gender, course, email, phone, grade):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO students (roll_no, name, age, gender, course, email, phone, grade, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (roll_no, name, age, gender, course, email, phone, grade,
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.conn.commit()

    def update_student(self, student_id, roll_no, name, age, gender, course, email, phone, grade):
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE students
            SET roll_no=?, name=?, age=?, gender=?, course=?, email=?, phone=?, grade=?
            WHERE id=?
        """, (roll_no, name, age, gender, course, email, phone, grade, student_id))
        self.conn.commit()

    def delete_student(self, student_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM students WHERE id=?", (student_id,))
        self.conn.commit()

    def get_all_students(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY id")
        return cur.fetchall()

    def search_students(self, term):
        cur = self.conn.cursor()
        like = f"%{term}%"
        cur.execute("""
            SELECT * FROM students
            WHERE roll_no LIKE ? OR name LIKE ? OR course LIKE ?
            ORDER BY id
        """, (like, like, like))
        return cur.fetchall()

    def get_student_by_id(self, student_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
        return cur.fetchone()

    def student_count(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        return cur.fetchone()[0]

    def course_breakdown(self):
        cur = self.conn.cursor()
        cur.execute("SELECT course, COUNT(*) FROM students GROUP BY course ORDER BY course")
        return cur.fetchall()

    def grade_breakdown(self):
        cur = self.conn.cursor()
        cur.execute("SELECT grade, COUNT(*) FROM students GROUP BY grade ORDER BY grade")
        return cur.fetchall()


# ----------------------------------------------------------------------
# LOGIN WINDOW
# ----------------------------------------------------------------------
class LoginWindow(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("Student DB - Login")
        self.geometry("360x260")
        self.resizable(False, False)
        NAVY = "#0f172a"
        self.configure(bg=NAVY)

        tk.Label(self, text="Student Database System", font=("Segoe UI", 14, "bold"),
                 bg=NAVY, fg="white").pack(pady=(25, 5))
        tk.Label(self, text="Please log in to continue", font=("Segoe UI", 9),
                 bg=NAVY, fg="#cbd5e1").pack(pady=(0, 15))

        form = tk.Frame(self, bg=NAVY)
        form.pack()

        tk.Label(form, text="Username:", bg=NAVY, fg="white").grid(row=0, column=0, sticky="e", pady=6, padx=5)
        self.username_var = tk.StringVar()
        tk.Entry(form, textvariable=self.username_var, width=22).grid(row=0, column=1, pady=6)

        tk.Label(form, text="Password:", bg=NAVY, fg="white").grid(row=1, column=0, sticky="e", pady=6, padx=5)
        self.password_var = tk.StringVar()
        tk.Entry(form, textvariable=self.password_var, show="*", width=22).grid(row=1, column=1, pady=6)

        tk.Button(self, text="Login", width=20, bg="#2563eb", fg="white",
                  command=self.attempt_login).pack(pady=15)

        tk.Label(self, text="Default: admin / admin123", font=("Segoe UI", 8),
                 bg=NAVY, fg="#94a3b8").pack()

        self.bind("<Return>", lambda e: self.attempt_login())

    def attempt_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing info", "Enter both username and password.")
            return
        if self.db.verify_login(username, password):
            self.destroy()
            app = MainApp(self.db, username)
            app.mainloop()
        else:
            messagebox.showerror("Login failed", "Invalid username or password.")


# ----------------------------------------------------------------------
# MAIN APPLICATION WINDOW
# ----------------------------------------------------------------------
class MainApp(tk.Tk):
    COLUMNS = ("id", "roll_no", "name", "age", "gender", "course", "email", "phone", "grade", "date_added")
    HEADERS = ("ID", "Roll No", "Name", "Age", "Gender", "Course", "Email", "Phone", "Grade", "Added")

    def __init__(self, db, current_username):
        super().__init__()
        self.db = db
        self.current_username = current_username
        self.title("Student Database Management System")
        self.geometry("1000x600")
        self.minsize(900, 550)

        self._build_top_bar()
        self._build_table()
        self._build_bottom_bar()
        self.refresh_table()

    # ---------- UI Sections ----------
    def _build_top_bar(self):
        bar = tk.Frame(self, bg="#1e293b", height=50)
        bar.pack(fill="x")

        tk.Label(bar, text="Student Database Management System", fg="white", bg="#1e293b",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=15, pady=10)

        actions = tk.Frame(self, bg="#f2f4f7")
        actions.pack(fill="x", padx=10, pady=8)

        tk.Button(actions, text="+ Add Student", bg="#16a34a", fg="white",
                  command=self.open_add_window).pack(side="left", padx=4)
        tk.Button(actions, text="Update Selected", bg="#2563eb", fg="white",
                  command=self.open_update_window).pack(side="left", padx=4)
        tk.Button(actions, text="Delete Selected", bg="#dc2626", fg="white",
                  command=self.delete_selected).pack(side="left", padx=4)
        tk.Button(actions, text="Generate Report", bg="#7c3aed", fg="white",
                  command=self.open_report_window).pack(side="left", padx=4)
        tk.Button(actions, text="Refresh", command=self.refresh_table).pack(side="left", padx=4)
        tk.Button(actions, text="Change Credentials", bg="#f59e0b", fg="white",
                  command=self.open_change_credentials_window).pack(side="left", padx=4)

        search_frame = tk.Frame(actions, bg="#f2f4f7")
        search_frame.pack(side="right")
        self.search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.search_var, width=25).pack(side="left", padx=4)
        tk.Button(search_frame, text="Search", command=self.search).pack(side="left")
        tk.Button(search_frame, text="Clear", command=self.refresh_table).pack(side="left", padx=4)
        self.search_var.trace_add("write", lambda *_: self.search())

    def _build_table(self):
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", selectmode="browse")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self.tree.heading(col, text=header)
            width = 60 if col in ("id", "age") else 130
            self.tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _build_bottom_bar(self):
        self.status_var = tk.StringVar()
        status = tk.Label(self, textvariable=self.status_var, anchor="w",
                           bg="#e5e7eb", padx=10, pady=4)
        status.pack(fill="x", side="bottom")

    # ---------- Data operations ----------
    def refresh_table(self):
        self.search_var.set("")
        rows = self.db.get_all_students()
        self._populate(rows)

    def search(self):
        term = self.search_var.get().strip()
        rows = self.db.search_students(term) if term else self.db.get_all_students()
        self._populate(rows)

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert("", "end", values=row)
        self.status_var.set(f"{len(rows)} student(s) shown  |  Total in database: {self.db.student_count()}")

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])["values"][0]

    def delete_selected(self):
        student_id = self.get_selected_id()
        if student_id is None:
            messagebox.showinfo("No selection", "Select a student row to delete.")
            return
        if messagebox.askyesno("Confirm delete", f"Delete student ID {student_id}? This cannot be undone."):
            self.db.delete_student(student_id)
            self.refresh_table()

    def open_add_window(self):
        StudentFormWindow(self, self.db, mode="add")

    def open_update_window(self):
        student_id = self.get_selected_id()
        if student_id is None:
            messagebox.showinfo("No selection", "Select a student row to update.")
            return
        record = self.db.get_student_by_id(student_id)
        StudentFormWindow(self, self.db, mode="update", record=record)

    def open_report_window(self):
        ReportWindow(self, self.db)

    def open_change_credentials_window(self):
        ChangeCredentialsWindow(self, self.db, self.current_username)


# ----------------------------------------------------------------------
# ADD / UPDATE FORM (shared window)
# ----------------------------------------------------------------------
class StudentFormWindow(tk.Toplevel):
    FIELDS = ["roll_no", "name", "age", "gender", "course", "email", "phone", "grade"]
    LABELS = ["Roll No", "Name", "Age", "Gender", "Course", "Email", "Phone", "Grade"]

    def __init__(self, parent, db, mode="add", record=None):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.mode = mode
        self.record = record  # full row tuple when updating

        self.title("Add Student" if mode == "add" else "Update Student")
        self.geometry("360x420")
        self.resizable(False, False)
        self.grab_set()  # modal

        self.vars = {f: tk.StringVar() for f in self.FIELDS}

        form = tk.Frame(self, padx=15, pady=15)
        form.pack(fill="both", expand=True)

        for i, (field, label) in enumerate(zip(self.FIELDS, self.LABELS)):
            tk.Label(form, text=label + ":").grid(row=i, column=0, sticky="e", pady=6, padx=5)
            if field == "gender":
                combo = ttk.Combobox(form, textvariable=self.vars[field],
                                      values=["Male", "Female", "Other"], width=20, state="readonly")
                combo.grid(row=i, column=1, pady=6)
            elif field == "grade":
                combo = ttk.Combobox(form, textvariable=self.vars[field],
                                      values=["A", "B", "C", "D", "F"], width=20, state="readonly")
                combo.grid(row=i, column=1, pady=6)
            else:
                tk.Entry(form, textvariable=self.vars[field], width=23).grid(row=i, column=1, pady=6)

        if mode == "update" and record:
            # record columns: id, roll_no, name, age, gender, course, email, phone, grade, date_added
            values = dict(zip(MainApp.COLUMNS, record))
            for f in self.FIELDS:
                self.vars[f].set(values.get(f, ""))

        btn_text = "Add Student" if mode == "add" else "Save Changes"
        tk.Button(self, text=btn_text, bg="#2563eb", fg="white",
                  command=self.submit).pack(pady=10)

    def submit(self):
        data = {f: self.vars[f].get().strip() for f in self.FIELDS}

        if not data["roll_no"] or not data["name"]:
            messagebox.showwarning("Missing info", "Roll No and Name are required.")
            return

        age_val = None
        if data["age"]:
            try:
                age_val = int(data["age"])
            except ValueError:
                messagebox.showwarning("Invalid age", "Age must be a number.")
                return

        try:
            if self.mode == "add":
                self.db.add_student(data["roll_no"], data["name"], age_val, data["gender"],
                                     data["course"], data["email"], data["phone"], data["grade"])
                messagebox.showinfo("Success", "Student added successfully.")
            else:
                student_id = self.record[0]
                self.db.update_student(student_id, data["roll_no"], data["name"], age_val,
                                        data["gender"], data["course"], data["email"],
                                        data["phone"], data["grade"])
                messagebox.showinfo("Success", "Student updated successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Roll No", "A student with that Roll No already exists.")
            return

        self.parent.refresh_table()
        self.destroy()


# ----------------------------------------------------------------------
# CHANGE CREDENTIALS WINDOW
# ----------------------------------------------------------------------
class ChangeCredentialsWindow(tk.Toplevel):
    def __init__(self, parent, db, current_username):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.current_username = current_username

        self.title("Change Username / Password")
        self.geometry("360x360")
        self.resizable(False, False)
        self.grab_set()  # modal

        form = tk.Frame(self, padx=15, pady=15)
        form.pack(fill="both", expand=True)

        tk.Label(form, text=f"Logged in as: {current_username}",
                 font=("Segoe UI", 9, "italic"), fg="#555").grid(
            row=0, column=0, columnspan=2, pady=(0, 12), sticky="w")

        tk.Label(form, text="Current Password:").grid(row=1, column=0, sticky="e", pady=6, padx=5)
        self.current_password_var = tk.StringVar()
        tk.Entry(form, textvariable=self.current_password_var, show="*", width=23).grid(row=1, column=1, pady=6)

        ttk.Separator(form, orient="horizontal").grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        tk.Label(form, text="New Username:").grid(row=3, column=0, sticky="e", pady=6, padx=5)
        self.new_username_var = tk.StringVar(value=current_username)
        tk.Entry(form, textvariable=self.new_username_var, width=23).grid(row=3, column=1, pady=6)

        tk.Label(form, text="New Password:").grid(row=4, column=0, sticky="e", pady=6, padx=5)
        self.new_password_var = tk.StringVar()
        tk.Entry(form, textvariable=self.new_password_var, show="*", width=23).grid(row=4, column=1, pady=6)

        tk.Label(form, text="Confirm New Password:").grid(row=5, column=0, sticky="e", pady=6, padx=5)
        self.confirm_password_var = tk.StringVar()
        tk.Entry(form, textvariable=self.confirm_password_var, show="*", width=23).grid(row=5, column=1, pady=6)

        tk.Button(self, text="Save Changes", bg="#f59e0b", fg="white",
                  command=self.submit).pack(pady=10)

    def submit(self):
        current_password = self.current_password_var.get().strip()
        new_username = self.new_username_var.get().strip()
        new_password = self.new_password_var.get().strip()
        confirm_password = self.confirm_password_var.get().strip()

        if not current_password:
            messagebox.showwarning("Missing info", "Enter your current password.")
            return
        if not new_username:
            messagebox.showwarning("Missing info", "New username cannot be empty.")
            return
        if not new_password:
            messagebox.showwarning("Missing info", "New password cannot be empty.")
            return
        if new_password != confirm_password:
            messagebox.showwarning("Mismatch", "New password and confirmation do not match.")
            return

        success, message = self.db.change_credentials(
            self.current_username, current_password, new_username, new_password
        )

        if success:
            self.parent.current_username = new_username
            messagebox.showinfo("Success", message)
            self.destroy()
        else:
            messagebox.showerror("Error", message)


# ----------------------------------------------------------------------
# REPORT WINDOW
# ----------------------------------------------------------------------
class ReportWindow(tk.Toplevel):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.title("Student Report")
        self.geometry("480x480")

        self.text = tk.Text(self, wrap="word", font=("Consolas", 10))
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(self, text="Export Report to File", bg="#7c3aed", fg="white",
                  command=self.export_report).pack(pady=(0, 10))

        self.report_content = self.generate_report_text()
        self.text.insert("1.0", self.report_content)
        self.text.config(state="disabled")

    def generate_report_text(self):
        total = self.db.student_count()
        courses = self.db.course_breakdown()
        grades = self.db.grade_breakdown()

        lines = []
        lines.append("=" * 50)
        lines.append("STUDENT DATABASE REPORT")
        lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Total students: {total}")
        lines.append("")
        lines.append("Students per course:")
        if courses:
            for course, count in courses:
                lines.append(f"  - {course or 'N/A'}: {count}")
        else:
            lines.append("  (no data)")
        lines.append("")
        lines.append("Students per grade:")
        if grades:
            for grade, count in grades:
                lines.append(f"  - {grade or 'N/A'}: {count}")
        else:
            lines.append("  (no data)")
        lines.append("")
        lines.append("-" * 50)
        lines.append("Full Student Listing")
        lines.append("-" * 50)
        for row in self.db.get_all_students():
            (sid, roll_no, name, age, gender, course, email, phone, grade, added) = row
            lines.append(f"[{sid}] {roll_no} - {name} | Age: {age} | {gender} | "
                          f"{course} | Grade: {grade} | Added: {added}")

        return "\n".join(lines)

    def export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")],
            initialfile="student_report.txt",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.report_content)
            messagebox.showinfo("Exported", f"Report saved to:\n{path}")


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    database = Database()
    login = LoginWindow(database)
    login.mainloop()
