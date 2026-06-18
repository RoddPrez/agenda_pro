import sqlite3
from datetime import datetime, timedelta
import random

DB = "agenda_pro.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("📌 Insertando datos para JUNIO 2026...")

# ---------- Crear usuario base ----------
cur.execute("""
INSERT OR IGNORE INTO users (username, password, nombre, carrera, semestre)
VALUES ('diego_ramirez', 'chosica2026', 'Diego Ramírez', 'Ingeniería de Software', 10)
""")

cur.execute("SELECT id FROM users WHERE username='diego_ramirez'")
user_id = cur.fetchone()[0]


# ===========================================================
#                GENERADOR DE EVENTOS COMPLETO
# ===========================================================

eventos = []

inicio = datetime(2026, 6, 1)
dias_mes = 30

# Catálogos de actividades

# Cursos típicos de 10mo ciclo de Ingeniería de Software UNMSM
clases_lista = [
    ("Taller de Tesis II", "08:00", "10:00"),
    ("Gestión de Proyectos de TI", "10:00", "12:00"),
    ("Calidad y Pruebas de Software", "08:30", "10:30"),
    ("Arquitectura de Software Empresarial", "09:00", "11:00"),
    ("Seminario de Ingeniería de Software", "10:30", "12:30"),
    ("Ética y Realidad Nacional", "08:00", "09:30"),
]

charlas = [
    "Charla de IA aplicada al sector bancario",
    "Conferencia de Ciberseguridad",
    "Evento DevOps Lima",
    "Meetup de Software Architecture",
    "Charla Big Data y Analytics",
    "Seminario Blockchain",
    "Webinar de Data Engineering BCP",
]

cursos = [
    "Curso virtual de Kubernetes",
    "Curso de Machine Learning",
    "Curso de Arquitectura Cloud (AWS)",
    "Certificación SCRUM",
    "Curso de Power BI Avanzado",
    "Curso de SQL para Analítica",
]

