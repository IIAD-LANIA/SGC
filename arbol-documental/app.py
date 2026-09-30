"""Árbol documental IIAD — LANIA · ICA

Guía de consulta de los documentos del sistema de gestión que evidencian cada
requisito de ISO 17034:2016 e ISO/IEC 17043:2023 (numerales según
GSA-MC-SAD-003 V3).

Datos:
  data/arbol.csv     una fila por aparición de un documento en un numeral
  data/catalogo.csv  una fila por documento; aquí se registra el enlace

Para actualizar un enlace se edita data/catalogo.csv en GitHub; la app se
vuelve a desplegar sola con el nuevo commit.

Colores y tipografía según la «Guía para editores web y gestores de
contenido del ICA» (2025); ver tema.py.
"""
import base64
from pathlib import Path
import unicodedata

import pandas as pd
import streamlit as st

from arbol_svg import construir_svg, pagina_html
from tabla_periodica import datos_tabla, pagina as pagina_tabla
from tema import FUENTE, FUENTE_URL, LIMA, TEXTO, TIPO_ESTILO, TITULO, VERDE, VERDE_OSC

BASE = Path(__file__).parent
DATA = BASE / "data"
LOGO = BASE / "assets" / "logo_ica_blanco.png"

TIPOS = list(TIPO_ESTILO)
NORMAS = ["ISO 17034", "ISO/IEC 17043"]
NOMBRE_NORMA = {"ISO 17034": "ISO 17034:2016 · Productores de materiales de referencia",
                "ISO/IEC 17043": "ISO/IEC 17043:2023 · Proveedores de ensayos de aptitud"}
TRONCO7 = {"ISO 17034": "Requisitos técnicos y de producción de MR", "ISO/IEC 17043": "Requisitos del proceso de EA"}

CORRECCIONES = [
    "**ISO 17034, 7.17.** El Visio asigna «GSA-SAD-P-014 Gestión del trabajo no conforme». "
    "GSA-SAD-P-014 V1 es *Instalaciones y condiciones ambientales*; se reemplazó por "
    "**GSA-SAD-P-004 V12** *Control del trabajo no conforme*.",
    "**ISO 17034, 7.3 · ISO/IEC 17043, 7.5.** «GSA-SAD-P-020 Manejo de documentos y registros» "
    "se reemplazó por **GSA-I-SAD-020 V11**; GSA-SAD-P-020 V2 es *Ingreso a los laboratorios de la SAD*.",
    "**Ambos árboles, 7.3/7.5, 8.6 y 8.7.** «GSA-SAD-007» se corrigió a **GSA-I-SAD-007 V8** "
    "*Acciones correctivas y de mejora* (es instructivo, no procedimiento).",
    "**ISO/IEC 17043, 7.2 y 7.3.** «GSAD-SAD-P-028» y «GSAD-SAD-P-030» se corrigieron a "
    "GSA-SAD-P-028 y GSA-SAD-P-030.",
    "**ISO/IEC 17043, capítulo 7.** El Visio lo rotula «Requisitos técnicos de producción MR» "
    "(copiado del árbol de ISO 17034); aquí se presenta como *Requisitos del proceso de EA*.",
    "**Nombres unificados con la versión vigente:** GSA-I-SAD-038, GSA-I-SAD-020, GSA-SAD-P-008 y GSA-SAD-P-025.",
    "**Por revisar, sin aplicar:** GSA-SAD-P-033 V2 cubre el diseño estadístico de EA *y de MR*, pero solo "
    "aparece en el árbol de ISO/IEC 17043. No hay documentos ubicados en el numeral 7.1 de ISO 17034.",
]

st.set_page_config(page_title="Árbol documental IIAD · ICA", page_icon="🌳", layout="wide")

