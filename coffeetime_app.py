import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import sqlite3, hashlib, os

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

DB_PATH = "coffeetime.db"

def hash_password(password: str) -> str:
    """Crea un hash seguro para la contraseña."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    """Crea la base de datos y agrega recetas iniciales si no existen."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabla usuarios
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        display_name TEXT
    );
    """)

    # Tabla recetas
    c.execute("""
    CREATE TABLE IF NOT EXISTS recetas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        ingredientes TEXT,
        pasos TEXT,
        imagen TEXT
    );
    """)

    # Insertar recetas ejemplo si aún no existen
    c.execute("SELECT COUNT(*) FROM recetas")
    if c.fetchone()[0] == 0:
        recetas = [
            ("Café Latte", "Café suave con leche espumosa.",
             "Café espresso\nLeche entera\nEspuma de leche",
             "1. Preparar espresso.\n2. Calentar leche.\n3. Agregar espuma y servir.",
             "latte.jpg"),
            ("Capuccino", "Espresso con partes iguales de leche y espuma.",
             "Café espresso\nLeche\nCacao en polvo",
             "1. Preparar espresso.\n2. Agregar leche caliente y espuma.\n3. Espolvorear cacao.",
             "capuccino.jpg"),
            ("Moka", "Café con leche y chocolate.",
             "Café espresso\nLeche\nChocolate en polvo\nAzúcar al gusto",
             "1. Preparar espresso.\n2. Calentar leche con chocolate.\n3. Mezclar y servir caliente.",
             "moka.jpg")
        ]
        c.executemany("INSERT INTO recetas (nombre, descripcion, ingredientes, pasos, imagen) VALUES (?, ?, ?, ?, ?)", recetas)

    conn.commit()
    conn.close()

# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================

class CoffeeTimeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CoffeeTime")
        self.geometry("460x720")
        self.resizable(False, False)
        self.current_user = None

        # --- Estilo general ---
        self.configure(bg="#F8EFEA")
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background="#F8EFEA")
        style.configure("TLabel", background="#F8EFEA", font=("Segoe UI", 11))
        style.configure("Header.TLabel", background="#F8EFEA", font=("Segoe UI Semibold", 20, "bold"), foreground="#4B2E05")
        style.configure("TButton", font=("Segoe UI", 11), padding=6, relief="flat", background="#DCC3A1", foreground="#4B2E05")
        style.map("TButton",
                  background=[("active", "#C7A27C"), ("pressed", "#B58E68")])

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (LoginFrame, RegisterFrame, MainMenuFrame, RecipesFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()
        frame.event_generate("<<ShowFrame>>")

    def login_user(self, username, password):
        if not username or not password:
            messagebox.showwarning("Atención", "Ingrese usuario y contraseña.")
            return False
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, password_hash, display_name FROM usuarios WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if row:
            uid, pw, name = row
            if pw == hash_password(password):
                self.current_user = (uid, username, name)
                messagebox.showinfo("Bienvenido", f"Hola {name or username} ☕")
                self.show_frame(MainMenuFrame)
                return True
        messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
        return False

    def register_user(self, username, password, display_name):
        if not username or not password:
            messagebox.showwarning("Atención", "Ingrese usuario y contraseña.")
            return False
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO usuarios (username, password_hash, display_name) VALUES (?, ?, ?)",
                      (username, hash_password(password), display_name))
            conn.commit()
            messagebox.showinfo("Registro exitoso", "Usuario creado correctamente.")
            self.show_frame(LoginFrame)
            return True
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ese usuario ya existe.")
            return False
        finally:
            conn.close()

# ============================================================
# PANTALLAS
# ============================================================

# --- LOGIN ---
class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller: CoffeeTimeApp):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="CoffeeTime", style="Header.TLabel").pack(pady=(15, 5))

        # --- Imagen decorativa ---
        if os.path.exists("totoro.jpg"):
            img = Image.open("totoro.jpg").resize((280, 180))
            self.bg_photo = ImageTk.PhotoImage(img)
            ttk.Label(self, image=self.bg_photo).pack(pady=10)

        ttk.Label(self, text="Usuario:").pack(anchor="w", padx=40)
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack(fill="x", padx=40, pady=(0, 8))

        ttk.Label(self, text="Contraseña:").pack(anchor="w", padx=40)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack(fill="x", padx=40, pady=(0, 8))

        ttk.Button(self, text="Iniciar sesión", command=self.on_login).pack(fill="x", padx=40, pady=(5, 6))
        ttk.Button(self, text="Registrarse", command=lambda: controller.show_frame(RegisterFrame)).pack(fill="x", padx=40)

    def on_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        self.controller.login_user(u, p)

# --- REGISTRO ---
class RegisterFrame(ttk.Frame):
    def __init__(self, parent, controller: CoffeeTimeApp):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Crear cuenta", style="Header.TLabel").pack(pady=15)

        self.username_entry = ttk.Entry(self)
        self.display_entry = ttk.Entry(self)
        self.password_entry = ttk.Entry(self, show="*")
        self.password2_entry = ttk.Entry(self, show="*")

        campos = [("Usuario:", self.username_entry),
                  ("Nombre para mostrar:", self.display_entry),
                  ("Contraseña:", self.password_entry),
                  ("Confirmar contraseña:", self.password2_entry)]
        for lbl, ent in campos:
            ttk.Label(self, text=lbl).pack(anchor="w", padx=40)
            ent.pack(fill="x", padx=40, pady=(0, 6))

        ttk.Button(self, text="Guardar", command=self.on_register).pack(fill="x", padx=40, pady=(8, 6))
        ttk.Button(self, text="Cancelar", command=lambda: controller.show_frame(LoginFrame)).pack(fill="x", padx=40)

    def on_register(self):
        u = self.username_entry.get().strip()
        d = self.display_entry.get().strip()
        p1 = self.password_entry.get().strip()
        p2 = self.password2_entry.get().strip()
        if p1 != p2:
            messagebox.showwarning("Error", "Las contraseñas no coinciden.")
            return
        self.controller.register_user(u, p1, d)

# --- MENÚ PRINCIPAL ---
class MainMenuFrame(ttk.Frame):
    def __init__(self, parent, controller: CoffeeTimeApp):
        super().__init__(parent)
        self.controller = controller
        self.welcome = ttk.Label(self, text="Bienvenido", style="Header.TLabel")
        self.welcome.pack(pady=20)

        ttk.Button(self, text="Ver recetas", command=lambda: controller.show_frame(RecipesFrame)).pack(fill="x", padx=60, pady=5)
        ttk.Button(self, text="Cerrar sesión", command=self.logout).pack(fill="x", padx=60, pady=15)
        self.bind("<<ShowFrame>>", self.on_show)

    def on_show(self, event=None):
        user = self.controller.current_user
        if user:
            _, u, d = user
            self.welcome.config(text=f"Hola, {d or u} ☕")

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame(LoginFrame)

# --- VER RECETAS ---
class RecipesFrame(ttk.Frame):
    def __init__(self, parent, controller: CoffeeTimeApp):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Recetas de café", style="Header.TLabel").pack(pady=10)
        self.listbox = ttk.Treeview(self, columns=("nombre",), show="headings", height=5)
        self.listbox.heading("nombre", text="Recetas disponibles")
        self.listbox.pack(fill="x", padx=20)
        self.listbox.bind("<<TreeviewSelect>>", self.mostrar_receta)

        self.image_label = ttk.Label(self)
        self.image_label.pack(pady=10)

        self.ingredients_label = ttk.Label(self, text="", wraplength=400, justify="left")
        self.ingredients_label.pack(pady=4)
        self.steps_label = ttk.Label(self, text="", wraplength=400, justify="left")
        self.steps_label.pack(pady=4)

        ttk.Button(self, text="Volver al menú", command=lambda: controller.show_frame(MainMenuFrame)).pack(pady=10)
        self.bind("<<ShowFrame>>", self.cargar_lista)

    def cargar_lista(self, event=None):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, nombre FROM recetas")
        recetas = c.fetchall()
        conn.close()
        for i in self.listbox.get_children():
            self.listbox.delete(i)
        for r in recetas:
            self.listbox.insert("", "end", iid=r[0], values=(r[1],))

    def mostrar_receta(self, event=None):
        sel = self.listbox.selection()
        if not sel: return
        rid = sel[0]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT nombre, ingredientes, pasos, imagen FROM recetas WHERE id=?", (rid,))
        nombre, ing, pas, img = c.fetchone()
        conn.close()

        if os.path.exists(img):
            image = Image.open(img).resize((280, 180))
            self.photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo, text="")
        else:
            self.image_label.config(image="", text="[Imagen no disponible]")

        self.ingredients_label.config(text=f"🧂 Ingredientes:\n{ing}")
        self.steps_label.config(text=f"👣 Pasos:\n{pas}")

# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    init_db()
    app = CoffeeTimeApp()
    app.mainloop()
