"""Árbol documental IIAD — LANIA · ICA

Guía de consulta de los documentos del sistema de gestión que evidencian cada
requisito de ISO 17034:2016 e ISO/IEC 17043:2023 (numerales según
GSA-MC-SAD-003 V3).

Datos:
  data/arbol.csv     una fila por aparición de un documento en un numeral
  data/catalogo.csv  una fila por documento; aquí se registra el enlace

Para actualizar un enlace se edita data/catalogo.csv en GitHub; la app se
vuelve a desplegar sola con el nuevo commit.
"""
from html import escape
from pathlib import Path
import unicodedata

import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / "data"

TIPOS = {
    "Manual": ("MC", "#2d4b72"),
    "Procedimiento": ("P", "#3a4047"),
    "Instructivo": ("I", "#56636f"),
    "Guía o matriz": ("G", "#1b6c70"),
    "Instructivo operativo": ("IO", "#80602c"),
    "Forma (registro)": ("F", "#6b4c9d"),
    "Otro": ("·", "#6b7470"),
}
NORMAS = ["ISO 17034", "ISO/IEC 17043"]

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
    "**ISO/IEC 17043, tronco del numeral 7.** El Visio lo rotula «Requisitos técnicos de producción MR» "
    "(copiado del árbol de ISO 17034); aquí se presenta como *Requisitos del proceso de EA*.",
    "**Nombres unificados con la versión vigente:** GSA-I-SAD-038, GSA-I-SAD-020, GSA-SAD-P-008 y GSA-SAD-P-025.",
    "**Por revisar, sin aplicar:** GSA-SAD-P-033 V2 cubre el diseño estadístico de EA *y de MR*, pero solo "
    "aparece en el árbol de ISO/IEC 17043. No hay documentos ubicados en el numeral 7.1 de ISO 17034.",
]

st.set_page_config(page_title="Árbol documental IIAD", page_icon="🌳", layout="wide")

