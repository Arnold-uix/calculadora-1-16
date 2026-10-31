import streamlit as st
import pandas as pd
from itertools import product

st.set_page_config(page_title="Calculadora Tabla de la Verdad", layout="centered")

st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se muestra en **0 y 1**.")

# ---------------------------------------------------------------
# Estado de la sesión: lista de símbolos (permite "Borrar Último")
# ---------------------------------------------------------------
if "tokens" not in st.session_state:
    st.session_state.tokens = []


def agregar(simbolo):
    st.session_state.tokens.append(simbolo)


def borrar_ultimo():
    if st.session_state.tokens:
        st.session_state.tokens.pop()


def limpiar_todo():
    st.session_state.tokens = []


# ---------------------------------------------------------------
# Interfaz: Constructor de Expresión
# ---------------------------------------------------------------
st.subheader("🛠️ Constructor de Expresión")

st.markdown("**Variables:**")
variables = ["p", "q", "r", "s", "t", "u"]
cols = st.columns(6)
for i, v in enumerate(variables):
    with cols[i]:
        st.button(v, key=f"var_{v}", on_click=agregar, args=(v,), width="stretch")

st.markdown("**Operadores:**")
operadores = [("∧", "and"), ("∨", "or"), ("¬", "not"),
              ("⊕", "xor"), ("→", "imp"), ("↔", "iff")]
cols = st.columns(6)
for i, (simbolo, nombre) in enumerate(operadores):
    with cols[i]:
        st.button(simbolo, key=f"op_{nombre}", on_click=agregar, args=(simbolo,), width="stretch")

c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 1.5])
with c1:
    st.button("(", key="par_abre", on_click=agregar, args=("(",), width="stretch")
with c2:
    st.button(")", key="par_cierra", on_click=agregar, args=(")",), width="stretch")
with c3:
    st.button("🗑️ Limpiar Todo", key="limpiar", on_click=limpiar_todo, width="stretch")
with c4:
    st.button("⌫ Borrar Último", key="borrar", on_click=borrar_ultimo, width="stretch")

st.divider()

st.markdown("**Expresión actual:**")
st.code(" ".join(st.session_state.tokens) or "(vacío)", language="text")


# ---------------------------------------------------------------
# Lógica central: analizador sintáctico (sin usar eval)
# Precedencia (mayor a menor): ¬ , ∧ , ⊕ , ∨ , → , ↔
# ---------------------------------------------------------------
class Analizador:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def actual(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def consumir(self):
        tok = self.actual()
        self.i += 1
        return tok

    def analizar(self):
        nodo = self.bicondicional()
        if self.actual() is not None:
            raise ValueError("Símbolos sobrantes")
        return nodo

    def bicondicional(self):
        izq = self.implicacion()
        while self.actual() == "↔":
            self.consumir()
            izq = ("↔", izq, self.implicacion())
        return izq

    def implicacion(self):
        izq = self.disyuncion()
        if self.actual() == "→":
            self.consumir()
            return ("→", izq, self.implicacion())  # asociativa a la derecha
        return izq

    def disyuncion(self):
        izq = self.xor()
        while self.actual() == "∨":
            self.consumir()
            izq = ("∨", izq, self.xor())
        return izq

    def xor(self):
        izq = self.conjuncion()
        while self.actual() == "⊕":
            self.consumir()
            izq = ("⊕", izq, self.conjuncion())
        return izq

    def conjuncion(self):
        izq = self.negacion()
        while self.actual() == "∧":
            self.consumir()
            izq = ("∧", izq, self.negacion())
        return izq

    def negacion(self):
        if self.actual() == "¬":
            self.consumir()
            return ("¬", self.negacion())
        return self.atomo()

    def atomo(self):
        tok = self.consumir()
        if tok == "(":
            nodo = self.bicondicional()
            if self.consumir() != ")":
                raise ValueError("Falta cerrar paréntesis")
            return nodo
        if tok in variables:
            return ("var", tok)
        raise ValueError("Expresión incompleta")


def evaluar(nodo, entorno):
    tipo = nodo[0]
    if tipo == "var":
        return entorno[nodo[1]]
    if tipo == "¬":
        return not evaluar(nodo[1], entorno)
    a = evaluar(nodo[1], entorno)
    b = evaluar(nodo[2], entorno)
    if tipo == "∧":
        return a and b
    if tipo == "∨":
        return a or b
    if tipo == "⊕":
        return a != b
    if tipo == "→":
        return (not a) or b
    if tipo == "↔":
        return a == b
    raise ValueError("Operador desconocido")


def generar_tabla(tokens):
    arbol = Analizador(tokens).analizar()
    vars_usadas = sorted({t for t in tokens if t in variables})
    if not vars_usadas:
        raise ValueError("Sin variables")

    filas = []
    for valores in product([0, 1], repeat=len(vars_usadas)):
        entorno = {v: bool(val) for v, val in zip(vars_usadas, valores)}
        resultado = evaluar(arbol, entorno)
        filas.append(list(valores) + [int(resultado)])
    return vars_usadas, filas


# ---------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------
if st.button("🚀 Generar Tabla", type="primary", width="stretch"):
    if not st.session_state.tokens:
        st.warning("⚠️ Ingresa o construye una expresión primero.")
    else:
        try:
            vars_usadas, filas = generar_tabla(st.session_state.tokens)
        except (ValueError, IndexError):
            st.error("❌ Expresión inválida. Revisa operadores y paréntesis.")
        else:
            df = pd.DataFrame(filas, columns=vars_usadas + ["Resultado"])
            st.success(f"✅ Tabla generada para {len(vars_usadas)} variable(s)")
            st.dataframe(df, width="stretch", hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Descargar CSV", csv, "tabla_verdad.csv", "text/csv")