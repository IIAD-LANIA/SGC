# SGC · Aplicativos del sistema de gestión

Área IIAD · LANIA · Subgerencia de Análisis y Diagnóstico · Instituto Colombiano Agropecuario (ICA)

En este repositorio se almacenan los aplicativos relacionados con la mejora y el desarrollo del sistema de gestión (ISO 17034, ISO/IEC 17043, ISO/IEC 17025). Cada aplicativo vive en su propia carpeta, con su `requirements.txt` y su `README.md`.

| Aplicativo | Carpeta | Archivo principal (Streamlit) | Descripción |
|---|---|---|---|
| Árbol documental IIAD | [`arbol-documental/`](arbol-documental/) | `arbol-documental/app.py` | Documentos del sistema de gestión que evidencian cada requisito de ISO 17034 e ISO/IEC 17043, según GSA-MC-SAD-003 V3. |

## Convenciones

- `.streamlit/config.toml` (raíz) define el tema institucional ICA para todas las apps del repositorio.
- Cada cambio de contenido (enlaces, versiones de documentos) se registra con un commit que identifique el documento afectado, p. ej. `Enlace GSA-SAD-P-028 V5`.
