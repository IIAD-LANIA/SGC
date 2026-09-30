# Árbol documental IIAD

Guía de consulta, para el personal del Área IIAD del LANIA (ICA), de los documentos del sistema de gestión que evidencian cada requisito de **ISO 17034:2016** (producción de MR) e **ISO/IEC 17043:2023** (EA). La numeración sigue el Manual Técnico **GSA-MC-SAD-003 V3**.

## Estructura

```
arbol-documental/      Carpeta de esta app dentro del repositorio SGC
app.py                 Aplicación Streamlit (solo lectura)
arbol_svg.py           Dibujo del árbol: tronco = capítulos, ramas = numerales, hojas = documentos
assets/logo_ica_blanco.png  Logo institucional para el encabezado
data/catalogo.csv      Un renglón por documento: código, nombre, tipo, versión, ENLACE, nota
data/arbol.csv         Un renglón por aparición de un documento en un numeral de cada norma
requirements.txt
```

El enlace se registra **una sola vez por código** en `data/catalogo.csv`. Si un documento aparece en varios numerales o en ambas normas (p. ej. GSA-SAD-P-028 en 7.9, 7.12–7.13 de ISO 17034 y 7.2 de ISO/IEC 17043), todos toman el mismo enlace.

El tema institucional (verde ICA) está en `.streamlit/config.toml`, en la **raíz** del repositorio SGC: Streamlit Community Cloud lo lee desde ahí y aplica a todas las apps del repositorio.

## Vistas

- **Árbol ISO 17034 / Árbol ISO/IEC 17043:** el sistema completo como árbol. Botones 3–8 para ir a cada capítulo, rueda del ratón para acercar, arrastrar para mover. Al pasar el cursor sobre un documento se ve su nombre completo, versión y en qué otros numerales aparece; al hacer clic se abre el enlace. La búsqueda resalta los documentos que coinciden y atenúa el resto.
- **Lista por numeral:** la misma información en listas desplegables.
- **Catálogo:** tabla de los 81 documentos con los numerales donde aparece cada uno, descargable en CSV.
- **Correcciones al Visio:** diferencias entre este árbol y los diagramas originales.

## Actualizar enlaces o documentos

1. En GitHub, abrir `arbol-documental/data/catalogo.csv` y usar **Edit** (lápiz).
2. Pegar la URL en la columna `enlace` del código correspondiente. Se aceptan URL `https://…` (SharePoint, DIAMANTE) o rutas de red, que se muestran como texto para copiar.
3. Hacer **Commit** con un mensaje que identifique el cambio (p. ej. `Enlace GSA-SAD-P-028 V5`). La app se actualiza sola en uno o dos minutos.

El historial de commits deja el registro de quién cambió qué y cuándo.

- **Cambio de versión de un documento:** editar la columna `version` en `catalogo.csv`.
- **Documento nuevo o reubicado en otro numeral:** agregar la fila en `catalogo.csv` (si es nuevo) y en `arbol.csv`. En `arbol.csv`, `orden` define la posición, `nivel` la sangría (1, 2, 3) y `documento_padre` el código del documento del que depende.

## Ejecutar localmente

```bash
cd arbol-documental
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud

1. La carpeta `arbol-documental/` va en la raíz del repositorio `IIAD-LANIA/SGC`.
2. En https://share.streamlit.io: **Create app** → repositorio `IIAD-LANIA/SGC`, rama `main`, archivo principal `arbol-documental/app.py`.
3. En la configuración de la app, **Sharing**: definir quién puede verla (ver consideraciones abajo).

## Consideraciones

- **Visibilidad.** Una app desplegada desde un repositorio público es pública. Para restringirla al personal, use un repositorio privado y limite la visualización a los correos invitados desde *Sharing*. Verifique los límites vigentes del plan gratuito para apps privadas.
- **Contenido.** El árbol solo contiene códigos, nombres y enlaces de documentos controlados. No contiene valores asignados, datos de participantes ni resultados, en coherencia con el numeral 4 (imparcialidad y confidencialidad) de GSA-MC-SAD-003. Los enlaces a SharePoint siguen exigiendo el inicio de sesión institucional para abrir el documento.
- **Política institucional.** Alojar información del SGC en un servicio externo debe validarse con la Oficina de TIC y con la Coordinación del GGCA.
- **Disponibilidad.** Las apps del plan gratuito entran en reposo tras un periodo sin uso; el primer acceso posterior tarda unos segundos en reactivarla.
