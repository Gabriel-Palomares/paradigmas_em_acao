# Paradigmas em Ação — Gráfica de Comunicação Visual

Controle de materiais (estoque em m²) + orçamento por m² a partir da arte em PDF.

| Pasta | Paradigma | Como executar |
|---|---|---|
| `oo/grafica_oo.py` | Orientado a objetos | `python oo/grafica_oo.py` |
| `funcional/orcamento_funcional.py` | Funcional | `python funcional/orcamento_funcional.py` |
| `logico/base_grafica.pl` | Lógico (Prolog) | `swipl logico/base_grafica.pl` ou colar em https://swish.swi-prolog.org |
| `eventos/grafica_eventos.py` | Orientado a eventos | `python eventos/grafica_eventos.py` |
| `orcar.py` | Calculadora (usa o modelo OO) | `python orcar.py artes/banner_promocao_90x120.pdf banner LONA440` |
| `prototipo/index.html` | Protótipo com interface (eventos + funções puras em JS) | abrir no navegador |
| `testes/test_paradigmas.py` | Testes automatizados | `python -m unittest -v testes/test_paradigmas.py` |

Requisitos: Python 3.10+ e `pip install pypdf`. As artes de exemplo ficam em `artes/`
(`python gerar_artes.py artes` recria; exige `reportlab`).
