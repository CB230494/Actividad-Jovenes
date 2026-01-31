import random
import streamlit as st

# ----------------------------
# Datos: orden canónico (protestante) de 66 libros
# ----------------------------
BOOKS = [
    "Génesis","Éxodo","Levítico","Números","Deuteronomio",
    "Josué","Jueces","Rut","1 Samuel","2 Samuel","1 Reyes","2 Reyes",
    "1 Crónicas","2 Crónicas","Esdras","Nehemías","Ester",
    "Job","Salmos","Proverbios","Eclesiastés","Cantares",
    "Isaías","Jeremías","Lamentaciones","Ezequiel","Daniel",
    "Oseas","Joel","Amós","Abdías","Jonás","Miqueas","Nahúm",
    "Habacuc","Sofonías","Hageo","Zacarías","Malaquías",
    "Mateo","Marcos","Lucas","Juan","Hechos",
    "Romanos","1 Corintios","2 Corintios","Gálatas","Efesios","Filipenses",
    "Colosenses","1 Tesalonicenses","2 Tesalonicenses",
    "1 Timoteo","2 Timoteo","Tito","Filemón",
    "Hebreos","Santiago","1 Pedro","2 Pedro",
    "1 Juan","2 Juan","3 Juan","Judas","Apocalipsis"
]
INDEX = {b: i for i, b in enumerate(BOOKS)}

# “Complicadas”: prioriza libros menos obvios (puedes modificar)
HARD_SET = set([
    "Abdías","Nahúm","Habacuc","Sofonías","Hageo","Zacarías","Malaquías",
    "Filemón","Judas","2 Juan","3 Juan","2 Pedro","2 Tesalonicenses",
    "2 Timoteo","Tito","Colosenses","1 Tesalonicenses","Lamentaciones",
    "Cantares","Ezequiel","Amós","Miqueas","Oseas","Joel"
])

def is_before(a: str, b: str) -> bool:
    return INDEX[a] < INDEX[b]

def normalize_pair(a: str, b: str):
    """Para que (A,B) y (B,A) cuenten como la misma pregunta y no se repitan."""
    return tuple(sorted([a, b], key=lambda x: INDEX[x]))

def pick_book(pool):
    return random.choice(pool)

def make_question(used_pairs: set, avoid_too_obvious=True):
    """
    Genera una pregunta no repetida:
    - statement: texto
    - correct: True/False
    - meta: (a, b, relation)
    """

    # Pool “difícil” (mayor probabilidad) + resto (por si no alcanza)
    hard_list = [b for b in BOOKS if b in HARD_SET]
    normal_list = [b for b in BOOKS if b not in HARD_SET]

    for _ in range(5000):
        # 75% de probabilidad de tomar “difícil”
        a = pick_book(hard_list if random.random() < 0.75 else BOOKS)
        b = pick_book(hard_list if random.random() < 0.75 else BOOKS)

        if a == b:
            continue

        # Evitar pares “demasiado obvios”: uno del AT y otro del NT con extremos grandes
        if avoid_too_obvious:
            dist = abs(INDEX[a] - INDEX[b])
            # Evita distancias enormes (tipo Génesis vs Apocalipsis)
            if dist > 45:
                continue
            # Evita distancias demasiado pequeñas (sería muy fácil si son casi consecutivos)
            if dist < 2:
                continue

        pair_key = normalize_pair(a, b)
        if pair_key in used_pairs:
            continue

        # Elegir relación a preguntar
        relation = random.choice(["antes", "después"])

        # Determinar la verdad real de la afirmación
        if relation == "antes":
            truth = is_before(a, b)
            statement = f"📖 **{a}** está **antes** que **{b}**."
        else:
            truth = (not is_before(a, b))
            statement = f"📖 **{a}** está **después** que **{b}**."

        # Para que haya V/F variado: a veces invertimos el enunciado
        # (Ej: si era verdadero, lo hacemos falso cambiando el orden)
        if random.random() < 0.5:
            # Cambiar orden de libros y recalcular
            a2, b2 = b, a
            pair_key2 = normalize_pair(a2, b2)
            # pair_key2 == pair_key, sigue sin repetición
            a, b = a2, b2
            if relation == "antes":
                truth = is_before(a, b)
                statement = f"📖 **{a}** está **antes** que **{b}**."
            else:
                truth = (not is_before(a, b))
                statement = f"📖 **{a}** está **después** que **{b}**."

        used_pairs.add(pair_key)
        return statement, truth, (a, b, relation)

    raise RuntimeError("No se pudo generar una pregunta única. Ajusta filtros.")

