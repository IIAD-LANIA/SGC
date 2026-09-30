"""Paleta institucional ICA tomada de la «Guía para editores web y gestores de
contenido del ICA» (2025), sección Estilo visual: fondo #FFFFFF, títulos
#000000, cuerpo de texto #4B4B4B, tipografía Nunito Sans; verdes, lima y ocre
de las piezas gráficas de la guía y azul de la barra GOV.CO."""

BLANCO = "#FFFFFF"
TITULO = "#000000"
TEXTO = "#4B4B4B"
VERDE = "#329D4A"        # verde institucional (títulos de la guía)
VERDE_OSC = "#33773B"    # verde oscuro (numeración de página de la guía)
LIMA = "#A4CB2F"         # verde lima (franja inferior de la guía)
OCRE = "#BA9437"         # ocre (pie de página de la sede electrónica)
AZUL = "#3366CC"         # azul GOV.CO
GRIS_LINEA = "#D9D9D9"
FUENTE = '"Nunito Sans", Verdana, Arial, sans-serif'
FUENTE_URL = "https://fonts.googleapis.com/css2?family=Nunito+Sans:opsz,wght@6..12,400;6..12,600;6..12,700;6..12,800&display=swap"

# Tipo de documento → (fondo de la etiqueta, color del texto, abreviatura)
TIPO_ESTILO = {
    "Manual": (AZUL, BLANCO, "MC"),
    "Procedimiento": (VERDE_OSC, BLANCO, "P"),
    "Instructivo": (OCRE, BLANCO, "I"),
    "Guía o matriz": (LIMA, "#1F2A05", "G"),
    "Instructivo operativo": ("#7A5E1E", BLANCO, "IO"),
    "Forma (registro)": (TEXTO, BLANCO, "F"),
    "Otro": ("#9A9A9A", BLANCO, "·"),
}

# Capítulo → (color de familia, tinte de fondo)
CAPITULO_ESTILO = {
    "3": (OCRE, "#F7F1E3"),
    "4": (AZUL, "#E8EEF9"),
    "5": (TEXTO, "#F0F0F0"),
    "6": (LIMA, "#F1F7DF"),
    "7": (VERDE, "#E6F3E9"),
    "8": (VERDE_OSC, "#E3EDE5"),
}
