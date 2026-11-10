/* ==========================================================
   Paradigmas em Ação - Base de conhecimento LÓGICA (Prolog)
   Domínio: gráfica de comunicação visual
   Executar em SWI-Prolog:  ?- consult('base_grafica.pl').
   ou colar em https://swish.swi-prolog.org
   ========================================================== */

/* ---------------- FATOS ---------------- */

% material(Codigo, Nome, PrecoM2, Ambiente).
material(lona440,     'Lona 440g',          45.0,  externo).
material(lona280,     'Lona 280g',          32.0,  interno).
material(vinil_br,    'Vinil branco',       55.0,  ambos).
material(vinil_tr,    'Vinil transparente', 60.0,  interno).
material(vinil_perf,  'Vinil perfurado',    70.0,  externo).
material(pvc3mm,      'PVC 3mm',           120.0,  interno).
material(pvc5mm,      'PVC 5mm',           160.0,  externo).

% aceita(Produto, Material): o produto pode ser feito nesse material.
aceita(banner,  lona440).
aceita(banner,  lona280).
aceita(adesivo, vinil_br).
aceita(adesivo, vinil_tr).
aceita(adesivo, vinil_perf).
aceita(placa,   pvc3mm).
aceita(placa,   pvc5mm).

% estoque(Material, SaldoM2).
estoque(lona440,    50.0).
estoque(lona280,     8.0).
estoque(vinil_br,   12.0).
estoque(vinil_tr,    4.0).
estoque(vinil_perf,  6.0).
estoque(pvc3mm,      3.0).
estoque(pvc5mm,      0.5).

% minimo(Material, EstoqueMinimoM2).
minimo(lona440,    10.0).
minimo(lona280,    10.0).
minimo(vinil_br,   10.0).
minimo(vinil_tr,    5.0).
minimo(vinil_perf,  3.0).
minimo(pvc3mm,      1.0).
minimo(pvc5mm,      1.0).

% fornecedor(Material, Fornecedor).
fornecedor(lona440,    lonas_sul).
fornecedor(lona280,    lonas_sul).
fornecedor(vinil_br,   adesivos_pr).
fornecedor(vinil_tr,   adesivos_pr).
fornecedor(vinil_perf, adesivos_pr).
fornecedor(pvc3mm,     chapas_brasil).
fornecedor(pvc5mm,     chapas_brasil).

/* ---------------- REGRAS ---------------- */

% Um material serve para o ambiente pedido, ou serve para "ambos".
serve_para(Material, Ambiente) :- material(Material, _, _, Ambiente).
serve_para(Material, _)        :- material(Material, _, _, ambos).

% Material recomendado para um produto num ambiente.
recomendado(Produto, Ambiente, Material) :-
    aceita(Produto, Material),
    serve_para(Material, Ambiente).

% Material com saldo abaixo do mínimo precisa ser reposto.
precisa_repor(Material) :-
    estoque(Material, Saldo),
    minimo(Material, Minimo),
    Saldo < Minimo.

% Fornecedor que deve ser acionado (há algo dele para repor).
acionar_fornecedor(Fornecedor, Material) :-
    precisa_repor(Material),
    fornecedor(Material, Fornecedor).

% Área (m²) a partir de largura e altura em cm.
area_m2(Largura, Altura, Area) :-
    Area is Largura * Altura / 10000.

% Consumo de estoque com 10% de perda de produção.
consumo(Largura, Altura, Qtd, Consumo) :-
    area_m2(Largura, Altura, Area),
    Consumo is Area * Qtd * 1.1.

% Dá para produzir se o material é aceito e há saldo suficiente.
pode_produzir(Produto, Material, Largura, Altura, Qtd) :-
    aceita(Produto, Material),
    consumo(Largura, Altura, Qtd, Consumo),
    estoque(Material, Saldo),
    Saldo >= Consumo.

% Preço só do material, com área mínima cobrada de 0,25 m².
preco_material(Material, Largura, Altura, Qtd, Preco) :-
    material(Material, _, PrecoM2, _),
    area_m2(Largura, Altura, Area),
    AreaCobrada is max(Area * Qtd, 0.25),
    Preco is AreaCobrada * PrecoM2.

% O material recomendado mais barato (não existe outro recomendado com preço menor).
mais_barato(Produto, Ambiente, Material) :-
    recomendado(Produto, Ambiente, Material),
    material(Material, _, Preco, _),
    \+ ( recomendado(Produto, Ambiente, Outro),
         material(Outro, _, PrecoOutro, _),
         PrecoOutro < Preco ).

/* ---------------- CONSULTAS DE EXEMPLO ----------------
?- recomendado(banner, externo, M).
?- recomendado(adesivo, externo, M).
?- precisa_repor(M).
?- acionar_fornecedor(F, M).
?- pode_produzir(adesivo, vinil_br, 30, 30, 50).
?- pode_produzir(placa, pvc5mm, 60, 40, 2).
?- preco_material(lona440, 90, 120, 1, P).
?- mais_barato(adesivo, interno, M).
?- findall(M, precisa_repor(M), Lista), length(Lista, N).
------------------------------------------------------- */