st.markdown(
    f"""
    <style>
      @import url("{FUENTE_URL}");
      html, body, .stApp{{font-family:{FUENTE};color:{TEXTO}}}
      .stApp h1, .stApp h2, .stApp h3{{font-family:{FUENTE};color:{TITULO}}}
      .block-container{{padding-top:3.4rem}}
      /* color institucional aunque no se cargue .streamlit/config.toml */
      .stTabs [data-baseweb="tab-highlight"]{{background-color:{VERDE} !important}}
      .stTabs button[aria-selected="true"] p{{color:{VERDE_OSC} !important}}
      .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p{{font-weight:700}}
      .ica-band{{background:{VERDE_OSC};border-radius:10px;padding:18px 24px;display:flex;align-items:center;gap:26px;
                flex-wrap:wrap;border-bottom:8px solid {LIMA};margin-bottom:.6rem}}
      .ica-band img{{height:62px;width:auto}}
      .ica-band .sep{{width:1px;align-self:stretch;background:rgba(255,255,255,.35)}}
      .ica-band .txt{{color:#fff;min-width:0;flex:1 1 320px}}
      .ica-band .eb{{font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;opacity:.9;font-weight:700}}
      .ica-band h1{{font-family:{FUENTE};font-weight:800;font-size:2.2rem;line-height:1.1;margin:.15rem 0 .25rem;padding:0;color:#fff}}
      .ica-band .sub{{font-size:1rem;opacity:.92;margin:0}}
      [data-testid="stMetricValue"]{{font-family:{FUENTE};font-weight:800;color:{VERDE_OSC}}}
      section[data-testid="stSidebar"]{{border-right:4px solid {LIMA}}}
    </style>
    """,
    unsafe_allow_html=True,
)


def _norm(s: str) -> str:
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()


@st.cache_data(ttl=300)
def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    cat = pd.read_csv(DATA / "catalogo.csv", dtype=str, keep_default_na=False)
    arb = pd.read_csv(DATA / "arbol.csv", dtype=str, keep_default_na=False)
    arb["orden"] = arb["orden"].astype(int)
    arb["nivel"] = arb["nivel"].astype(int)
    arb = arb.sort_values("orden").merge(cat, on="codigo", how="left")
    faltan = arb.loc[arb["documento"].isna(), "codigo"].unique()
    if len(faltan):
        st.warning("Códigos del árbol sin fila en el catálogo: " + ", ".join(faltan))
    return cat, arb.fillna("")


cat, arb = cargar()
tiene_enlace = cat.set_index("codigo")["enlace"].str.strip().ne("").to_dict()
apariciones = arb[arb["numeral"] != "Base"][["codigo", "norma", "numeral"]].drop_duplicates().to_dict("records")

# ---------- Barra lateral: filtros ----------
with st.sidebar:
    st.header("Filtros")
    q = st.text_input("Buscar documento", placeholder="Código o nombre: P-028, homogeneidad, 3-406", key="q").strip()
    if hasattr(st, "pills"):
        tipos_sel = st.pills("Tipo de documento", TIPOS, selection_mode="multi", default=TIPOS, key="tipos")
    else:
        tipos_sel = st.multiselect("Tipo de documento", TIPOS, default=TIPOS, key="tipos")
    tipos_sel = list(tipos_sel) or TIPOS  # ninguno marcado = todos
    solo_sin = st.toggle("Solo documentos sin enlace", key="solo_sin")
    st.divider()
    st.caption(
        "La búsqueda resalta los numerales que contienen el documento. Los enlaces se registran una vez "
        "por código en `data/catalogo.csv`: si un documento aparece en varios numerales o en ambas normas, "
        "todos usan el mismo enlace."
    )

filtrando = bool(q) or solo_sin or len(tipos_sel) < len(TIPOS)


def coincide(r) -> bool:
    if r["tipo"] not in tipos_sel:
        return False
    if solo_sin and tiene_enlace.get(r["codigo"], False):
        return False
    if q and _norm(q) not in _norm(f'{r["codigo"]} {r["documento"]}'):
        return False
    return True


def conteo(df: pd.DataFrame) -> tuple[int, int]:
    codigos = df["codigo"].unique()
    return sum(tiene_enlace.get(c, False) for c in codigos), len(codigos)


def incrustar(html: str, alto: int):
    if hasattr(st, "iframe"):
        st.iframe(html, height=alto)
    else:  # versiones anteriores de Streamlit
        import streamlit.components.v1 as components
        components.html(html, height=alto, scrolling=True)


