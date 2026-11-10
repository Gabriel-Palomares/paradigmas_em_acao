"""
Paradigmas em Ação — Recorte FUNCIONAL
Operação escolhida: CALCULAR O ORÇAMENTO e PROJETAR A BAIXA DE ESTOQUE.

Princípios aplicados:
  * dados imutáveis (NamedTuple, tuple, frozenset, MappingProxyType);
  * funções puras: o resultado depende só da entrada, sem efeitos colaterais;
  * funções de alta ordem (map, filter, reduce, funções que recebem/retornam funções);
  * funções anônimas (lambda) e closures;
  * recursão no lugar de laços.
"""
from __future__ import annotations

import math
from functools import reduce
from types import MappingProxyType
from typing import Callable, Mapping, NamedTuple

AREA_MINIMA_M2 = 0.25
PERDA_PRODUCAO = 0.10
FAIXAS_DESCONTO = ((1500.0, 0.10), (500.0, 0.05))       # tupla: não pode ser alterada


class Item(NamedTuple):                                 # registro imutável
    tipo: str               # "banner" | "adesivo" | "placa"
    material: str
    preco_m2: float
    largura_cm: float
    altura_cm: float
    quantidade: int
    opcoes: frozenset = frozenset()
    furos: int = 0


# ---------- funções puras básicas ----------
def area_m2(item: Item) -> float:
    return item.largura_cm * item.altura_cm / 10_000


def perimetro_cm(item: Item) -> float:
    return 2 * (item.largura_cm + item.altura_cm)


def area_cobrada(item: Item) -> float:
    return max(area_m2(item) * item.quantidade, AREA_MINIMA_M2)


def consumo_m2(item: Item) -> float:
    return area_m2(item) * item.quantidade * (1 + PERDA_PRODUCAO)


# ---------- acabamentos: uma TABELA DE FUNÇÕES (lambdas) em vez de herança ----------
def _acab_banner(i: Item) -> float:
    if "bastao" in i.opcoes:
        return (i.largura_cm * 0.15 + 3.00) * i.quantidade
    return math.ceil(perimetro_cm(i) / 50) * 0.80 * i.quantidade


ACABAMENTOS: Mapping[str, Callable[[Item], float]] = MappingProxyType({
    "banner": _acab_banner,
    "adesivo": lambda i: area_cobrada(i) * (25.00 * ("laminado" in i.opcoes)
                                            + 18.00 * ("recorte" in i.opcoes)),
    "placa": lambda i: (perimetro_cm(i) / 100 * 6.00
                        + 1.50 * i.furos) * i.quantidade,
})


def preco_item(item: Item) -> float:
    return round(area_cobrada(item) * item.preco_m2 + ACABAMENTOS[item.tipo](item), 2)


# ---------- recursão ----------
def percentual_desconto(subtotal: float, faixas: tuple = FAIXAS_DESCONTO) -> float:
    """Percorre as faixas recursivamente: caso-base = tupla vazia."""
    if not faixas:
        return 0.0
    (limite, pct), *resto = faixas
    return pct if subtotal >= limite else percentual_desconto(subtotal, tuple(resto))


def soma_recursiva(valores: tuple) -> float:
    return 0.0 if not valores else valores[0] + soma_recursiva(valores[1:])


# ---------- alta ordem e composição ----------
def compor(*funcoes: Callable) -> Callable:
    """compor(f, g, h)(x) == h(g(f(x)))"""
    return reduce(lambda f, g: lambda x: g(f(x)), funcoes)


def aplicar_desconto(pct: float) -> Callable[[float], float]:
    """Closure: devolve uma função que já 'lembra' o percentual."""
    return lambda valor: round(valor * (1 - pct), 2)


def orcar(itens: tuple[Item, ...]) -> Mapping:
    precos = tuple(map(preco_item, itens))
    subtotal = round(reduce(lambda acc, p: acc + p, precos, 0.0), 2)
    pct = percentual_desconto(subtotal)
    total = aplicar_desconto(pct)(subtotal)
    return MappingProxyType({
        "precos": precos, "subtotal": subtotal,
        "percentual": pct, "desconto": round(subtotal - total, 2), "total": total,
    })


