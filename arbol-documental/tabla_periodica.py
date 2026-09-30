"""Vista «tabla periódica» del sistema de gestión.

Cada capítulo de la norma es una fila (una familia, con su color); cada
numeral es una casilla con el número de documentos asociados y cuántos
tienen enlace. Al seleccionar una casilla, el panel de la derecha muestra
los documentos de ese numeral, con su enlace y los otros numerales donde
se usan.
"""
import json

from tema import (AZUL, BLANCO, CAPITULO_ESTILO, FUENTE, FUENTE_URL, GRIS_LINEA, LIMA, OCRE,
                  TEXTO, TIPO_ESTILO, TITULO, VERDE, VERDE_OSC)


def datos_tabla(sub, tronco7, coincide, filtrando, apariciones, norma, tiene_enlace):
    """Arma la estructura que consume la página a partir del DataFrame de una norma."""
    capitulos, base = [], []
    for cap, dcap in sub.groupby("capitulo", sort=False):
        filas = dcap.to_dict("records")
        if cap.startswith("0"):
            base = [_doc(r, coincide, filtrando, apariciones, norma, "") for r in filas]
            continue
        clave, titulo = cap.split(" · ", 1)
        if clave == "7":
            titulo = tronco7
        nums = []
        for (n, req), d in dcap.groupby(["numeral", "requisito"], sort=False):
            docs = [_doc(r, coincide, filtrando, apariciones, norma, n) for r in d.to_dict("records")]
            unicos = {x["codigo"] for x in docs}
            nums.append({
                "n": n, "t": req, "docs": docs,
                "total": len(unicos),
                "con": sum(tiene_enlace.get(c, False) for c in unicos),
                "hits": sum(1 for x in docs if x["hit"]),
            })
        color, tinte = CAPITULO_ESTILO.get(clave, (VERDE, "#EEF5EF"))
        capitulos.append({"clave": clave, "titulo": titulo, "color": color, "tinte": tinte, "nums": nums})
    return {"capitulos": capitulos, "base": base, "filtrando": filtrando, "norma": norma}


def _doc(r, coincide, filtrando, apariciones, norma, numeral):
    otras = [f'{a["norma"]} {a["numeral"]}' for a in apariciones
             if a["codigo"] == r["codigo"] and not (a["norma"] == norma and a["numeral"] == numeral)]
    return {
        "codigo": r["codigo"], "documento": r["documento"], "tipo": r["tipo"], "version": r["version"],
        "nivel": int(r["nivel"]), "enlace": r["enlace"].strip(), "nota": r.get("nota", ""),
        "obs": r["observacion"], "otras": otras, "hit": bool(filtrando and coincide(r)),
    }