# ---------- Encabezado ----------
logo_b64 = base64.b64encode(LOGO.read_bytes()).decode() if LOGO.exists() else ""
st.markdown(
    f"""<div class="ica-band">
      {f'<img src="data:image/png;base64,{logo_b64}" alt="Instituto Colombiano Agropecuario">' if logo_b64 else ""}
      <div class="sep"></div>
      <div class="txt">
        <div class="eb">Subgerencia de Análisis y Diagnóstico · LANIA · Área IIAD</div>
        <h1>Árbol documental del sistema de gestión</h1>
        <p class="sub">Documentos que evidencian cada requisito de ISO 17034 e ISO/IEC 17043,
        según el Manual Técnico GSA-MC-SAD-003 V3.</p>
      </div></div>""",
    unsafe_allow_html=True,
)
m = st.columns(3)
for col, norma in zip(m, NORMAS):
    a, n = conteo(arb[arb["norma"] == norma])
    col.metric(f"{norma} · documentos con enlace", f"{a} / {n}")
a, n = sum(tiene_enlace.values()), len(cat)
m[2].metric("Catálogo completo", f"{a} / {n}")

tabs = st.tabs(["ISO 17034", "ISO/IEC 17043", "Catálogo", "Árbol completo", "Correcciones al Visio"])

for tab, norma in zip(tabs[:2], NORMAS):
    with tab:
        st.caption(NOMBRE_NORMA[norma] + ". Cada fila es un capítulo y cada casilla un numeral: "
                   "seleccione una casilla para ver sus documentos.")
        sub = arb[arb["norma"] == norma]
        datos = datos_tabla(sub, TRONCO7[norma], coincide, filtrando, apariciones, norma, tiene_enlace)
        incrustar(pagina_tabla(datos), 900)

with tabs[2]:
    donde = (
        arb[arb["numeral"] != "Base"]
        .groupby(["codigo", "norma"])["numeral"]
        .apply(lambda s: ", ".join(dict.fromkeys(s)))
        .unstack(fill_value="")
        .reindex(columns=NORMAS, fill_value="")
    )
    tabla = cat.merge(donde, left_on="codigo", right_index=True, how="left").fillna("")
    tabla = tabla[tabla.apply(coincide, axis=1)]
    tabla["enlace"] = tabla["enlace"].where(tabla["enlace"].str.lower().str.startswith("http"), None)
    st.dataframe(
        tabla[["tipo", "codigo", "documento", "version", *NORMAS, "enlace", "nota"]],
        hide_index=True,
        width="stretch",
        column_config={
            "tipo": "Tipo",
            "codigo": "Código",
            "documento": st.column_config.TextColumn("Documento", width="large"),
            "version": "Versión",
            "enlace": st.column_config.LinkColumn("Enlace", display_text="Abrir ↗"),
            "nota": "Nota",
        },
    )
    st.download_button(
        "Descargar catálogo (CSV)",
        tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name="catalogo_arbol_documental_IIAD.csv",
        mime="text/csv",
    )

with tabs[3]:
    norma = st.radio("Norma", NORMAS, horizontal=True, key="norma_arbol", label_visibility="collapsed")
    st.caption("Vista general en forma de árbol: tronco = capítulos, ramas = numerales, hojas = documentos. "
               "Use los botones 3–8 para ir a cada capítulo.")
    sub = arb[arb["norma"] == norma]

    def donde(codigo, numeral):
        return "; ".join(f'{a["norma"]} {a["numeral"]}' for a in apariciones
                         if a["codigo"] == codigo and not (a["norma"] == norma and a["numeral"] == numeral))

    def estado_de(r) -> str:
        return "n" if not filtrando else ("hit" if coincide(r) else "dim")

    incrustar(pagina_html(construir_svg(sub, norma, donde, estado_de, TRONCO7[norma]), enfocar=bool(q)), 880)

with tabs[4]:
    st.write("Diferencias entre este mapa y los diagramas Visio originales:")
    st.markdown("\n".join(f"{i}. {c}" for i, c in enumerate(CORRECCIONES, 1)))

st.divider()
st.caption(
    "Versiones tomadas de los documentos vigentes (septiembre 2026). Para agregar o cambiar un enlace, "
    "edite `data/catalogo.csv` en el repositorio; la app se actualiza con el commit."
)