# ---------- estoque sem mutação ----------
def consumo_por_material(itens: tuple[Item, ...]) -> Mapping[str, float]:
    return MappingProxyType(reduce(
        lambda acc, it: {**acc, it.material: acc.get(it.material, 0.0) + consumo_m2(it)},
        itens, {}))


def baixar_estoque(estoque: Mapping[str, float], itens: tuple[Item, ...]) -> Mapping[str, float]:
    """Devolve um NOVO estoque; o original continua intacto."""
    consumo = consumo_por_material(itens)
    return MappingProxyType({m: round(s - consumo.get(m, 0.0), 3) for m, s in estoque.items()})


def cabe_no_estoque(estoque: Mapping[str, float], itens: tuple[Item, ...]) -> bool:
    consumo = consumo_por_material(itens)
    return all(estoque.get(m, 0.0) >= c for m, c in consumo.items())


def criticos(estoque: Mapping[str, float], minimos: Mapping[str, float]) -> tuple[str, ...]:
    return tuple(filter(lambda m: estoque[m] < minimos[m], estoque))


# ---------- demonstração ----------
ESTOQUE_INICIAL = MappingProxyType({"LONA440": 50.0, "LONA280": 8.0, "VINIL_BR": 12.0,
                                    "VINIL_TR": 4.0, "VINIL_PERF": 6.0, "PVC3MM": 3.0, "PVC5MM": 0.5})
MINIMOS = MappingProxyType({"LONA440": 10, "LONA280": 10, "VINIL_BR": 10,
                            "VINIL_TR": 5, "VINIL_PERF": 3, "PVC3MM": 1, "PVC5MM": 1})

PEDIDO = (
    Item("banner", "LONA440", 45.0, 90, 120, 1, frozenset({"ilhos"})),
    Item("adesivo", "VINIL_BR", 55.0, 30, 30, 50, frozenset({"laminado", "recorte"})),
    Item("placa", "PVC3MM", 120.0, 60, 40, 2, furos=4),
)

if __name__ == "__main__":
    r = orcar(PEDIDO)
    print("ENTRADA :")
    for it in PEDIDO:
        print(f"  {it.tipo:<8} {it.material:<9} {it.largura_cm}x{it.altura_cm} cm  qtd={it.quantidade:<3}"
              f" R$ {it.preco_m2:.2f}/m²  opções={sorted(it.opcoes)} furos={it.furos}")
    print("SAÍDA   :")
    for it, p in zip(PEDIDO, r["precos"]):
        print(f"  {it.tipo:<8} R$ {p:>8.2f}")
    print(f"  subtotal R$ {r['subtotal']:.2f} | desconto {r['percentual']:.0%} = "
          f"R$ {r['desconto']:.2f} | total R$ {r['total']:.2f}")

    print("\nsoma_recursiva(precos) =", round(soma_recursiva(r["precos"]), 2))
    print("percentual_desconto(1600) =", percentual_desconto(1600))
    print("percentual_desconto(100)  =", percentual_desconto(100))

    m2_para_reais = compor(lambda m2: m2 * 45.0, aplicar_desconto(0.05))
    print("compor(m2 * 45, -5%)(2.0) =", m2_para_reais(2.0))

    novo = baixar_estoque(ESTOQUE_INICIAL, PEDIDO)
    print("\ncabe_no_estoque =", cabe_no_estoque(ESTOQUE_INICIAL, PEDIDO))
    print("estoque ORIGINAL:", dict(ESTOQUE_INICIAL))
    print("estoque NOVO    :", dict(novo))
    print("críticos antes  :", criticos(ESTOQUE_INICIAL, MINIMOS))
    print("críticos depois :", criticos(novo, MINIMOS))
    try:
        ESTOQUE_INICIAL["LONA440"] = 0
    except TypeError as e:
        print("\nTentativa de alterar o estoque original ->", type(e).__name__, ":", e)