PLANTILLA = r"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="__FUENTE_URL__">
<style>
  :root{--blanco:__BLANCO__;--titulo:__TITULO__;--texto:__TEXTO__;--verde:__VERDE__;--verde-osc:__VERDE_OSC__;
        --lima:__LIMA__;--ocre:__OCRE__;--azul:__AZUL__;--linea:__GRIS_LINEA__;--suave:#F6F7F6}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--blanco);color:var(--texto);font:15px/1.45 __FUENTE__}
  button{font:inherit;color:inherit}
  :focus-visible{outline:3px solid var(--azul);outline-offset:2px}
  .app{display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,380px);gap:16px;height:100%}
  .tabla{overflow:auto;padding:4px 6px 16px 2px}
  .panel{overflow:auto;border:1px solid var(--linea);border-radius:10px;background:var(--blanco)}
  @media (max-width:760px){ .app{grid-template-columns:1fr;grid-template-rows:auto auto;height:auto}
    .tabla,.panel{overflow:visible} html,body{height:auto} }

  .familias{display:flex;flex-wrap:wrap;gap:6px 14px;margin:2px 0 14px;font-size:13px}
  .familias span{display:inline-flex;align-items:center;gap:6px}
  .familias i{width:14px;height:14px;border-radius:3px;display:inline-block}

  .fila{display:grid;grid-template-columns:84px 1fr;gap:10px;margin-bottom:12px;align-items:start}
  .cap{border-radius:8px;color:var(--blanco);padding:8px 6px;text-align:center;min-height:112px;display:flex;flex-direction:column;justify-content:center}
  .cap b{font-size:34px;line-height:1;font-weight:800}
  .cap span{font-size:10.5px;line-height:1.2;font-weight:700;margin-top:6px;overflow-wrap:anywhere;hyphens:auto}
  .casillas{display:grid;grid-template-columns:repeat(auto-fill,minmax(122px,1fr));gap:8px}
  .casilla{position:relative;text-align:left;border:1px solid var(--linea);border-top:6px solid var(--fam);background:var(--tinte);
           border-radius:6px;padding:7px 9px 22px;min-height:112px;cursor:pointer;transition:transform .12s, box-shadow .12s}
  .casilla:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.12)}
  .casilla.sel{outline:3px solid var(--verde-osc);outline-offset:1px;box-shadow:0 6px 18px rgba(51,119,59,.28)}
  .casilla.dim{opacity:.28}
  .casilla .cnt{position:absolute;right:8px;top:6px;font-size:12px;font-weight:700;color:var(--texto)}
  .casilla .num{display:block;font-size:24px;font-weight:800;color:var(--titulo);line-height:1.05;letter-spacing:-.01em}
  .casilla .req{display:block;font-size:12px;line-height:1.25;margin-top:4px;color:var(--texto);font-weight:600}
  .casilla .cov{position:absolute;left:9px;right:9px;bottom:8px;height:5px;border-radius:3px;background:#E3E3E3;overflow:hidden}
  .casilla .cov i{display:block;height:100%;background:var(--verde)}
  .casilla .hits{position:absolute;right:6px;bottom:15px;background:var(--azul);color:#fff;font-size:11px;font-weight:700;border-radius:99px;padding:0 7px}

  .ph{padding:16px 18px 12px;border-bottom:1px solid var(--linea);border-top:8px solid var(--fam,var(--verde));border-radius:10px 10px 0 0}
  .ph .eb{font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;color:var(--texto)}
  .ph h2{margin:4px 0 2px;color:var(--titulo);font-size:22px;line-height:1.2;font-weight:800}
  .ph .res{font-size:13px}
  .docs{list-style:none;margin:0;padding:8px 12px 14px}
  .docs li{padding:9px 6px;border-bottom:1px solid #EFEFEF}
  .docs li.n2{margin-left:22px;border-left:2px solid var(--linea);padding-left:10px}
  .docs li.n3{margin-left:44px;border-left:2px solid var(--linea);padding-left:10px}
  .docs li.hit{background:#EEF3FC;border-radius:6px}
  .d1{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .badge{display:inline-grid;place-items:center;min-width:26px;height:20px;border-radius:4px;font-size:11px;font-weight:800;padding:0 4px}
  .cod{font-weight:800;color:var(--titulo);font-size:14px}
  .ver{font-size:12px;color:var(--texto);border:1px solid var(--linea);border-radius:99px;padding:0 7px}
  .tit{margin:3px 0 0;color:var(--texto);font-size:14px}
  .d2{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:6px}
  .abrir{display:inline-flex;align-items:center;gap:5px;background:var(--verde-osc);color:#fff;text-decoration:none;font-weight:700;font-size:13px;border-radius:6px;padding:4px 11px}
  .abrir:hover{background:var(--verde)}
  .sin{font-size:12.5px;color:#7A7A7A;border:1px dashed #BDBDBD;border-radius:6px;padding:3px 9px}
  .ruta{font-size:12px;word-break:break-all;background:var(--suave);border-radius:4px;padding:2px 6px}
  .otras{font-size:12px;color:var(--texto)}
  .otras b{font-weight:700}
  .obs{font-size:12.5px;color:#7A5E1E;background:#F7F1E3;border-left:3px solid var(--ocre);padding:4px 8px;margin-top:6px;border-radius:0 4px 4px 0}
  .vacio{padding:18px}
  .vacio h2{margin:0 0 6px;color:var(--titulo);font-size:20px;font-weight:800}
  .vacio p{margin:0 0 12px}
  .tipos{display:grid;gap:6px;margin:10px 0 16px}
  .tipos div{display:flex;align-items:center;gap:8px;font-size:13.5px}
  .resumen{width:100%;border-collapse:collapse;font-size:13.5px}
  .resumen td{padding:5px 4px;border-bottom:1px solid #EFEFEF}
  .resumen td:last-child{text-align:right;font-variant-numeric:tabular-nums;font-weight:700}
  .resumen i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
  h3.sub{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--titulo);margin:16px 0 6px}
</style></head><body>
<div class="app">
  <div class="tabla" id="tabla"></div>
  <aside class="panel" id="panel" aria-live="polite"></aside>
</div>
<script>
const D = __DATA__;
const T = __TIPOS__;
const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const web = u => /^https?:\/\//i.test(u || "");
let sel = null;

function badge(tipo){ const t = T[tipo] || T["Otro"]; return `<span class="badge" style="background:${t[0]};color:${t[1]}" title="${esc(tipo)}">${t[2]}</span>`; }

function tabla(){
  const fam = D.capitulos.map(c => `<span><i style="background:${c.color}"></i>${esc(c.clave)} · ${esc(c.titulo)}</span>`).join("");
  let h = `<div class="familias">${fam}</div>`;
  D.capitulos.forEach((c, ci) => {
    h += `<div class="fila"><div class="cap" style="background:${c.color}"><b>${esc(c.clave)}</b><span>${esc(c.titulo)}</span></div><div class="casillas">`;
    c.nums.forEach((n, ni) => {
      const pct = n.total ? Math.round(100 * n.con / n.total) : 0;
      const dim = D.filtrando && !n.hits ? " dim" : "";
      const s = sel && sel[0] === ci && sel[1] === ni ? " sel" : "";
      h += `<button class="casilla${dim}${s}" style="--fam:${c.color};--tinte:${c.tinte}" data-c="${ci}" data-n="${ni}"
               aria-label="Numeral ${esc(n.n)} ${esc(n.t)}, ${n.total} documentos, ${n.con} con enlace">
        <span class="cnt" title="Documentos asociados">${n.total} doc.</span>
        <span class="num">${esc(n.n)}</span><span class="req">${esc(n.t)}</span>
        ${D.filtrando && n.hits ? `<span class="hits">${n.hits}</span>` : ""}
        <span class="cov" title="${n.con} de ${n.total} con enlace"><i style="width:${pct}%"></i></span></button>`;
    });
    h += `</div></div>`;
  });
  document.getElementById("tabla").innerHTML = h;
}

function docItem(d){
  let link;
  if (d.enlace && web(d.enlace)) link = `<a class="abrir" href="${esc(d.enlace)}" target="_blank" rel="noopener">Abrir documento ↗</a>`;
  else if (d.enlace) link = `<span class="ruta" title="Ruta de red">${esc(d.enlace)}</span>`;
  else link = `<span class="sin">Sin enlace registrado</span>`;
  const otras = d.otras.length ? `<span class="otras"><b>También en:</b> ${esc(d.otras.join(" · "))}</span>` : "";
  return `<li class="n${Math.min(d.nivel,3)}${d.hit ? " hit" : ""}">
    <div class="d1">${badge(d.tipo)}<span class="cod">${esc(d.codigo)}</span>${d.version ? `<span class="ver">${esc(d.version)}</span>` : ""}</div>
    <p class="tit">${esc(d.documento)}</p>
    <div class="d2">${link}${otras}</div>
    ${d.nota ? `<div class="otras">${esc(d.nota)}</div>` : ""}
    ${d.obs ? `<div class="obs">Corregido frente al Visio: ${esc(d.obs)}</div>` : ""}</li>`;
}

function panel(){
  const p = document.getElementById("panel");
  if (!sel){
    const tipos = Object.entries(T).map(([k,v]) => `<div><span class="badge" style="background:${v[0]};color:${v[1]}">${v[2]}</span>${esc(k)}</div>`).join("");
    const res = D.capitulos.map(c => { let a=0,b=0; c.nums.forEach(n=>{a+=n.con;b+=n.total}); return `<tr><td><i style="background:${c.color}"></i>${esc(c.clave)} · ${esc(c.titulo)}</td><td>${c.nums.length} num.</td><td>${a}/${b}</td></tr>`; }).join("");
    p.innerHTML = `<div class="vacio"><h2>Seleccione un numeral</h2>
      <p>Cada casilla es un numeral de ${esc(D.norma)}. El número de la esquina indica cuántos documentos lo evidencian y la barra inferior, cuántos tienen enlace.</p>
      <h3 class="sub">Documentos base</h3><ul class="docs" style="padding:0">${D.base.map(docItem).join("")}</ul>
      <h3 class="sub">Tipos de documento</h3><div class="tipos">${tipos}</div>
      <h3 class="sub">Resumen por capítulo</h3><table class="resumen">${res}</table></div>`;
    return;
  }
  const c = D.capitulos[sel[0]], n = c.nums[sel[1]];
  p.innerHTML = `<div class="ph" style="--fam:${c.color}">
      <div class="eb">${esc(D.norma)} · Capítulo ${esc(c.clave)} · ${esc(c.titulo)}</div>
      <h2>${esc(n.n)} ${esc(n.t)}</h2>
      <div class="res">${n.total} documentos asociados · ${n.con} con enlace</div></div>
    <ul class="docs">${n.docs.map(docItem).join("")}</ul>`;
  p.scrollTop = 0;
}

document.getElementById("tabla").addEventListener("click", e => {
  const b = e.target.closest(".casilla"); if (!b) return;
  const k = [+b.dataset.c, +b.dataset.n];
  sel = sel && sel[0] === k[0] && sel[1] === k[1] ? null : k;
  tabla(); panel();
  if (window.innerWidth <= 760 && sel) document.getElementById("panel").scrollIntoView({behavior:"smooth"});
});

// Con búsqueda activa, se abre el primer numeral con coincidencias
if (D.filtrando){ outer: for (let ci=0; ci<D.capitulos.length; ci++) for (let ni=0; ni<D.capitulos[ci].nums.length; ni++) if (D.capitulos[ci].nums[ni].hits){ sel=[ci,ni]; break outer; } }
tabla(); panel();
</script></body></html>"""


def pagina(datos: dict) -> str:
    reemplazos = {
        "__FUENTE_URL__": FUENTE_URL, "__FUENTE__": FUENTE, "__BLANCO__": BLANCO, "__TITULO__": TITULO,
        "__TEXTO__": TEXTO, "__VERDE_OSC__": VERDE_OSC, "__VERDE__": VERDE, "__LIMA__": LIMA,
        "__OCRE__": OCRE, "__AZUL__": AZUL, "__GRIS_LINEA__": GRIS_LINEA,
        "__TIPOS__": json.dumps(TIPO_ESTILO, ensure_ascii=False),
        "__DATA__": json.dumps(datos, ensure_ascii=False).replace("</", "<\\/"),
    }
    html = PLANTILLA
    for k, v in reemplazos.items():
        html = html.replace(k, v)
    return html
