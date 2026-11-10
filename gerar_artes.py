"""Gera artes de exemplo em PDF com o tamanho real de impressão (escala 1:1)."""
import os, sys
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

ARTES = [
    ("banner_promocao_90x120.pdf", 90, 120, "PROMOÇÃO DE INVERNO", colors.HexColor("#c0392b")),
    ("adesivo_logo_30x30.pdf", 30, 30, "LOGO", colors.HexColor("#2c3e50")),
    ("placa_saida_60x40.pdf", 60, 40, "SAÍDA", colors.HexColor("#27ae60")),
]

def gerar(pasta):
    os.makedirs(pasta, exist_ok=True)
    for nome, l, a, texto, cor in ARTES:
        c = canvas.Canvas(os.path.join(pasta, nome), pagesize=(l * cm, a * cm))
        c.setFillColor(cor); c.rect(0, 0, l * cm, a * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", min(l, a) * 0.09 * cm)
        c.drawCentredString(l * cm / 2, a * cm / 2, texto)
        c.save()
        print("gerado:", nome)

if __name__ == "__main__":
    gerar(sys.argv[1] if len(sys.argv) > 1 else "artes")