# ----------------------------
# Estado / lógica del juego
# ----------------------------
TOTAL_QUESTIONS = 15

def init_game():
    st.session_state.started = True
    st.session_state.q_index = 0
    st.session_state.used_pairs = set()
    st.session_state.red = 0
    st.session_state.blue = 0
    st.session_state.history = []  # (q#, team, statement, answer, correct)
    st.session_state.current = None  # (statement, truth, meta)

def current_team():
    # Alterna turnos: 0 -> Rojo, 1 -> Azul, 2 -> Rojo...
    return "🔴 Rojo" if st.session_state.q_index % 2 == 0 else "🔵 Azul"

def team_color(team_name: str):
    return "red" if "Rojo" in team_name else "blue"

def next_question():
    statement, truth, meta = make_question(
        st.session_state.used_pairs,
        avoid_too_obvious=True
    )
    st.session_state.current = (statement, truth, meta)

def answer(choice: bool):
    statement, truth, _meta = st.session_state.current
    team = current_team()
    ok = (choice == truth)

    if ok:
        if "Rojo" in team:
            st.session_state.red += 1
        else:
            st.session_state.blue += 1

    st.session_state.history.append(
        (st.session_state.q_index + 1, team, statement, choice, ok)
    )

    st.session_state.q_index += 1
    st.session_state.current = None

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Batalla Bíblica: Antes o Después", page_icon="📖", layout="centered")

st.title("📖 Batalla Bíblica: ¿Antes o Después?")
st.write("Dos equipos compiten respondiendo **Verdadero/Falso** sobre el orden de los libros de la Biblia.")

colA, colB = st.columns(2)
with colA:
    st.metric("🔴 Equipo Rojo", st.session_state.get("red", 0))
with colB:
    st.metric("🔵 Equipo Azul", st.session_state.get("blue", 0))

controls = st.columns([1, 1, 1])
with controls[0]:
    if st.button("🎮 Iniciar / Reiniciar juego", use_container_width=True):
        init_game()

with controls[1]:
    st.caption("15 preguntas · turnos alternos")

with controls[2]:
    if st.session_state.get("started", False):
        st.caption(f"Pregunta {st.session_state.q_index + 1} de {TOTAL_QUESTIONS}")

if not st.session_state.get("started", False):
    st.info("Presiona **Iniciar / Reiniciar juego** para comenzar.")
    st.stop()

# Si terminó el juego
if st.session_state.q_index >= TOTAL_QUESTIONS:
    st.subheader("🏁 Resultado final")

    r, b = st.session_state.red, st.session_state.blue
    if r > b:
        st.success(f"Ganó **🔴 Equipo Rojo** con {r} puntos 🎉")
    elif b > r:
        st.success(f"Ganó **🔵 Equipo Azul** con {b} puntos 🎉")
    else:
        st.warning(f"¡Empate! 🔴 {r} vs 🔵 {b}")

    with st.expander("📜 Ver historial de preguntas"):
        for qn, team, stmt, ans, ok in st.session_state.history:
            ans_txt = "Verdadero" if ans else "Falso"
            st.write(f"**{qn}. {team}** → {stmt}  \nRespuesta: **{ans_txt}** → {'✅' if ok else '❌'}")
    st.stop()

# Si no hay pregunta actual, crear una
if st.session_state.current is None:
    next_question()

statement, truth, _meta = st.session_state.current
team = current_team()

st.subheader(f"Turno de: {team}")
st.markdown(statement)

btn1, btn2 = st.columns(2)
with btn1:
    if st.button("✅ Verdadero", use_container_width=True):
        answer(True)
        st.rerun()

with btn2:
    if st.button("❌ Falso", use_container_width=True):
        answer(False)
        st.rerun()

with st.expander("📌 Reglas rápidas"):
    st.write("- 1 punto si acierta, 0 si falla.")
    st.write("- 15 preguntas, sin repetición de pares de libros.")
    st.write("- Turnos alternos: Rojo, Azul, Rojo, Azul…")










