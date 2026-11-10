"""Testes automatizados (unittest) — executar:  python -m unittest -v testes/test_paradigmas.py"""
import os
import sys
import unittest

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path[:0] = [os.path.join(RAIZ, "oo"), os.path.join(RAIZ, "funcional")]
ARTES = os.path.join(RAIZ, "artes")

import grafica_oo as oo
import orcamento_funcional as fn


def pdf(nome):
    return os.path.join(ARTES, nome)


class TestLeituraPDF(unittest.TestCase):
    def test_dimensoes_banner(self):
        arte = oo.ArquivoArte(pdf("banner_promocao_90x120.pdf"))
        self.assertEqual((arte.largura_cm, arte.altura_cm), (90.0, 120.0))
        self.assertAlmostEqual(arte.area_m2, 1.08)

    def test_escala_1_para_10(self):
        arte = oo.ArquivoArte(pdf("adesivo_logo_30x30.pdf"), escala=10)
        self.assertEqual(arte.largura_cm, 300.0)


class TestOrientadoObjetos(unittest.TestCase):
    def setUp(self):
        self.est = oo.montar_estoque()
        self.banner = oo.ArquivoArte(pdf("banner_promocao_90x120.pdf"))
        self.adesivo = oo.ArquivoArte(pdf("adesivo_logo_30x30.pdf"))
        self.placa = oo.ArquivoArte(pdf("placa_saida_60x40.pdf"))

    def test_polimorfismo_precos(self):
        itens = [oo.Banner(self.banner, self.est.material("LONA440")),
                 oo.Adesivo(self.adesivo, self.est.material("VINIL_BR"), 50, True, True),
                 oo.PlacaPVC(self.placa, self.est.material("PVC3MM"), 2, 4)]
        self.assertEqual([p.preco_total() for p in itens], [55.80, 441.00, 93.60])

    def test_area_minima(self):
        p = oo.Adesivo(self.adesivo, self.est.material("VINIL_BR"), 1)   # 0,09 m² -> cobra 0,25
        self.assertEqual(p.preco_total(), 13.75)

    def test_desconto_5_porcento(self):
        orc = oo.Orcamento(oo.Cliente("X", ""))
        orc.adicionar(oo.Adesivo(self.adesivo, self.est.material("VINIL_BR"), 50, True, True))
        orc.adicionar(oo.Banner(self.banner, self.est.material("LONA440")))
        orc.adicionar(oo.PlacaPVC(self.placa, self.est.material("PVC3MM"), 2, 4))
        self.assertEqual((orc.subtotal(), orc.desconto(), orc.total()), (590.40, 29.52, 560.88))

    def test_material_incompativel(self):
        with self.assertRaises(ValueError):
            oo.Banner(self.banner, self.est.material("PVC3MM"))

    def test_aprovacao_tudo_ou_nada(self):
        orc = oo.Orcamento(oo.Cliente("X", ""))
        orc.adicionar(oo.Banner(self.banner, self.est.material("LONA440")))
        orc.adicionar(oo.PlacaPVC(self.placa, self.est.material("PVC5MM"), 2))
        with self.assertRaises(oo.EstoqueInsuficienteError):
            orc.aprovar(self.est)
        self.assertEqual(self.est.saldo("LONA440"), 50.0)   # nada foi baixado
        self.assertEqual(orc.status, "ABERTO")

    def test_encapsulamento(self):
        with self.assertRaises(AttributeError):
            getattr(self.est, "__saldos")                      # atributo privado (name mangling)
        with self.assertRaises(ValueError):
            self.est.material("LONA440").preco_m2 = 0


class TestFuncional(unittest.TestCase):
    def test_mesmo_resultado_que_oo(self):
        r = fn.orcar(fn.PEDIDO)
        self.assertEqual(r["precos"], (55.80, 441.00, 93.60))
        self.assertEqual((r["subtotal"], r["desconto"], r["total"]), (590.40, 29.52, 560.88))

    def test_funcao_pura_mesma_entrada_mesma_saida(self):
        self.assertEqual(fn.orcar(fn.PEDIDO), fn.orcar(fn.PEDIDO))

    def test_desconto_recursivo(self):
        self.assertEqual([fn.percentual_desconto(v) for v in (100, 500, 1499.99, 1500)],
                         [0.0, 0.05, 0.05, 0.10])

    def test_estoque_original_intacto(self):
        novo = fn.baixar_estoque(fn.ESTOQUE_INICIAL, fn.PEDIDO)
        self.assertEqual(fn.ESTOQUE_INICIAL["VINIL_BR"], 12.0)
        self.assertEqual(novo["VINIL_BR"], 7.05)
        with self.assertRaises(TypeError):
            fn.ESTOQUE_INICIAL["VINIL_BR"] = 0

    def test_compor(self):
        self.assertEqual(fn.compor(lambda x: x + 1, lambda x: x * 10)(2), 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