st.markdown(
    """
    <style>
      .arb-row{display:flex;align-items:baseline;gap:.5rem;padding:.2rem 0;flex-wrap:wrap}
      .arb-badge{display:inline-block;min-width:1.7rem;text-align:center;border-radius:4px;color:#fff;
                 font:700 .68rem ui-monospace,Menlo,Consolas,monospace;padding:.12rem .25rem;align-self:center}
      .arb-code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85rem;font-weight:600;white-space:nowrap}
      .arb-title{flex:1 1 16rem;min-width:0}
      .arb-ver{font-size:.78rem;opacity:.65;white-space:nowrap}
      .arb-fix{font-size:.75rem;font-weight:700;color:#b26b00;white-space:nowrap}
      .arb-open{font-size:.8rem;font-weight:600;white-space:nowrap;text-decoration:none;
                border:1px solid currentColor;border-radius:99px;padding:.05rem .55rem}
      .arb-none{font-size:.78rem;opacity:.5;white-space:nowrap}
      .arb-path{font-size:.75rem;word-break:break-all}
      .arb-kids{border-left:1px solid rgba(128,128,128,.45);margin-left:.85rem;padding-left:.7rem}
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

# ---------- Barra lateral: filtros ----------
with st.sidebar:
    st.header("Filtros")
    q = st.text_input("Buscar", placeholder="Código o nombre: P-028, homogeneidad, 3-406", key="q").strip()
    tipos_sel = st.multiselect("Tipo de documento", list(TIPOS), default=list(TIPOS), key="tipos")
    solo_sin = st.toggle("Solo documentos sin enlace", key="solo_sin")
    st.divider()
    st.caption(
        "Los enlaces se registran una vez por código en `data/catalogo.csv`: si un documento aparece en "
        "varios numerales o en ambas normas, todos usan el mismo enlace."
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


def enlace_html(url: str) -> str:
    url = url.strip()
    if not url:
        return '<span class="arb-none">sin enlace</span>'
    if url.lower().startswith(("http://", "https://")):
        return f'<a class="arb-open" href="{escape(url)}" target="_blank" rel="noopener">Abrir ↗</a>'
    return f'<code class="arb-path">{escape(url)}</code>'


def fila_html(r, atenuar: bool) -> str:
    abbr, color = TIPOS.get(r["tipo"], TIPOS["Otro"])
    estilo = ' style="opacity:.45"' if atenuar else ""
    fix = '<span class="arb-fix" title="Corregido frente al Visio">corregido</span>' if r["observacion"] else ""
    ver = f'<span class="arb-ver">{escape(r["version"])}</span>' if r["version"] else ""
    return (
        f'<div class="arb-row"{estilo}>'
        f'<span class="arb-badge" style="background:{color}" title="{escape(r["tipo"])}">{abbr}</span>'
        f'<span class="arb-code">{escape(r["codigo"])}</span>'
        f'<span class="arb-title">{escape(r["documento"])}</span>{ver}{fix}{enlace_html(r["enlace"])}</div>'
    )


def render_bloque(filas: list) -> str:
    """Convierte filas planas (con nivel) en HTML anidado, filtrando ramas sin coincidencias."""
    n = len(filas)
    visibles = [False] * n
    for i in range(n - 1, -1, -1):  # una fila se ve si coincide o si algún descendiente se ve
        vis = coincide(filas[i])
        j = i + 1
        while j < n and filas[j]["nivel"] > filas[i]["nivel"]:
            vis = vis or (visibles[j] and filas[j]["nivel"] == filas[i]["nivel"] + 1)
            j += 1
        visibles[i] = vis or not filtrando
    html, pila = [], []
    for i, r in enumerate(filas):
        if not visibles[i]:
            continue
        while pila and pila[-1] > r["nivel"]:  # cerrar contenedores de niveles más profundos
            html.append("</div>")
            pila.pop()
        if r["nivel"] > 1 and (not pila or pila[-1] < r["nivel"]):
            html.append('<div class="arb-kids">')
            pila.append(r["nivel"])
        html.append(fila_html(r, filtrando and not coincide(r)))
    html.extend("</div>" for _ in pila)
    return "".join(html)


def conteo(df: pd.DataFrame) -> tuple[int, int]:
    codigos = df["codigo"].unique()
    return sum(tiene_enlace.get(c, False) for c in codigos), len(codigos)


# ---------- Encabezado ----------
st.caption("LANIA · Área IIAD · Subgerencia de Análisis y Diagnóstico")
st.title("Árbol documental IIAD")
st.write(
    "Documentos del sistema de gestión que evidencian cada requisito de ISO 17034 e ISO/IEC 17043, "
    "ordenados según el Manual Técnico GSA-MC-SAD-003 V3."
)
m = st.columns(3)
for col, norma in zip(m, NORMAS):
    a, n = conteo(arb[arb["norma"] == norma])
    col.metric(f"{norma} · documentos con enlace", f"{a} / {n}")
a, n = sum(tiene_enlace.values()), len(cat)
m[2].metric("Catálogo completo", f"{a} / {n}")

tabs = st.tabs(NORMAS + ["Catálogo", "Correcciones al Visio"])

for tab, norma in zip(tabs[:2], NORMAS):
    with tab:
        sub = arb[arb["norma"] == norma]
        algo = False
        for capitulo, dcap in sub.groupby("capitulo", sort=False):
            numerales = []
            for (numeral, req), dnum in dcap.groupby(["numeral", "requisito"], sort=False):
                cuerpo = render_bloque(dnum.to_dict("records"))
                if cuerpo:
                    numerales.append((numeral, req, dnum, cuerpo))
            if not numerales:
                continue
            algo = True
            a, n = conteo(dcap)
            st.subheader(capitulo)
            st.caption(f"{a} de {n} documentos con enlace")
            for numeral, req, dnum, cuerpo in numerales:
                a, n = conteo(dnum)
                etiqueta = f"**{numeral}** · {req}" if numeral != "Base" else f"**{req}**"
                with st.expander(f"{etiqueta}   ({a}/{n})", expanded=filtrando or numeral == "Base"):
                    st.markdown(cuerpo, unsafe_allow_html=True)
        if not algo:
            st.info("Ningún documento coincide con la búsqueda o los filtros.")

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
    st.write("Diferencias entre este árbol y los diagramas Visio originales:")
    st.markdown("\n".join(f"{i}. {c}" for i, c in enumerate(CORRECCIONES, 1)))

st.divider()
st.caption(
    "Versiones tomadas de los documentos vigentes (septiembre 2026). Para agregar o cambiar un enlace, "
    "edite `data/catalogo.csv` en el repositorio; la app se actualiza con el commit."
)
