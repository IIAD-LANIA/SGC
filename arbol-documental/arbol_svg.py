"""Dibujo del árbol documental en SVG.

Tronco: capítulos de la norma (3 abajo, junto a las raíces; 8 arriba).
Ramas: subnumerales, alternados a izquierda y derecha del tronco.
Hojas: documentos del sistema de gestión asociados a cada subnumeral
(los documentos que dependen de otro cuelgan con sangría bajo su padre).
Raíces: los manuales GSA-MC-SAD-003 y GSA-MC-SAD-001.
"""
from html import escape
import json

# Paleta institucional
VERDE = "#0b5e36"
VERDE_OSC = "#07432a"
AMARILLO = "#f2b705"
TIPO_COLOR = {
    "Manual": "#1f4e79",
    "Procedimiento": "#3a4047",
    "Instructivo": "#5a6773",
    "Guía o matriz": "#15706f",
    "Instructivo operativo": "#8a6428",
    "Forma (registro)": "#6b4c9d",
    "Otro": "#6b7470",
}

BOX_W, BOX_H = 190, 52          # subnumeral (rama)
GAP_TRUNK = 70                  # del tronco a la caja del subnumeral
LEAF_OFF = 44                   # de la caja a la primera hoja
INDENT = 24                     # sangría por nivel de dependencia
LEAF_W, LEAF_H, LEAF_GAP = 280, 40, 7
BLOCK_GAP = 26
CH_W, CH_H = 290, 58            # capítulo (nodo del tronco)
ROOT_W, ROOT_H = 230, 40


