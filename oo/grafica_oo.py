"""
Paradigmas em Ação — Protótipo ORIENTADO A OBJETOS
Domínio: gráfica de comunicação visual (controle de materiais + orçamento por m²).

Fluxo demonstrado:
  1. cadastra materiais no estoque;
  2. lê as artes em PDF e descobre largura x altura (cm);
  3. monta um orçamento com banner, adesivo e placa de PVC;
  4. aprova o orçamento, dando baixa no estoque;
  5. lista os materiais que ficaram abaixo do estoque mínimo.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import date

from pypdf import PdfReader

PT_PARA_CM = 2.54 / 72          # 1 ponto PDF = 1/72 polegada
AREA_MINIMA_M2 = 0.25           # área mínima cobrada por item
PERDA_PRODUCAO = 0.10           # 10% de perda (sangria, refile, erro)


class EstoqueInsuficienteError(Exception):
    """Lançada quando não há material suficiente para produzir um pedido."""


# --------------------------------------------------------------------------
class Material:
    """Matéria-prima vendida por m² (lona, vinil, chapa de PVC...)."""

    AMBIENTES = ("interno", "externo", "ambos")

    def __init__(self, codigo: str, nome: str, preco_m2: float, ambiente: str):
        if ambiente not in self.AMBIENTES:
            raise ValueError(f"Ambiente inválido: {ambiente}")
        self._codigo = codigo
        self._nome = nome
        self._ambiente = ambiente
        self.preco_m2 = preco_m2          # passa pela validação do setter

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def ambiente(self) -> str:
        return self._ambiente

    @property
    def preco_m2(self) -> float:
        return self._preco_m2

    @preco_m2.setter
    def preco_m2(self, valor: float) -> None:
        if valor <= 0:
            raise ValueError("O preço por m² deve ser positivo")
        self._preco_m2 = float(valor)

    def custo(self, area_m2: float) -> float:
        return area_m2 * self._preco_m2

    def __repr__(self) -> str:
        return f"Material({self._codigo}, R$ {self._preco_m2:.2f}/m²)"


# --------------------------------------------------------------------------
class Estoque:
    """Controla o saldo (em m²) de cada material. Os dicionários são privados."""

    def __init__(self):
        self.__materiais: dict[str, Material] = {}
        self.__saldos: dict[str, float] = {}
        self.__minimos: dict[str, float] = {}

    def cadastrar(self, material: Material, saldo_m2: float, minimo_m2: float) -> None:
        self.__materiais[material.codigo] = material
        self.__saldos[material.codigo] = float(saldo_m2)
        self.__minimos[material.codigo] = float(minimo_m2)

    def material(self, codigo: str) -> Material:
        return self.__materiais[codigo]

    def saldo(self, codigo: str) -> float:
        return round(self.__saldos[codigo], 3)

    def tem_disponivel(self, codigo: str, area_m2: float) -> bool:
        return self.__saldos.get(codigo, 0.0) >= area_m2

    def baixar(self, codigo: str, area_m2: float) -> None:
        if not self.tem_disponivel(codigo, area_m2):
            raise EstoqueInsuficienteError(
                f"{codigo}: precisa {area_m2:.3f} m², há {self.saldo(codigo):.3f} m²")
        self.__saldos[codigo] -= area_m2

    def repor(self, codigo: str, area_m2: float) -> None:
        self.__saldos[codigo] += area_m2

    def abaixo_do_minimo(self) -> list[str]:
        return [c for c, s in self.__saldos.items() if s < self.__minimos[c]]

    def relatorio(self) -> str:
        linhas = []
        for c, s in self.__saldos.items():
            alerta = "  <-- REPOR" if s < self.__minimos[c] else ""
            linhas.append(f"  {c:<20}{s:>8.3f} m²  (mín. {self.__minimos[c]:.1f}){alerta}")
        return "\n".join(linhas)


# --------------------------------------------------------------------------
class ArquivoArte:
    """Arte enviada pelo cliente em PDF. Lê o tamanho da 1ª página.

    O PDF guarda o tamanho da página em pontos (1/72 pol). Usa-se o TrimBox
    (área final após o corte) e, se não existir, o MediaBox. O parâmetro
    'escala' permite artes feitas reduzidas (ex.: 1:10 -> escala=10).
    """

    def __init__(self, caminho: str, escala: float = 1.0):
        self._caminho = caminho
        self._escala = escala
        self._largura_cm, self._altura_cm = self._ler_dimensoes()

    def _ler_dimensoes(self) -> tuple[float, float]:
        pagina = PdfReader(self._caminho).pages[0]
        caixa = pagina.trimbox                         # cai no mediabox se ausente
        unidade = float(pagina.get("/UserUnit", 1))
        largura = float(caixa.width) * unidade * PT_PARA_CM * self._escala
        altura = float(caixa.height) * unidade * PT_PARA_CM * self._escala
        if pagina.rotation in (90, 270):
            largura, altura = altura, largura
        return round(largura, 1), round(altura, 1)

    @property
    def largura_cm(self) -> float:
        return self._largura_cm

    @property
    def altura_cm(self) -> float:
        return self._altura_cm

    @property
    def area_m2(self) -> float:
        return self._largura_cm * self._altura_cm / 10_000

    @property
    def perimetro_cm(self) -> float:
        return 2 * (self._largura_cm + self._altura_cm)

    def __repr__(self) -> str:
        return f"Arte({self._largura_cm:g} x {self._altura_cm:g} cm)"


# --------------------------------------------------------------------------
class ProdutoImpresso(ABC):
    """Classe abstrata: tudo que a gráfica imprime a partir de uma arte."""

    def __init__(self, arte: ArquivoArte, material: Material, quantidade: int = 1):
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        if material.codigo not in self.materiais_aceitos():
            raise ValueError(f"{self.tipo()} não pode ser feito em {material.codigo}")
        self._arte = arte
        self._material = material
        self._quantidade = quantidade

    # ---- pontos de variação (cada subclasse responde do seu jeito) ----
    @abstractmethod
    def tipo(self) -> str: ...

    @abstractmethod
    def materiais_aceitos(self) -> set[str]: ...

    @abstractmethod
    def custo_acabamento(self) -> float:
        """Custo de acabamento do item inteiro (todas as unidades)."""

    # ---- comportamento comum, herdado por todos ----
    @property
    def material(self) -> Material:
        return self._material

    @property
    def quantidade(self) -> int:
        return self._quantidade

    def area_cobrada_m2(self) -> float:
        return max(self._arte.area_m2 * self._quantidade, AREA_MINIMA_M2)

    def consumo_estoque_m2(self) -> float:
        return self._arte.area_m2 * self._quantidade * (1 + PERDA_PRODUCAO)

    def preco_total(self) -> float:
        return round(self._material.custo(self.area_cobrada_m2())
                     + self.custo_acabamento(), 2)

    def descricao(self) -> str:
        return (f"{self._quantidade}x {self.tipo()} {self._arte.largura_cm:g}x"
                f"{self._arte.altura_cm:g} cm em {self._material.nome}")


class Banner(ProdutoImpresso):
    PRECO_ILHOS = 0.80          # 1 ilhós a cada 50 cm de perímetro
    PRECO_BASTAO_CM = 0.15      # bastão (em cima e embaixo) por cm de largura
    PRECO_CORDA = 3.00

    def __init__(self, arte, material, quantidade=1, acabamento="ilhos"):
        super().__init__(arte, material, quantidade)
        if acabamento not in ("ilhos", "bastao"):
            raise ValueError("Acabamento de banner: 'ilhos' ou 'bastao'")
        self._acabamento = acabamento

    def tipo(self):
        return "Banner"

    def materiais_aceitos(self):
        return {"LONA440", "LONA280"}

    def custo_acabamento(self):
        if self._acabamento == "ilhos":
            n_ilhos = math.ceil(self._arte.perimetro_cm / 50)
            unitario = n_ilhos * self.PRECO_ILHOS
        else:
            unitario = self._arte.largura_cm * self.PRECO_BASTAO_CM + self.PRECO_CORDA
        return unitario * self._quantidade


class Adesivo(ProdutoImpresso):
    PRECO_LAMINACAO_M2 = 25.00
    PRECO_RECORTE_M2 = 18.00

    def __init__(self, arte, material, quantidade=1, laminado=False, recorte=False):
        super().__init__(arte, material, quantidade)
        self._laminado = laminado
        self._recorte = recorte

    def tipo(self):
        return "Adesivo"

    def materiais_aceitos(self):
        return {"VINIL_BR", "VINIL_TR", "VINIL_PERF"}

    def custo_acabamento(self):
        area = self.area_cobrada_m2()
        custo = 0.0
        if self._laminado:
            custo += area * self.PRECO_LAMINACAO_M2
        if self._recorte:
            custo += area * self.PRECO_RECORTE_M2
        return custo


class PlacaPVC(ProdutoImpresso):
    PRECO_CORTE_M = 6.00        # corte da chapa por metro de perímetro
    PRECO_FURO = 1.50

    def __init__(self, arte, material, quantidade=1, furos=0):
        super().__init__(arte, material, quantidade)
        self._furos = furos

    def tipo(self):
        return "Placa PVC"

    def materiais_aceitos(self):
        return {"PVC3MM", "PVC5MM"}

    def custo_acabamento(self):
        corte = self._arte.perimetro_cm / 100 * self.PRECO_CORTE_M
        return (corte + self._furos * self.PRECO_FURO) * self._quantidade


# --------------------------------------------------------------------------
class Cliente:
    def __init__(self, nome: str, telefone: str):
        self._nome = nome
        self._telefone = telefone

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def telefone(self) -> str:
        return self._telefone


class Orcamento:
    """Agrupa produtos de um cliente, calcula desconto e controla o status."""

    FAIXAS_DESCONTO = ((1500.0, 0.10), (500.0, 0.05))   # (a partir de, %)
    _proximo_numero = 1

    def __init__(self, cliente: Cliente):
        self._numero = Orcamento._proximo_numero
        Orcamento._proximo_numero += 1
        self._cliente = cliente
        self._data = date.today()
        self._itens: list[ProdutoImpresso] = []
        self._status = "ABERTO"

    @property
    def numero(self) -> int:
        return self._numero

    @property
    def status(self) -> str:
        return self._status

    @property
    def itens(self) -> tuple[ProdutoImpresso, ...]:
        return tuple(self._itens)              # cópia: ninguém altera a lista por fora

    def adicionar(self, produto: ProdutoImpresso) -> None:
        if self._status != "ABERTO":
            raise RuntimeError("Orçamento já fechado")
        self._itens.append(produto)

    def subtotal(self) -> float:
        return round(sum(p.preco_total() for p in self._itens), 2)   # polimorfismo

    def percentual_desconto(self) -> float:
        for limite, pct in self.FAIXAS_DESCONTO:
            if self.subtotal() >= limite:
                return pct
        return 0.0

    def desconto(self) -> float:
        return round(self.subtotal() * self.percentual_desconto(), 2)

    def total(self) -> float:
        return round(self.subtotal() - self.desconto(), 2)

    def aprovar(self, estoque: Estoque) -> None:
        """Confere TODO o material antes de baixar (tudo ou nada)."""
        consumo: dict[str, float] = {}
        for p in self._itens:
            consumo[p.material.codigo] = consumo.get(p.material.codigo, 0) + p.consumo_estoque_m2()
        for codigo, area in consumo.items():
            if not estoque.tem_disponivel(codigo, area):
                raise EstoqueInsuficienteError(
                    f"Sem {codigo} suficiente: precisa {area:.3f} m², há {estoque.saldo(codigo):.3f} m²")
        for codigo, area in consumo.items():
            estoque.baixar(codigo, area)
        self._status = "APROVADO"

    def resumo(self) -> str:
        linhas = [f"ORÇAMENTO Nº {self._numero} - {self._cliente.nome} - {self._data:%d/%m/%Y}"]
        for p in self._itens:
            linhas.append(f"  {p.descricao():<52} R$ {p.preco_total():>9.2f}")
        linhas.append(f"  {'Subtotal':<52} R$ {self.subtotal():>9.2f}")
        linhas.append(f"  {'Desconto (' + format(self.percentual_desconto(), '.0%') + ')':<52} R$ {self.desconto():>9.2f}")
        linhas.append(f"  {'TOTAL':<52} R$ {self.total():>9.2f}")
        linhas.append(f"  Status: {self._status}")
        return "\n".join(linhas)


# --------------------------------------------------------------------------
def montar_estoque() -> Estoque:
    estoque = Estoque()
    estoque.cadastrar(Material("LONA440", "Lona 440g", 45.00, "externo"), 50, 10)
    estoque.cadastrar(Material("LONA280", "Lona 280g", 32.00, "interno"), 8, 10)
    estoque.cadastrar(Material("VINIL_BR", "Vinil branco", 55.00, "ambos"), 12, 10)
    estoque.cadastrar(Material("VINIL_TR", "Vinil transparente", 60.00, "interno"), 4, 5)
    estoque.cadastrar(Material("VINIL_PERF", "Vinil perfurado", 70.00, "externo"), 6, 3)
    estoque.cadastrar(Material("PVC3MM", "PVC 3mm", 120.00, "interno"), 3, 1)
    estoque.cadastrar(Material("PVC5MM", "PVC 5mm", 160.00, "externo"), 0.5, 1)
    return estoque


def main(pasta_artes: str = "artes") -> None:
    estoque = montar_estoque()
    print("== Estoque inicial ==")
    print(estoque.relatorio())

    banner_pdf = ArquivoArte(f"{pasta_artes}/banner_promocao_90x120.pdf")
    adesivo_pdf = ArquivoArte(f"{pasta_artes}/adesivo_logo_30x30.pdf")
    placa_pdf = ArquivoArte(f"{pasta_artes}/placa_saida_60x40.pdf")
    print("\n== Artes lidas dos PDFs ==")
    for nome, arte in (("banner", banner_pdf), ("adesivo", adesivo_pdf), ("placa", placa_pdf)):
        print(f"  {nome:<8} {arte}  área = {arte.area_m2:.4f} m²")

    orc = Orcamento(Cliente("Padaria Pão Quente", "(42) 99999-0000"))
    orc.adicionar(Banner(banner_pdf, estoque.material("LONA440"), 1, acabamento="ilhos"))
    orc.adicionar(Adesivo(adesivo_pdf, estoque.material("VINIL_BR"), 50, laminado=True, recorte=True))
    orc.adicionar(PlacaPVC(placa_pdf, estoque.material("PVC3MM"), 2, furos=4))

    print("\n== Polimorfismo: mesmo método, comportamentos diferentes ==")
    for p in orc.itens:
        print(f"  {p.tipo():<10} custo_acabamento() = R$ {p.custo_acabamento():.2f}")

    print()
    print(orc.resumo())

    orc.aprovar(estoque)
    print(f"\nOrçamento {orc.numero} -> {orc.status}")
    print("\n== Estoque após a aprovação ==")
    print(estoque.relatorio())
    print("\nMateriais abaixo do mínimo:", estoque.abaixo_do_minimo())

    print("\n== Regras de negócio protegidas ==")
    try:
        Banner(placa_pdf, estoque.material("PVC3MM"))
    except ValueError as e:
        print("  ValueError:", e)
    try:
        orc2 = Orcamento(Cliente("Loja Bela", "(42) 98888-0000"))
        orc2.adicionar(PlacaPVC(placa_pdf, estoque.material("PVC5MM"), 2))
        orc2.aprovar(estoque)
    except EstoqueInsuficienteError as e:
        print("  EstoqueInsuficienteError:", e)
    try:
        estoque.material("LONA440").preco_m2 = -10
    except ValueError as e:
        print("  ValueError:", e)


if __name__ == "__main__":
    main()