talleres = [
    "Taller de Testing Automatizado",
    "Taller de Diseño UX",
    "Workshop CI/CD",
    "Taller de Microservicios",
    "Práctica intensiva de APIs",
    "Taller de Visualización de Datos",
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

    # Modalidad de trabajo en BCP: alterna virtual y presencial (lunes a viernes)
    modalidad_bcp = random.choice(["presencial", "virtual"]) if dow < 5 else None

    # 💤 Dormir (ciclo circadiano, se acuesta temprano por el viaje largo desde Chosica)
    if dow < 5 and modalidad_bcp == "presencial":
        eventos.append(("Dormir", "Rutina", fecha, "23:00", "05:30", 1, "Sueño", "Baja"))
    elif dow >= 5:
        eventos.append(("Dormir", "Rutina", fecha, "23:00", "06:30", 1, "Sueño, descanso de fin de semana", "Baja"))
    else:
        eventos.append(("Dormir", "Rutina", fecha, "22:30", "05:30", 1, "Sueño", "Baja"))

    # ---------------------- MAÑANA ----------------------

    if dow < 5:
        # Traslado largo desde Chosica
        if modalidad_bcp == "presencial" or random.random() < 0.6:
            # Día con clases en la UNMSM (Cercado de Lima) -> viaje largo desde Chosica
            eventos.append(("Viaje Chosica - UNMSM", "Transporte", fecha, "05:45", "07:30", 0,
                            "Bus + Metropolitano, aprox. 1h 45min", "Alta"))
        else:
            eventos.append(("Viaje Chosica - Estación cercana", "Transporte", fecha, "06:30", "07:00", 0,
                            "Traslado corto antes de conectarse de forma remota", "Baja"))

    # Desayuno (ciclo circadiano)
    eventos.append(("Desayuno", "Alimentación", fecha, "07:30", "08:00", 1, "Comida principal antes de clases/trabajo", "Media"))

    # Clases (10mo ciclo, rotan) - solo días de semana
    if dow < 5:
        clase = random.choice(clases_lista)
        eventos.append((clase[0], "Académico", fecha, clase[1], clase[2], 1, "Clase universitaria - UNMSM", "Alta"))

    # Taller o curso en la mañana
    if random.random() < 0.35:
        title = random.choice(talleres + cursos)
        eventos.append((title, "Aprendizaje", fecha, "11:30", "13:00", 0, "", "Media"))

    # ---------------------- ALMUERZO ----------------------
    eventos.append(("Almuerzo", "Alimentación", fecha, "13:00", "13:45", 1, "Pausa de mediodía", "Media"))

    # ---------------------- TARDE ----------------------

    # Práctica profesional en BCP (Analítica y Tecnología), lunes a viernes
    if dow < 5:
        if modalidad_bcp == "presencial":
            eventos.append(("Viaje a oficinas BCP (San Isidro)", "Transporte", fecha,
                            "13:45", "14:30", 0, "Traslado desde UNMSM hacia oficina", "Alta"))
            eventos.append(("Práctica en BCP - Analítica y Tecnología", "Laboral", fecha,
                            "14:30", "19:00", 1, "Modalidad presencial - Oficina San Isidro", "Alta"))
            eventos.append(("Viaje BCP - Chosica", "Transporte", fecha,
                            "19:00", "21:00", 0, "Retorno a casa, hora punta", "Alta"))
        else:
            eventos.append(("Práctica en BCP - Analítica y Tecnología", "Laboral", fecha,
                            "14:30", "19:00", 1, "Modalidad virtual - Home office", "Alta"))

    # Investigación de tesis (todos los días, prioridad alta por estar en 10mo ciclo)
    if dow < 4:
        if modalidad_bcp == "presencial":
            # Llega tarde por el viaje desde BCP, la tesis se hace después del retorno
            eventos.append(("Investigación de tesis", "Proyecto académico", fecha,
                            "21:00", "22:00", 0, "Análisis de datos / redacción - Taller de Tesis II", "Alta"))
        else:
            eventos.append(("Investigación de tesis", "Proyecto académico", fecha,
                            "19:30", "21:00", 0, "Análisis de datos / redacción - Taller de Tesis II", "Alta"))
    elif dow == 4 and modalidad_bcp == "virtual":
        # Viernes virtual: hay tiempo antes de la salida social de la noche
        eventos.append(("Investigación de tesis", "Proyecto académico", fecha,
                        "19:00", "20:15", 0, "Análisis de datos / redacción - Taller de Tesis II", "Alta"))
    elif dow >= 5:
        eventos.append(("Investigación de tesis", "Proyecto académico", fecha,
                        "16:00", "18:30", 0, "Avance de capítulos y revisión con asesor", "Alta"))
    # Viernes presencial (dow==4 y modalidad_bcp=="presencial"): el viaje de retorno (19:00-21:00)
    # y la salida social no dejan margen, se descansa de la tesis ese día y se retoma el fin de semana.

    # Charla / conferencia en Lima (fines de semana o tarde libre)
    if random.random() < 0.3:
        title = random.choice(charlas)
        distrito = random.choice(lugares_lima)
        eventos.append((title, "Evento / Conferencia", fecha,
                        "15:00", "17:00", 0, f"Auditorio / webinar en {distrito}", "Media"))

    # ---------------------- CENA Y NOCHE ----------------------

    if dow == 5:
        # Sábado con salida social: la salida reemplaza cena + estudio + ocio en casa
        eventos.append(("Salida social", "Vida personal", fecha, "19:00", "22:30", 0,
                        "Cena afuera y paseo con amigos/pareja", "Media"))
    elif dow < 4 and modalidad_bcp == "presencial":
        # Llega tarde por el viaje BCP-Chosica (termina 21:00), luego tesis 21:00-22:00
        eventos.append(("Cena", "Alimentación", fecha, "22:00", "22:25", 1, "Última comida del día", "Media"))
        eventos.append(("Estudio personal", "Académico", fecha, "22:25", "22:30", 0,
                        "Repaso breve antes de dormir", "Baja"))
        title = random.choice(ocio)
        eventos.append((title, "Ocio", fecha, "22:30", "23:00", 0,
                        "Tiempo de relajación antes de dormir", "Baja"))
    elif dow < 4:
        # Día virtual: termina práctica a las 19:00, más margen en la noche
        eventos.append(("Cena", "Alimentación", fecha, "21:15", "21:45", 1, "Última comida del día", "Media"))
        eventos.append(("Estudio personal", "Académico", fecha, "21:45", "22:30", 0,
                        "Repaso de cursos / avance de tesis", "Alta"))
        title = random.choice(ocio)
        eventos.append((title, "Ocio", fecha, "22:30", "23:00", 0,
                        "Tiempo de relajación antes de dormir", "Baja"))
    elif dow == 4:
        # Viernes: la salida social (más abajo) reemplaza cena/estudio/ocio en casa
        pass
    else:
        # Domingo
        eventos.append(("Cena", "Alimentación", fecha, "20:00", "20:30", 1, "Última comida del día", "Media"))
        eventos.append(("Estudio personal", "Académico", fecha, "20:30", "21:30", 0,
                        "Repaso de cursos / avance de tesis", "Alta"))
        title = random.choice(ocio)
        eventos.append((title, "Ocio", fecha, "21:30", "22:30", 0,
                        "Tiempo de relajación antes de dormir", "Baja"))

    # Responsabilidades (fin de semana)
    if dow >= 5:
        title = random.choice(responsabilidades)
        eventos.append((title, "Responsabilidad", fecha, "12:00", "13:00", 0, "", "Media"))

    # Salida con pareja o amigos en viernes (sábado se maneja arriba junto con la cena)
    if dow == 4 and modalidad_bcp == "presencial":
        # Llega a las 21:00 por el viaje desde BCP, sale un poco más tarde
        eventos.append(("Salida social", "Vida personal", fecha,
                        "21:15", "23:00", 0, "Comida o paseo, reemplaza cena en casa y ocio", "Media"))
    elif dow == 4:
        eventos.append(("Salida social", "Vida personal", fecha,
                        "20:30", "22:30", 0, "Comida o paseo, reemplaza cena en casa y ocio", "Media"))

    # Descanso adicional fin de semana (compensa el desgaste de la semana)
    if dow == 6:
        eventos.append(("Siesta / descanso", "Rutina", fecha, "14:00", "15:00", 0,
                        "Recuperación del sueño acumulado en la semana", "Baja"))


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

print(f"🎉 {len(eventos)} eventos agregados correctamente para junio 2026.")
