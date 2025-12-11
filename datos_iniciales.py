import sqlite3
from datetime import datetime, timedelta
import random

DB = "agenda_pro.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("📌 Insertando datos para DICIEMBRE 2025...")

# ---------- Crear usuario base ----------
cur.execute("""
INSERT OR IGNORE INTO users (username, password, nombre, carrera, semestre)
VALUES ('javier_gamboa', 'limaperu2025', 'Javier Gamboa', 'Ingeniería de Software', 10)
""")

cur.execute("SELECT id FROM users WHERE username='javier_gamboa'")
user_id = cur.fetchone()[0]


# ===========================================================
#                GENERADOR DE EVENTOS COMPLETO
# ===========================================================

eventos = []

inicio = datetime(2025, 12, 1)
dias_mes = 31

# Catálogos de actividades
charlas = [
    "Charla de IA aplicada",
    "Conferencia de Ciberseguridad",
    "Evento DevOps Lima",
    "Meetup de Software Architecture",
    "Charla Big Data y Analytics",
    "Seminario Blockchain",
]

cursos = [
    "Curso virtual de Kubernetes",
    "Curso de Machine Learning",
    "Curso de Arquitectura Cloud",
    "Certificación SCRUM",
    "Curso de React Avanzado",
]

talleres = [
    "Taller de Testing Automatizado",
    "Taller de Diseño UX",
    "Workshop CI/CD",
    "Taller de Microservicios",
    "Práctica intensiva de APIs",
]

ocio = [
    "Tiempo libre / videojuegos",
    "Salir a caminar",
    "Series / Películas",
    "Reunión con amigos",
    "Música y relajación",
]

responsabilidades = [
    "Limpieza",
    "Compras",
    "Lavar ropa",
    "Ordenar escritorio",
]

lugares_lima = [
    "Miraflores", "San Isidro", "Centro de Lima", "La Molina", "Surco",
    "Barranco", "San Miguel", "Pueblo Libre"
]


# ============================
#   GENERACIÓN POR DÍA
# ============================

for i in range(dias_mes):

    dia = inicio + timedelta(days=i)
    fecha = dia.strftime("%Y-%m-%d")
    dow = dia.weekday()       # 0=Lunes ... 6=Domingo

    # 💤 Dormir
    eventos.append(("Dormir", "Rutina", fecha, "23:30", "07:00", 1, "Sueño", "Baja"))

    # ---------------------- MAÑANA ----------------------
    # Viaje
    if dow < 5:
        eventos.append(("Viaje al campus", "Transporte", fecha, "07:00", "07:50", 0, "", "Baja"))

    # Clases (rotan)
    clases_lista = [
        ("Arquitectura de Software Avanzada", "08:00", "10:00"),
        ("Desarrollo de Tesis II", "09:00", "11:00"),
        ("Ingeniería de Requisitos", "08:30", "10:30"),
        ("Compiladores Modernos", "10:00", "12:00"),
        ("Scrum y Gestión Ágil", "09:30", "11:30"),
    ]
    clase = random.choice(clases_lista)
    eventos.append((clase[0], "Académico", fecha, clase[1], clase[2], 1, "Clase universitaria", "Alta"))

    # Taller o curso en la mañana
    if random.random() < 0.4:
        title = random.choice(talleres + cursos)
        eventos.append((title, "Aprendizaje", fecha, "11:30", "13:00", 0, "", "Media"))

    # ---------------------- TARDE ----------------------
    # Trabajo part-time (lunes a viernes)
    if dow < 5:
        eventos.append(("Trabajo de programación", "Laboral", fecha,
                        "14:00", "18:00", 0, "Desarrollo web / backend", "Alta"))

    # Investigación de tesis
    eventos.append(("Investigación de tesis", "Proyecto académico", fecha,
                    "18:00", "20:00", 0, "Análisis de datos / redacción", "Alta"))

    # Charla / conferencia en Lima
    if random.random() < 0.5:
        title = random.choice(charlas)
        distrito = random.choice(lugares_lima)
        eventos.append((title, "Evento / Conferencia", fecha,
                        "15:00", "17:00", 0, f"Auditorio en {distrito}", "Media"))

    # ---------------------- NOCHE ----------------------
    # Estudio nocturno
    eventos.append(("Estudio personal", "Académico", fecha,
                    "20:00", "22:00", 0, "Repaso de cursos", "Alta"))

    # Ocio
    title = random.choice(ocio)
    eventos.append((title, "Ocio", fecha, "22:00", "23:00", 0, "", "Baja"))

    # Responsabilidades (fin de semana)
    if dow >= 5:
        title = random.choice(responsabilidades)
        eventos.append((title, "Responsabilidad", fecha, "12:00", "13:00", 0, "", "Media"))

    # Salida con pareja o amigos (viernes, sábado)
    if dow in [4, 5]:
        eventos.append(("Salida social", "Vida personal", fecha,
                        "19:00", "21:00", 0, "Comida o paseo", "Media"))


# ============================
#   INSERTAR EN LA BASE
# ============================

for ev in eventos:
    cur.execute("""
    INSERT INTO events (user_id, title, category, date, start, end, fixed, notes, priority)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, *ev))

conn.commit()
conn.close()

print(f"🎉 {len(eventos)} eventos agregados correctamente para diciembre 2025.")
