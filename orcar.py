"""Calculadora de orçamento: o cliente informa a arte em PDF e recebe o preço.

Exemplos:
  python orcar.py artes/banner_promocao_90x120.pdf banner LONA440
  python orcar.py artes/adesivo_logo_30x30.pdf adesivo VINIL_BR --qtd 50 --laminado --recorte
  python orcar.py artes/placa_saida_60x40.pdf placa PVC3MM --qtd 2 --furos 4
  python orcar.py arte_reduzida.pdf banner LONA440 --escala 10     (arte feita em 1:10)
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "oo"))
from grafica_oo import ArquivoArte, Adesivo, Banner, Cliente, Orcamento, PlacaPVC, montar_estoque

ap = argparse.ArgumentParser(description="Orçamento por m² a partir da arte em PDF")
ap.add_argument("pdf")
ap.add_argument("produto", choices=["banner", "adesivo", "placa"])
ap.add_argument("material")
ap.add_argument("--qtd", type=int, default=1)
ap.add_argument("--escala", type=float, default=1.0)
ap.add_argument("--bastao", action="store_true", help="banner com bastão e corda")
ap.add_argument("--laminado", action="store_true")
ap.add_argument("--recorte", action="store_true")
ap.add_argument("--furos", type=int, default=0)
ap.add_argument("--cliente", default="Cliente balcão")
a = ap.parse_args()

estoque = montar_estoque()
arte = ArquivoArte(a.pdf, a.escala)
mat = estoque.material(a.material)
if a.produto == "banner":
    prod = Banner(arte, mat, a.qtd, "bastao" if a.bastao else "ilhos")
elif a.produto == "adesivo":
    prod = Adesivo(arte, mat, a.qtd, a.laminado, a.recorte)
else:
    prod = PlacaPVC(arte, mat, a.qtd, a.furos)

orc = Orcamento(Cliente(a.cliente, ""))
orc.adicionar(prod)
print(f"Arte lida: {arte.largura_cm:g} x {arte.altura_cm:g} cm  ({arte.area_m2:.4f} m² por unidade)")
print(orc.resumo())
