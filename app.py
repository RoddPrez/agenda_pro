import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, date, time, timedelta
import os, textwrap
from ics import Calendar, Event
from sqlalchemy import create_engine, text

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Agenda Académica Inteligente — PRO", layout="wide")
st.title("📚 Agenda Académica Inteligente — PRO (Estudiantes TIC)")

# DB (SQLite local file)
# Ruta absoluta para que SIEMPRE use la misma base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "agenda_pro.db")

engine = create_engine(f"sqlite:///{DB_FILE}", echo=False, future=True)

# ----------------------------
# DB HELPERS
# ----------------------------
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            category TEXT,
            date TEXT,
            start TEXT,
            end TEXT,
            fixed INTEGER,
            notes TEXT,
            priority TEXT
        )
        """))

def add_user(username, password):
    with engine.begin() as conn:
        conn.execute(text("""
        INSERT OR IGNORE INTO users (username, password) VALUES (:u, :p)
        """), {"u": username, "p": password})

def get_user(username, password):
    q = text("SELECT * FROM users WHERE username=:u AND password=:p")
    df = pd.read_sql(q, engine, params={"u": username, "p": password})
    return df.iloc[0].to_dict() if not df.empty else None

def get_user_by_name(username):
    q = text("SELECT * FROM users WHERE username=:u")
    df = pd.read_sql(q, engine, params={"u": username})
    return df.iloc[0].to_dict() if not df.empty else None

def add_event(user_id, title, category, date_s, start_s, end_s, fixed, notes, priority):
    with engine.begin() as conn:
        conn.execute(text("""
        INSERT INTO events (user_id, title, category, date, start, end, fixed, notes, priority)
        VALUES (:uid,:t,:c,:d,:s,:e,:f,:n,:pr)
        """), {"uid": user_id, "t": title, "c": category, "d": date_s, "s": start_s, "e": end_s, "f": int(fixed), "n": notes, "pr": priority})

def update_event(eid, title, category, date_s, start_s, end_s, fixed, notes, priority):
    with engine.begin() as conn:
        conn.execute(text("""
        UPDATE events SET title=:t, category=:c, date=:d, start=:s, end=:e, fixed=:f, notes=:n, priority=:pr WHERE id=:id
        """), {"t": title, "c": category, "d": date_s, "s": start_s, "e": end_s, "f": int(fixed), "n": notes, "pr": priority, "id": eid})

def delete_event(eid):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM events WHERE id=:id"), {"id": eid})

def get_events(user_id):
    q = text("SELECT * FROM events WHERE user_id=:id ORDER BY date,start")
    return pd.read_sql(q, engine, params={"id": user_id})

# ----------------------------
# INIT
# ----------------------------
init_db()
# demo user
add_user("estudiante", "1234")

# ----------------------------
# AUTH
# ----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.header("🔐 Acceso")
    c1, c2 = st.columns(2)
    with c1:
        user_in = st.text_input("Usuario")
        pw_in = st.text_input("Contraseña", type="password")
        if st.button("Iniciar sesión"):
            u = get_user(user_in, pw_in)
            if u:
                st.session_state.user = u
                st.success("Sesión iniciada.")
                st.rerun()

            else:
                st.error("Usuario/contraseña incorrectos.")
    with c2:
        st.markdown("¿Nuevo? crea una cuenta rápida:")
        new_user = st.text_input("Nuevo usuario")
        new_pw = st.text_input("Nueva contraseña", type="password")
        if st.button("Crear cuenta"):
            if not new_user or not new_pw:
                st.warning("Completa usuario y contraseña.")
            else:
                add_user(new_user, new_pw)
                st.success("Cuenta creada. Inicia sesión arriba.")
    st.stop()

# ----------------------------
# Sidebar - info & Gemini (opcional)
# ----------------------------
st.sidebar.markdown(f"**Usuario:** {st.session_state.user['username']}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.user = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("**Gemini (opcional)**")
st.sidebar.markdown("Si quieres usar Gemini para recomendaciones, configura la variable de entorno `GEMINI_API_KEY` antes de ejecutar Streamlit.")
gem_key_env = os.environ.get("GEMINI_API_KEY", "")
if gem_key_env:
    st.sidebar.success("GEMINI_API_KEY encontrado en environment")
else:
    st.sidebar.info("GEMINI_API_KEY no configurada (usar optimizador local)")

# ----------------------------
# HELPERS: parse time / durations / energy / burnout
# ----------------------------
def parse_time_str_safe(s):
    """Return datetime.time from multiple input formats, fallback to 00:00."""
    if isinstance(s, time):
        return s
    if not isinstance(s, str):
        return datetime.strptime("00:00", "%H:%M").time()
    # try likely formats
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time()
        except:
            pass
    try:
        return datetime.fromisoformat(s).time()
    except:
        return datetime.strptime("00:00", "%H:%M").time()

def dur_hours(start_s, end_s):
    s = parse_time_str_safe(start_s)
    e = parse_time_str_safe(end_s)
    start_dt = datetime.combine(date.min, s)
    end_dt = datetime.combine(date.min, e)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return (end_dt - start_dt).total_seconds()/3600.0

def hour_energy(h):
    # heuristic energy factor (0..1)
    if 9 <= h < 12: return 0.95
    if 16 <= h < 20: return 0.92
    if 6 <= h < 9: return 0.75
    if 12 <= h < 16: return 0.78
    if 20 <= h < 23: return 0.6
    return 0.35

def event_energy_score(row):
    start_dt = datetime.combine(date.min, parse_time_str_safe(row["start"]))
    end_dt = datetime.combine(date.min, parse_time_str_safe(row["end"]))
    if end_dt <= start_dt: end_dt += timedelta(days=1)
    t = start_dt
    vals = []
    while t < end_dt:
        vals.append(hour_energy(t.hour))
        t += timedelta(hours=1)
    return float(np.mean(vals)) if vals else 0.0

def burnout_score(events_df):
    if events_df.empty:
        return {"score": 0.2, "risk": "Bajo", "notes": "No hay datos."}
    df = events_df.copy()
    df["dur"] = df.apply(lambda r: dur_hours(r["start"], r["end"]), axis=1)
    total_study = df[df["category"].isin(["Estudio","Tarea","Tesis","Clase","Proyecto TI","Investigación"])]["dur"].sum()
    total_work = df[df["category"]=="Trabajo"]["dur"].sum()
    sleep = df[df["category"]=="Sueño"]["dur"].sum()
    desired_sleep = 7 * 7.0  # 49h/week -> 7h/night
    sleep_factor = min(1.0, sleep / desired_sleep)
    study_factor = min(1.0, total_study / 20.0)
    work_factor = min(1.0, total_work / 30.0)
    score = 0.5*(1 - sleep_factor) + 0.3*(study_factor) + 0.2*(work_factor)
    score = float(max(0.0, min(1.0, score)))
    if score < 0.3: risk = "Bajo"
    elif score < 0.6: risk = "Medio"
    else: risk = "Alto"
    notes = f"Semana: Estudio {total_study:.1f}h, Trabajo {total_work:.1f}h, Sueño {sleep:.1f}h."
    return {"score": score, "risk": risk, "notes": notes}

# ----------------------------
# CRUD UI: add / edit / delete
# ----------------------------
st.markdown("## 🗓️ Agenda — Crear / Editar / Eliminar")

colA, colB = st.columns([2,1])
with colA:
    with st.form("add_event_form", clear_on_submit=False):
        title = st.text_input("Título", value="Estudiar")
        category = st.selectbox("Categoría", ["Estudio","Tarea","Clase","Tesis","Trabajo","Proyecto TI","Investigación","Deporte","Sueño","Ocio","Otro"])
        date_ev = st.date_input("Fecha", value=date.today())
        start_ev = st.time_input("Inicio", value=time(18,0))
        end_ev = st.time_input("Fin", value=time(19,30))
        fixed = st.checkbox("Evento fijo (no mover)", value=False)
        priority = st.selectbox("Prioridad", ["Baja","Media","Alta"])
        notes = st.text_area("Notas / Detalles", value="")
        if st.form_submit_button("➕ Añadir a mi agenda"):
            add_event(st.session_state.user["id"], title, category, str(date_ev), start_ev.strftime("%H:%M"), end_ev.strftime("%H:%M"), fixed, notes, priority)
            st.success("Evento guardado.")
            st.rerun()

with colB:
    st.write("Eventos actuales (selecciona para editar o eliminar).")
    events_df = get_events(st.session_state.user["id"])
    if events_df.empty:
        st.info("Aún no tienes eventos; añade algunos para probar las funciones PRO.")
    else:
        events_df["dur_h"] = events_df.apply(lambda r: dur_hours(r["start"], r["end"]), axis=1)
        st.metric("Total horas (registradas)", f"{events_df['dur_h'].sum():.1f} h")
        st.metric("Eventos registrados", len(events_df))

# Edit / delete panel
st.markdown("### ✏️ Editar / Eliminar evento")
events_df = get_events(st.session_state.user["id"])
if not events_df.empty:
    select_options = [0] + events_df["id"].tolist()
    select_id = st.selectbox("Selecciona evento (id) para editar/eliminar", options=select_options, format_func=lambda x: ("-- ninguno --" if x==0 else f"{int(x)} - " + events_df[events_df["id"]==int(x)]["title"].iloc[0] if int(x) in events_df["id"].values else str(x)))
    if select_id and select_id != 0:
        row = events_df[events_df["id"]==int(select_id)].iloc[0]
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("Título", value=row["title"])
            categories_list = ["Estudio","Tarea","Clase","Tesis","Trabajo","Proyecto TI","Investigación","Deporte","Sueño","Ocio","Otro"]
            new_category = st.selectbox("Categoría", categories_list, index=categories_list.index(row["category"]) if row["category"] in categories_list else 0)
            new_priority = st.selectbox("Prioridad", ["Baja","Media","Alta"], index=["Baja","Media","Alta"].index(row["priority"]) if row["priority"] in ["Baja","Media","Alta"] else 1)
        with col2:
            # safe parse start/end
            try:
                parsed_start = parse_time_str_safe(row["start"])
            except:
                parsed_start = time(18,0)
            try:
                parsed_end = parse_time_str_safe(row["end"])
            except:
                parsed_end = time(19,30)
            new_date = st.date_input("Fecha", value=pd.to_datetime(row["date"]).date())
            new_start = st.time_input("Inicio", value=parsed_start)
            new_end = st.time_input("Fin", value=parsed_end)
            new_fixed = st.checkbox("Fijo (no mover)", value=bool(int(row["fixed"]) if pd.notna(row["fixed"]) else False))
            new_notes = st.text_area("Notas", value=row["notes"] or "")
        if st.button("💾 Guardar cambios"):
            update_event(int(select_id), new_title, new_category, str(new_date), new_start.strftime("%H:%M"), new_end.strftime("%H:%M"), 1 if new_fixed else 0, new_notes, new_priority)
            st.success("Evento actualizado.")
            st.rerun()

        if st.button("🗑 Eliminar evento"):
            delete_event(int(select_id))
            st.warning("Evento eliminado.")
            st.rerun()
else:
    st.info("No hay eventos para editar.")

# ----------------------------
# Calendar Week View
# ----------------------------
st.markdown("## 📆 Vista semanal (Timeline Inteligente)")

week_start = st.date_input(
    "📅 Selecciona semana (Elige el Lunes)",
    value=(date.today() - timedelta(days=date.today().weekday()))
)
week_days = [week_start + timedelta(days=i) for i in range(7)]

events_week = get_events(st.session_state.user["id"])

if not events_week.empty:
    events_week["date_dt"] = pd.to_datetime(events_week["date"], errors="coerce").dt.date
    evw = events_week[events_week["date_dt"].isin(week_days)].copy()
    if evw.empty:
        st.warning("📌 No hay eventos programados para esta semana.")
    else:
        def to_dt(row):
            d = row["date_dt"]
            s = parse_time_str_safe(row["start"])
            e = parse_time_str_safe(row["end"])
            start_dt = datetime.combine(d, s)
            end_dt = datetime.combine(d, e)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            return start_dt, end_dt

        evw["start_dt"], evw["end_dt"] = zip(*evw.apply(lambda r: to_dt(r), axis=1))
        if "notes" not in evw.columns:
            evw["notes"] = ""
        fig = px.timeline(
            evw,
            x_start="start_dt",
            x_end="end_dt",
            y="title",
            color="category",
            hover_data={"notes": True, "date": True, "start": True, "end": True}
        )
        fig.update_layout(title="🧠 Distribución semanal de actividades")
        fig.update_yaxes(title="Actividad", autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Aún no tienes actividades registradas. Agrega una arriba para comenzar.")

# ----------------------------
# Optimizer: local + Gemini (optional)
# ----------------------------
st.markdown("## 🤖 Optimización y Recomendaciones")

def local_optimizer_impl(user_id, goals_text="", block_hours=1.5):
    df = get_events(user_id)
    if df.empty:
        return {"suggestions": [], "study_blocks": [], "target_week": 12.0, "existing_study": 0.0}
    df["dur_h"] = df.apply(lambda r: dur_hours(r["start"], r["end"]), axis=1)
    df["energy"] = df.apply(lambda r: event_energy_score(r), axis=1)
    suggestions = []
    low = df[(df["fixed"]==0) & (df["energy"]<0.6)].sort_values("energy")
    for _, r in low.iterrows():
        d = pd.to_datetime(r["date"]).date()
        day_ev = df[pd.to_datetime(df["date"]).dt.date==d]
        busy = []
        for _, b in day_ev.iterrows():
            busy.append((parse_time_str_safe(b["start"]), parse_time_str_safe(b["end"])))
        dur_min = int(r["dur_h"]*60)
        candidates=[]
        for hour in range(6,22):
            a = time(hour,0)
            btime = (datetime.combine(date.min,a)+timedelta(minutes=dur_min)).time()
            sa = datetime.combine(date.min,a); sb = datetime.combine(date.min,btime)
            overlaps=False
            for (x,y) in busy:
                xa = datetime.combine(date.min,x); yb = datetime.combine(date.min,y)
                if not (sb <= xa or sa >= yb):
                    overlaps=True; break
            if not overlaps:
                t=sa; vals=[]
                while t<sb:
                    vals.append(hour_energy(t.hour)); t+=timedelta(minutes=30)
                avg = np.mean(vals) if vals else 0
                candidates.append((a,btime,avg))
        for a,btime,avg in sorted(candidates, key=lambda x:-x[2]):
            if avg >= r["energy"] + 0.15:
                suggestions.append({"event_id": r["id"], "from": f"{r['date']} {r['start']}-{r['end']}", "to": f"{d} {a.strftime('%H:%M')}-{btime.strftime('%H:%M')}", "reason": f"Mejor energía ({avg:.2f} vs {r['energy']:.2f})"})
                break
    total_study = df[df["category"].isin(["Estudio","Tarea","Tesis","Clase","Investigación","Proyecto TI"])]["dur_h"].sum()
    target_week = max(12.0, total_study)
    remaining = max(0.0, target_week - total_study)
    study_blocks = []
    if remaining > 0:
        today = date.today()
        for i in range(7):
            if remaining <= 0: break
            d = today + timedelta(days=i)
            day_ev = df[pd.to_datetime(df["date"]).dt.date==d]
            busy=[]
            for _,b in day_ev.iterrows(): busy.append((parse_time_str_safe(b["start"]), parse_time_str_safe(b["end"])))
            for hour in range(18,22):
                a = time(hour,0)
                btime = (datetime.combine(date.min,a)+timedelta(minutes=int(block_hours*60))).time()
                sa = datetime.combine(date.min,a); sb = datetime.combine(date.min,btime)
                conflict=False
                for x,y in busy:
                    if not (sb <= datetime.combine(date.min,x) or sa >= datetime.combine(date.min,y)):
                        conflict=True; break
                if not conflict:
                    t=sa; vals=[]
                    while t<sb:
                        vals.append(hour_energy(t.hour)); t+=timedelta(minutes=30)
                    avg = np.mean(vals) if vals else 0
                    if avg >= 0.6:
                        study_blocks.append({"date":d,"start":a.strftime("%H:%M"),"end":btime.strftime("%H:%M"),"avg_energy":avg})
                        remaining -= block_hours
                        break
    return {"suggestions": suggestions, "study_blocks": study_blocks, "target_week": target_week, "existing_study": total_study}

col_opt1, col_opt2 = st.columns([3,1])
with col_opt1:
    goals = st.text_area("Objetivos / restricciones (p.ej. 'mantener trabajo, dormir 7h, aumentar estudio a 15h/sem')", height=100)
    if st.button("🔎 Generar optimización (local + Gemini si disponible)"):
        try:
            result = local_optimizer_impl(st.session_state.user["id"], goals_text=goals)
        except Exception as e:
            st.error(f"Error ejecutando optimizador local: {e}")
            result = {"suggestions": [], "study_blocks": [], "target_week": 12.0, "existing_study": 0.0}

        if result["suggestions"]:
            st.markdown("### ✅ Sugerencias de reubicación de eventos flexibles")
            for s in result["suggestions"]:
                st.markdown(f"- Evento {s['event_id']}: mover **{s['from']}** → **{s['to']}** ({s['reason']})")
        else:
            st.info("No hay sugerencias de reubicación de eventos flexibles (o no se encontró ventana mejor).")

        if result["study_blocks"]:
            st.markdown("### 📚 Bloques de estudio sugeridos")
            for b in result["study_blocks"]:
                st.markdown(f"- {b['date']} {b['start']}–{b['end']} (energía ~ {b['avg_energy']:.2f})")
            if st.button("➕ Añadir bloques sugeridos a la agenda"):
                for b in result["study_blocks"]:
                    add_event(st.session_state.user["id"], "Bloque de estudio (sugerido)", "Estudio", str(b["date"]), b["start"], b["end"], 0, "Sugerido por optimizador local", "Media")
                st.success("Bloques añadidos a la agenda.")
                st.rerun()
        else:
            st.info("No hay bloques sugeridos para añadir.")

with col_opt2:
    st.markdown("### AI / Gemini")
    gem_text = "(Gemini no configurado)"
    if os.environ.get("GEMINI_API_KEY"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            gem_text = "Gemini configurado. Se usará para consultas más avanzadas."
        except Exception as e:
            gem_text = f"Gemini detectado pero error: {e}"
    st.info(gem_text)

    if st.button("🔁 Ejecutar análisis avanzado (Gemini)"):
        if not os.environ.get("GEMINI_API_KEY"):
            st.error("GEMINI_API_KEY no configurada en el entorno.")
        else:
            df = get_events(st.session_state.user["id"])
            schedule_text = df.to_string(index=False)
            prompt = textwrap.dedent(f"""
            Eres un asistente experto en productividad para estudiantes universitarios de carreras TIC.
            Analiza la siguiente agenda y los objetivos:
            AGENDA:
            {schedule_text}

            OBJETIVOS:
            {goals}

            Devuelve: diagnóstico (breve), riesgos de burnout, recomendaciones priorizadas y un calendario alternativo de bloques (formato tabla).
            """)
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
                resp = genai.generate_text(model="models/gemini-2.5-flash", prompt=prompt, max_output_tokens=600)
                text = getattr(resp, "text", None) or getattr(resp, "output_text", None) or str(resp)
                st.subheader("Respuesta (Gemini)")
                st.write(text)
            except Exception as e:
                st.error(f"Error llamando a Gemini: {e}")

# ----------------------------
# Burnout & indicators
# ----------------------------
st.markdown("## 🩺 Indicadores de carga y riesgo")

events_all = get_events(st.session_state.user["id"])
burn = burnout_score(events_all)
st.metric("Riesgo de burnout", burn["risk"], delta=f"{burn['score']*100:.0f}%")
st.write(burn["notes"])

# ----------------------------
# Export (CSV / ICS)
# ----------------------------
st.markdown("## ⤓ Exportar / Compartir")
if not events_all.empty:
    csv_bytes = events_all.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Descargar CSV de agenda", data=csv_bytes, file_name="agenda.csv", mime="text/csv")
    c = Calendar()
    for _, ev in events_all.iterrows():
        e = Event()
        e.name = ev["title"]
        start_dt = datetime.combine(pd.to_datetime(ev["date"]).date(), parse_time_str_safe(ev["start"]))
        end_dt = datetime.combine(pd.to_datetime(ev["date"]).date(), parse_time_str_safe(ev["end"]))
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        e.begin = start_dt
        e.end = end_dt
        e.description = ev.get("notes","")
        c.events.add(e)
    st.download_button("📥 Descargar .ics (iCal)", data=str(c), file_name="agenda.ics", mime="text/calendar")
else:
    st.info("No hay eventos para exportar.")

# ----------------------------
# Footer / help
# ----------------------------
st.markdown("---")
st.caption("PRO: Este prototipo se puede extender: integración OAuth Google Calendar, notificaciones push, reconcilación de disponibilidad docentes, o versión multiusuario con roles.")

