"""
Paradigmas em Ação — Forma complementar: PROGRAMAÇÃO ORIENTADA A EVENTOS

Na gráfica, o trabalho acontece em reação a acontecimentos:
  "chegou uma arte em PDF"  ->  "orçamento gerado"  ->  "cliente aprovou"
  ->  "estoque baixado"  ->  "material abaixo do mínimo"  ->  "pedido ao fornecedor".

Ninguém chama ninguém diretamente: cada parte publica um evento num barramento
(EventBus) e quem se inscreveu nele reage. O laço principal apenas despacha
eventos de uma fila, como o laço de eventos de uma interface gráfica.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict, deque
from typing import Callable

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "oo"))
from grafica_oo import (ArquivoArte, Adesivo, Banner, Cliente,  # noqa: E402
                        EstoqueInsuficienteError, Orcamento, PlacaPVC, montar_estoque)


class EventBus:
    """Barramento publish/subscribe com fila de eventos."""

    def __init__(self):
        self._assinantes: dict[str, list[Callable]] = defaultdict(list)
        self._fila: deque[tuple[str, dict]] = deque()

    def inscrever(self, evento: str, tratador: Callable[[dict], None]) -> None:
        self._assinantes[evento].append(tratador)

    def publicar(self, evento: str, **dados) -> None:
        self._fila.append((evento, dados))

    def processar(self) -> None:
        """Laço de eventos: despacha até a fila esvaziar."""
        while self._fila:
            evento, dados = self._fila.popleft()
            for tratador in self._assinantes[evento] + self._assinantes["*"]:
                tratador({"evento": evento, **dados})


# ---------------------------------------------------------------- tratadores
class Grafica:
    """Liga os tratadores ao barramento. Cada método reage a UM evento."""

    PRODUTOS = {"banner": Banner, "adesivo": Adesivo, "placa": PlacaPVC}

    def __init__(self, bus: EventBus):
        self.bus = bus
        self.estoque = montar_estoque()
        self.orcamentos: dict[int, Orcamento] = {}
        self.pedidos_compra: list[str] = []
        bus.inscrever("arte_recebida", self.gerar_orcamento)
        bus.inscrever("orcamento_aprovado", self.baixar_estoque)
        bus.inscrever("estoque_baixado", self.verificar_minimos)
        bus.inscrever("estoque_baixo", self.pedir_reposicao)
        bus.inscrever("estoque_insuficiente", self.avisar_vendedor)

    def gerar_orcamento(self, e: dict) -> None:
        arte = ArquivoArte(e["arquivo"])
        classe = self.PRODUTOS[e["produto"]]
        produto = classe(arte, self.estoque.material(e["material"]), e["qtd"], **e.get("opcoes", {}))
        orc = Orcamento(Cliente(e["cliente"], ""))
        orc.adicionar(produto)
        self.orcamentos[orc.numero] = orc
        self.bus.publicar("orcamento_gerado", numero=orc.numero,
                          descricao=produto.descricao(), total=orc.total())

    def baixar_estoque(self, e: dict) -> None:
        orc = self.orcamentos[e["numero"]]
        try:
            orc.aprovar(self.estoque)
            self.bus.publicar("estoque_baixado", numero=orc.numero)
        except EstoqueInsuficienteError as erro:
            self.bus.publicar("estoque_insuficiente", numero=orc.numero, motivo=str(erro))

    def verificar_minimos(self, e: dict) -> None:
        for codigo in self.estoque.abaixo_do_minimo():
            if codigo not in self.pedidos_compra:
                self.bus.publicar("estoque_baixo", material=codigo,
                                  saldo=self.estoque.saldo(codigo))

    def pedir_reposicao(self, e: dict) -> None:
        self.pedidos_compra.append(e["material"])

    def avisar_vendedor(self, e: dict) -> None:
        pass   # numa versão real: e-mail / WhatsApp ao vendedor


def log(e: dict) -> None:
    """Assinante coringa ('*'): registra todo evento, sem conhecer os demais."""
    dados = ", ".join(f"{k}={v}" for k, v in e.items() if k != "evento")
    print(f"  [evento] {e['evento']:<21} {dados}")


def main(pasta: str = "artes") -> None:
    bus = EventBus()
    grafica = Grafica(bus)
    bus.inscrever("*", log)

    # Cliente aprova automaticamente orçamentos até R$ 600 (simulação)
    bus.inscrever("orcamento_gerado",
                  lambda e: bus.publicar("orcamento_aprovado", numero=e["numero"])
                  if e["total"] <= 600 else None)

    # Simula a "pasta de entrada" recebendo PDFs ao longo do dia
    chegadas = [
        dict(arquivo=f"{pasta}/adesivo_logo_30x30.pdf", produto="adesivo", material="VINIL_BR",
             qtd=50, cliente="Padaria Pão Quente", opcoes={"laminado": True, "recorte": True}),
        dict(arquivo=f"{pasta}/banner_promocao_90x120.pdf", produto="banner", material="LONA440",
             qtd=1, cliente="Mercado Bom Preço"),
        dict(arquivo=f"{pasta}/placa_saida_60x40.pdf", produto="placa", material="PVC5MM",
             qtd=2, cliente="Clínica Vida", opcoes={"furos": 4}),
    ]
    for c in chegadas:
        print(f"\n>> PDF chegou na pasta de entrada: {os.path.basename(c['arquivo'])}")
        bus.publicar("arte_recebida", **c)
        bus.processar()

    print("\nPedidos de compra gerados automaticamente:", grafica.pedidos_compra)


if __name__ == "__main__":
    main()
