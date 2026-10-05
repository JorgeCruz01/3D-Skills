"""Extrae texto y paginas (PNG) de una ficha tecnica en PDF, para archivarla
como referencia de un prop. Se ejecuta con el Python del sistema (necesita
PyMuPDF), no dentro de Blender:

    python pdf_a_referencia.py ficha.pdf carpeta_destino [prefijo] [max_paginas]
"""
import sys

import fitz


def main():
    pdf, destino = sys.argv[1], sys.argv[2]
    prefijo = sys.argv[3] if len(sys.argv) > 3 else "ref_ficha"
    maximo = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    doc = fitz.open(pdf)
    print("paginas", len(doc))
    for i, pagina in enumerate(doc):
        if i >= maximo:
            break
        print("--- pagina", i + 1)
        print(pagina.get_text()[:3500])
        pagina.get_pixmap(dpi=120).save("%s/%s_p%d.png" % (destino, prefijo, i + 1))


if __name__ == "__main__":
    main()
