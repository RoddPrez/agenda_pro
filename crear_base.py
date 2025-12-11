import sqlite3

DB = "agenda_pro.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

# -------------------------
# Crear tablas
# -------------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre TEXT,
    carrera TEXT,
    semestre INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    date TEXT,
    start TEXT,
    end TEXT,
    fixed INTEGER DEFAULT 0,
    notes TEXT,
    priority TEXT DEFAULT 'Media',
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

conn.commit()
print("📌 Base agenda_pro.db creada correctamente.")