def _cut(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _wrap(s: str, n: int, lines: int = 2) -> list[str]:
    words, out, cur = str(s).split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= n:
            cur = f"{cur} {w}".strip()
        else:
            out.append(cur)
            cur = w
    out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = _cut(out[-1] + " …", n)
    return out


def _doc_path(x, y, w, h):
    """Forma de documento de Visio: rectángulo con borde inferior ondulado."""
    b = y + h - 5
    return (f"M{x:.1f},{y:.1f} H{x + w:.1f} V{b:.1f} "
            f"c{-w / 6:.1f},7 {-w / 3:.1f},7 {-w / 2:.1f},0 "
            f"c{-w / 6:.1f},-7 {-w / 3:.1f},-7 {-w / 2:.1f},0 Z")


def _tip(r, where: str) -> str:
    partes = [f"<b>{escape(r['codigo'])}</b>", escape(r["documento"])]
    meta = " · ".join(x for x in [escape(r["tipo"]), escape(r["version"])] if x)
    partes.append(f"<span class='m'>{meta}</span>")
    if where:
        partes.append(f"<span class='m'>También en: {escape(where)}</span>")
    if r["observacion"]:
        partes.append(f"<span class='w'>Corregido frente al Visio</span>")
    url = r["enlace"].strip()
    if url and not url.lower().startswith("http"):
        partes.append(f"<span class='m'>Ruta: {escape(url)}</span>")
    elif not url:
        partes.append("<span class='m'>Sin enlace registrado</span>")
    return "<br>".join(partes)


def _leaf(r, x, y, estado, where):
    """estado: 'n' normal, 'hit' coincide con la búsqueda, 'dim' atenuada."""
    col = TIPO_COLOR.get(r["tipo"], TIPO_COLOR["Otro"])
    url = r["enlace"].strip()
    web = url.lower().startswith(("http://", "https://"))
    cls = f"leaf {estado}" + ("" if url else " nolink")
    tip = escape(_tip(r, where), quote=True)
    g = [f'<g class="{cls}" data-tip="{tip}">',
         f'<path class="card" d="{_doc_path(x, y, LEAF_W, LEAF_H)}"/>',
         f'<rect x="{x:.1f}" y="{y:.1f}" width="6" height="{LEAF_H - 5}" fill="{col}"/>',
         f'<text class="lc" x="{x + 13:.1f}" y="{y + 15:.1f}">{escape(_cut(r["codigo"], 30))}'
         + (f'<tspan class="lv"> {escape(r["version"])}</tspan>' if r["version"] else "")
         + (f'<tspan class="lw"> ✎</tspan>' if r["observacion"] else "") + "</text>",
         f'<text class="lt" x="{x + 13:.1f}" y="{y + 29:.1f}">{escape(_cut(r["documento"], 43))}</text>']
    cx, cy = x + LEAF_W - 13, y + 13
    if url:
        g.append(f'<circle class="dot on" cx="{cx:.1f}" cy="{cy:.1f}" r="7"/>'
                 f'<path class="arrow" d="M{cx - 3:.1f},{cy + 3:.1f} L{cx + 3:.1f},{cy - 3:.1f} M{cx - 1:.1f},{cy - 3:.1f} H{cx + 3:.1f} V{cy + 1:.1f}"/>')
    else:
        g.append(f'<circle class="dot off" cx="{cx:.1f}" cy="{cy:.1f}" r="6"/>')
    g.append("</g>")
    body = "".join(g)
    if web:
        return f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">{body}</a>'
    return body


def construir_svg(sub, norma_corta, donde, estado_de, tronco7):
    """sub: DataFrame de arbol+catalogo para una norma, ordenado por 'orden'.
    donde(codigo, numeral) -> texto con las otras apariciones.
    estado_de(fila) -> 'n' | 'hit' | 'dim'.
    """
    capitulos = []  # [(clave, titulo, [(numeral, requisito, filas)])]
    raices = []
    for cap, dcap in sub.groupby("capitulo", sort=False):
        if cap.startswith("0"):
            raices = dcap.to_dict("records")
            continue
        nums = [(n, req, d.to_dict("records")) for (n, req), d in dcap.groupby(["numeral", "requisito"], sort=False)]
        clave, titulo = cap.split(" · ", 1)
        if clave == "7":
            titulo = tronco7
        capitulos.append((clave, titulo, nums))

    out, y = [], 0.0
    x_min = -(GAP_TRUNK + BOX_W + LEAF_OFF + 2 * INDENT + LEAF_W) - 20
    x_max = -x_min
    trunk_top = None

    for clave, titulo, nums in reversed(capitulos):
        # reparto equilibrado de ramas a cada lado, en orden de numeral
        lados = {"izq": [], "der": []}
        alto = {"izq": 0.0, "der": 0.0}
        for n, req, filas in nums:
            h = max(BOX_H, len(filas) * LEAF_H + (len(filas) - 1) * LEAF_GAP)
            lado = "izq" if alto["izq"] <= alto["der"] else "der"
            lados[lado].append((n, req, filas, h))
            alto[lado] += h + BLOCK_GAP
        H = max(alto.values()) - BLOCK_GAP
        top = y + 40  # espacio para la etiqueta del capítulo
        if trunk_top is None:
            trunk_top = top - 20
        for lado, bloques in lados.items():
            s = -1 if lado == "izq" else 1
            yy = top + (H - (alto[lado] - BLOCK_GAP))  # ramas pegadas al nodo del capítulo
            for n, req, filas, h in reversed(bloques):  # numeral más alto arriba
                estados = [estado_de(r) for r in filas]
                rama_dim = all(e == "dim" for e in estados)
                by = yy + (h - BOX_H) / 2
                bcy = by + BOX_H / 2
                inner = GAP_TRUNK
                outer = GAP_TRUNK + BOX_W
                bx = inner if s > 0 else -outer
                cls = "branch dim" if rama_dim else "branch"
                out.append(f'<g class="{cls}">')
                out.append(f'<path class="limb" d="M0,{bcy:.1f} H{s * inner:.1f}"/>')
                out.append(f'<rect class="nbox" x="{bx:.1f}" y="{by:.1f}" width="{BOX_W}" height="{BOX_H}" rx="5"/>')
                tx = bx + 12
                out.append(f'<text class="nn" x="{tx:.1f}" y="{by + 21:.1f}">{escape(n)}</text>')
                for i, ln in enumerate(_wrap(req, 27, 2)):
                    out.append(f'<text class="nt" x="{tx:.1f}" y="{by + 35 + i * 12:.1f}">{escape(ln)}</text>')
                # hojas
                pos = []
                ly = yy
                for r in filas:
                    off = outer + LEAF_OFF + (r["nivel"] - 1) * INDENT
                    lx = off if s > 0 else -off - LEAF_W
                    pos.append((r, lx, ly))
                    ly += LEAF_H + LEAF_GAP
                # conectores: caja → hojas de nivel 1
                spine = s * (outer + LEAF_OFF / 2)
                lvl1 = [p for p in pos if p[0]["nivel"] == 1]
                ys = [bcy] + [p[2] + LEAF_H / 2 - 2 for p in lvl1]
                out.append(f'<path class="twig" d="M{s * outer:.1f},{bcy:.1f} H{spine:.1f} M{spine:.1f},{min(ys):.1f} V{max(ys):.1f}"/>')
                for r, lx, ly_ in lvl1:
                    edge = lx if s > 0 else lx + LEAF_W
                    out.append(f'<path class="twig" d="M{spine:.1f},{ly_ + LEAF_H / 2 - 2:.1f} H{edge:.1f}"/>')
                # conectores: documento padre → documentos dependientes
                for i, (r, lx, ly_) in enumerate(pos):
                    if r["nivel"] == 1:
                        continue
                    for j in range(i - 1, -1, -1):
                        pr, plx, ply = pos[j]
                        if pr["nivel"] == r["nivel"] - 1:
                            break
                    px = (plx + INDENT / 2) if s > 0 else (plx + LEAF_W - INDENT / 2)
                    edge = lx if s > 0 else lx + LEAF_W
                    out.append(f'<path class="twig" d="M{px:.1f},{ply + LEAF_H - 4:.1f} V{ly_ + LEAF_H / 2 - 2:.1f} H{edge:.1f}"/>')
                for (r, lx, ly_), e in zip(pos, estados):
                    out.append(_leaf(r, lx, ly_, e, donde(r["codigo"], n)))
                out.append("</g>")
                yy += h + BLOCK_GAP
        # nodo del capítulo sobre el tronco
        cy = top + H + 30
        out.append(f'<g class="chapter" data-ch="{escape(clave)}" data-zoom="{top - 30:.1f},{cy + CH_H + 10:.1f}">'
                   f'<rect x="{-CH_W / 2}" y="{cy:.1f}" width="{CH_W}" height="{CH_H}" rx="6"/>'
                   f'<text class="cn" x="{-CH_W / 2 + 16}" y="{cy + 38:.1f}">{escape(clave)}</text>')
        for i, ln in enumerate(_wrap(titulo, 28, 2)):
            out.append(f'<text class="ct" x="{-CH_W / 2 + 52}" y="{cy + 25 + i * 16:.1f}">{escape(ln)}</text>')
        out.append("</g>")
        y = cy + CH_H + 50

    # raíces: manuales
    ry = y
    for r in raices:
        url = r["enlace"].strip()
        tip = escape(_tip(r, ""), quote=True)
        body = (f'<g class="root{"" if url else " nolink"}" data-tip="{tip}">'
                f'<rect x="{-ROOT_W / 2}" y="{ry:.1f}" width="{ROOT_W}" height="{ROOT_H}" rx="{ROOT_H / 2}"/>'
                f'<text x="0" y="{ry + 25:.1f}" text-anchor="middle">{escape(r["codigo"])} {escape(r["version"])}</text></g>')
        if url.lower().startswith("http"):
            body = f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener">{body}</a>'
        out.append(body)
        ry += ROOT_H + 12
    trunk = f'<path class="trunk" d="M0,{trunk_top:.1f} V{ry - 12 - ROOT_H / 2:.1f}"/>'
    alto_total = ry + 150            # margen inferior para la leyenda
    vb = (x_min, trunk_top - 90, x_max - x_min, alto_total - trunk_top + 90)
    svg = (f'<svg id="tree" xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.0f} {vb[1]:.0f} {vb[2]:.0f} {vb[3]:.0f}" '
           f'data-full="{vb[0]:.0f} {vb[1]:.0f} {vb[2]:.0f} {vb[3]:.0f}" role="img" aria-label="Árbol documental {escape(norma_corta)}">'
           + trunk + "".join(out) + "</svg>")
    return svg


PLANTILLA = r"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@500;600&family=Source+Sans+3:wght@400;600;700&display=swap">
<style>
  html,body{margin:0;height:100%;background:#ffffff;font-family:"Source Sans 3","Segoe UI",Roboto,Arial,sans-serif}
  #wrap{position:relative;height:100%;overflow:hidden;background:
      radial-gradient(circle at 1px 1px,#e3e9e4 1px,transparent 0) 0 0/22px 22px, #fbfcfb;
      border:1px solid #d5ddd7;border-radius:8px;cursor:grab;touch-action:none}
  #wrap.drag{cursor:grabbing}
  svg{width:100%;height:100%;display:block;user-select:none}
  .trunk{stroke:__VERDE_OSC__;stroke-width:12;stroke-linecap:round;fill:none}
  .limb{stroke:__VERDE__;stroke-width:4;fill:none}
  .twig{stroke:#8fa597;stroke-width:1.4;fill:none}
  .nbox{fill:__AMARILLO__;stroke:#c99700;stroke-width:1}
  .nn{font:700 16px "Barlow Condensed","Arial Narrow",Arial,sans-serif;fill:#2a2100}
  .nt{font:600 10.5px "Source Sans 3",Arial,sans-serif;fill:#3b3100}
  .chapter rect{fill:__VERDE__;stroke:__VERDE_OSC__;stroke-width:2}
  .chapter{cursor:zoom-in}
  .cn{font:700 34px "Barlow Condensed","Arial Narrow",Arial,sans-serif;fill:__AMARILLO__}
  .ct{font:700 14px "Source Sans 3",Arial,sans-serif;fill:#ffffff}
  .leaf .card{fill:#ffffff;stroke:#b8c4bc;stroke-width:1}
  .leaf:hover .card{stroke:__VERDE__;stroke-width:2}
  .leaf.nolink .card{stroke-dasharray:4 3}
  .lc{font:600 11px "IBM Plex Mono",Consolas,monospace;fill:#1c231f}
  .lv{font:500 10px "Source Sans 3",Arial,sans-serif;fill:#6a756e}
  .lw{fill:#b26b00}
  .lt{font:400 11px "Source Sans 3",Arial,sans-serif;fill:#3f4a44}
  .dot.on{fill:__VERDE__}.dot.off{fill:none;stroke:#b8c4bc;stroke-width:1.4}
  .arrow{stroke:#fff;stroke-width:1.6;fill:none;stroke-linecap:round}
  a .leaf{cursor:pointer}
  .leaf.hit .card{stroke:#d18f00;stroke-width:3;fill:#fff8e1}
  .leaf.dim,.branch.dim .nbox,.branch.dim text,.branch.dim .limb{opacity:.16}
  .root rect{fill:#1f4e79}.root text{font:700 14px "IBM Plex Mono",Consolas,monospace;fill:#fff}
  a .root{cursor:pointer}
  #tools{position:absolute;right:10px;top:10px;display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;
         background:rgba(255,255,255,.92);border:1px solid #d5ddd7;border-radius:8px;padding:5px 6px;max-width:calc(100% - 20px)}
  #tools button{border:1px solid #c7d1ca;background:#fff;border-radius:6px;min-width:34px;height:32px;font:600 14px Arial;color:#1c231f;cursor:pointer;padding:0 10px}
  #tools button:hover{border-color:__VERDE__;color:__VERDE__}
  #tools .lab{font:12px "Source Sans 3",Arial;color:#6a756e;align-self:center;margin-right:2px}
  #tools button.ch{background:__VERDE__;color:#fff;border-color:__VERDE__;font-family:"Barlow Condensed","Arial Narrow",Arial;font-size:16px;min-width:30px;padding:0 6px}
  #tools button.ch:hover{background:__VERDE_OSC__;color:__AMARILLO__}
  #legend{position:absolute;left:10px;bottom:10px;background:rgba(255,255,255,.94);border:1px solid #d5ddd7;border-radius:6px;padding:7px 10px;font:12px "Source Sans 3",Arial;color:#3f4a44;display:flex;flex-wrap:wrap;gap:6px 12px;max-width:calc(100% - 40px)}
  #legend span{display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
  #legend i{width:10px;height:12px;display:inline-block;border-radius:2px}
  #hint{position:absolute;left:10px;top:10px;max-width:calc(100% - 520px);font:12px "Source Sans 3",Arial;color:#6a756e;background:rgba(255,255,255,.9);padding:3px 8px;border-radius:5px}
  #tip{position:absolute;pointer-events:none;background:#16231c;color:#fff;font:13px/1.35 "Source Sans 3",Arial;padding:8px 10px;border-radius:6px;max-width:330px;box-shadow:0 6px 18px rgba(0,0,0,.25);display:none;z-index:5}
  #tip .m{color:#bfd3c6;font-size:12px}#tip .w{color:#ffd166;font-size:12px}
</style>
<div id="wrap">
  __SVG__
  <div id="tools"><span class="lab">Ir a</span>__CHAPTERS__<button id="zin" title="Acercar">+</button><button id="zout" title="Alejar">−</button><button id="fit" title="Ver todo el árbol">Ver todo</button></div>
  <div id="legend">__LEGEND__</div>
  <div id="tip"></div>
</div>
<script>
(function(){
  const svg=document.getElementById('tree'), wrap=document.getElementById('wrap'), tip=document.getElementById('tip');
  const full=svg.dataset.full.split(' ').map(Number);
  let vb=full.slice();
  const set=()=>svg.setAttribute('viewBox',vb.join(' '));
  const aspect=()=>wrap.clientWidth/wrap.clientHeight;
  function fitBox(x,y,w,h){ const a=aspect(); if(w/h>a){const nh=w/a; y-= (nh-h)/2; h=nh;} else {const nw=h*a; x-=(nw-w)/2; w=nw;} vb=[x,y,w,h]; set(); }
  function fitAll(){ fitBox(...full); }
  function zoom(f,cx,cy){ if(cx===undefined){cx=vb[0]+vb[2]/2;cy=vb[1]+vb[3]/2;}
    const nw=Math.min(Math.max(vb[2]*f, 250), full[2]*3); const k=nw/vb[2];
    vb=[cx-(cx-vb[0])*k, cy-(cy-vb[1])*k, vb[2]*k, vb[3]*k]; set(); }
  function pt(e){ const r=svg.getBoundingClientRect(); return [vb[0]+(e.clientX-r.left)/r.width*vb[2], vb[1]+(e.clientY-r.top)/r.height*vb[3]]; }
  wrap.addEventListener('wheel',e=>{e.preventDefault(); const [x,y]=pt(e); zoom(e.deltaY>0?1.15:1/1.15,x,y);},{passive:false});
  let drag=null, moved=false;
  wrap.addEventListener('pointerdown',e=>{ if(e.target.closest('#tools')) return; drag=[e.clientX,e.clientY,vb[0],vb[1]]; moved=false; });
  window.addEventListener('pointermove',e=>{
    if(drag){ const r=svg.getBoundingClientRect(); const dx=e.clientX-drag[0], dy=e.clientY-drag[1];
      if(Math.abs(dx)+Math.abs(dy)>4){ moved=true; wrap.classList.add('drag'); }
      if(moved){ vb[0]=drag[2]-dx/r.width*vb[2]; vb[1]=drag[3]-dy/r.height*vb[3]; set(); tip.style.display='none'; } }
  });
  window.addEventListener('pointerup',()=>{ drag=null; wrap.classList.remove('drag'); });
  svg.addEventListener('click',e=>{ if(moved){ e.preventDefault(); e.stopPropagation(); moved=false; return; }
    const ch=e.target.closest('.chapter'); if(ch){ const [a,b]=ch.dataset.zoom.split(',').map(Number); fitBox(full[0],a,full[2],b-a); } },true);
  document.getElementById('zin').onclick=()=>zoom(1/1.4);
  document.getElementById('zout').onclick=()=>zoom(1.4);
  document.getElementById('fit').onclick=fitAll;
  document.querySelectorAll('#tools .ch').forEach(bt=>bt.onclick=()=>{ const g=svg.querySelector('.chapter[data-ch="'+bt.dataset.ch+'"]'); if(!g) return; const [a,b]=g.dataset.zoom.split(',').map(Number); fitBox(full[0],a,full[2],b-a); });
  svg.addEventListener('mousemove',e=>{
    const g=e.target.closest('[data-tip]'); if(!g||drag&&moved){ tip.style.display='none'; return; }
    tip.innerHTML=g.dataset.tip; tip.style.display='block';
    const r=wrap.getBoundingClientRect(); let x=e.clientX-r.left+14, y=e.clientY-r.top+14;
    if(x+tip.offsetWidth>r.width-8) x=e.clientX-r.left-tip.offsetWidth-14;
    if(y+tip.offsetHeight>r.height-8) y=e.clientY-r.top-tip.offsetHeight-14;
    tip.style.left=x+'px'; tip.style.top=y+'px';
  });
  svg.addEventListener('mouseleave',()=>tip.style.display='none');
  function initial(){
    if(!wrap.clientWidth||!wrap.clientHeight) return;   // pestaña oculta: se ajusta al mostrarse
    const hits=[...svg.querySelectorAll('.leaf.hit')];
    if(hits.length && __FOCUS__){
      let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity;
      hits.forEach(h=>{const b=h.getBBox(); x0=Math.min(x0,b.x); y0=Math.min(y0,b.y); x1=Math.max(x1,b.x+b.width); y1=Math.max(y1,b.y+b.height);});
      fitBox(Math.min(x0,-200)-120, y0-160, Math.max(x1,200)-Math.min(x0,-200)+240, y1-y0+320);
    } else fitAll();
  }
  initial();
  let touched=false; wrap.addEventListener('pointerdown',()=>touched=true); wrap.addEventListener('wheel',()=>touched=true);
  window.addEventListener('resize',()=>{ if(!touched) initial(); });
})();
</script>
"""


def pagina_html(svg: str, enfocar: bool, capitulos=("3", "4", "5", "6", "7", "8")) -> str:
    leyenda = "".join(f'<span><i style="background:{c}"></i>{escape(t)}</span>' for t, c in TIPO_COLOR.items())
    leyenda += ('<span><svg width="14" height="14"><circle cx="7" cy="7" r="6" fill="%s"/></svg>con enlace</span>'
                '<span><svg width="14" height="14"><circle cx="7" cy="7" r="5.5" fill="none" stroke="#b8c4bc" stroke-width="1.4"/></svg>sin enlace</span>'
                '<span style="color:#b26b00">✎ corregido frente al Visio</span>'
                '<span style="color:#6a756e">· Arrastre para mover · rueda para acercar · clic en un capítulo o documento</span>') % VERDE
    botones = "".join(f'<button class="ch" data-ch="{c}" title="Capítulo {c}">{c}</button>' for c in capitulos)
    return (PLANTILLA.replace("__SVG__", svg).replace("__LEGEND__", leyenda).replace("__CHAPTERS__", botones)
            .replace("__VERDE_OSC__", VERDE_OSC).replace("__VERDE__", VERDE).replace("__AMARILLO__", AMARILLO)
            .replace("__FOCUS__", json.dumps(bool(enfocar))))
