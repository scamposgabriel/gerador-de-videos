# Ações do roteiro (modo tutorial)

Cada ação é uma tupla: `("nome", argumento1, argumento2, ...)`. As ações de uma fala rodam em ordem; o que não precisa esperar
(cursor, destaque, legenda) anda junto com a narração. Seletor = seletor CSS (ex.: `"#busca"`, `".cartoes .cartao:nth-child(3)"`).

## Câmera
| Ação | O que faz |
|---|---|
| `("foco", sel, max_zoom)` | aproxima a câmera no elemento (até `max_zoom`, padrão 1,4) e acende o destaque nele. Bloco grande demais para aproximar: só rola até ele. |
| `("zoom", sel, max_zoom)` | só aproxima, sem destaque |
| `("zoom0",)` | volta a câmera ao normal |
| `("rolar", sel, margem_px)` | rola a página até o elemento ficar a `margem` px do topo |
| `("rolarTexto", "texto", margem)` | idem, achando o elemento pelo texto que começa com "texto" |
| `("topo",)` | volta ao topo da página |

Zoom acima de 1,8 só para elemento pequeno (ex.: horário no canto). Para leitura confortável, 1,2 a 1,5.

## Destaque (holofote, escurece o resto)
| Ação | O que faz |
|---|---|
| `("destacar", sel)` | destaca um elemento |
| `("destacarFaixa", sel_inicio, sel_fim)` | destaca do primeiro ao segundo elemento (ex.: cabeçalho até uma linha da tabela) |
| `("destacarTexto", "texto")` | destaca a seção (`<section>`) que contém o texto |
| `("destacarFaixaTexto", "texto", n_linhas)` | destaca do título com o texto até a linha `n` da tabela da seção |
| `("destacarColunas", sel_tabela, ini, fim)` | destaca as colunas `ini` a `fim` (contando do 0) de uma tabela, inclusive de uma capa |
| `("apagar",)` | apaga o destaque |

## Cursor e mouse
| Ação | O que faz |
|---|---|
| `("cursorEm", sel)` | leva o cursor desenhado até o elemento (sem clicar) |
| `("cursorEmTexto", "texto")` | idem, pelo texto |
| `("clique",)` | desenha o "clique" (anel) onde o cursor está, sem clicar de verdade |
| `("clicar", sel)` | leva o cursor, desenha o clique e clica de verdade (muda a tela) |
| `("clicarSemCursor", sel)` | clica de verdade sem mostrar o cursor (ex.: voltar um filtro) |
| `("menu", sel)` | volta o zoom, leva o cursor ao item de menu e clica (troca de aba) |
| `("pairar", sel)` | cursor até o elemento e mouse de verdade em cima: abre dicas de passar o mouse |
| `("pairarFaixa", "texto")` | idem numa faixa de gráfico SVG com `data-tip` que começa com o texto |
| `("digitar", sel, "texto")` | clica no campo e digita letra por letra |
| `("soltar",)` | tira o mouse de verdade de cima (fecha dicas) |

## Telas reais pesadas (painéis com abas, mapas, carregamento)
| Ação | O que faz |
|---|---|
| `("aguardar", "condição JS", limite_ms, folga_ms)` | espera a página ficar pronta **sem andar o relógio do vídeo**: o carregamento não aparece |
| `("esperarReal", ms)` | espera de verdade (mapa, gráfico), também sem andar o relógio |
| `("js", "código")` | roda um código na página (ex.: avisar a capa para entrar numa aba) |
| `("clicarFrame", "parte da url", seletor)` | clica num botão dentro de uma moldura (iframe), com cursor e anel |
| `("rolarDentro", sel)` | rola um painel que tem rolagem própria até o elemento |
| `("focoPct", x, y, max_zoom)` | ponto em % da tela sem zoom (como os pontos de um tutorial): acha o bloco que está lá, aproxima e destaca |
| `("cursorPct", x, y)` / `("destacarPct", x, y)` | cursor / destaque no ponto em % |
| `("focoFaixa", sel_a, sel_b, max_zoom)` | aproxima e destaca a faixa que vai de um elemento a outro (ex.: os botões do canto do topo) |
| `("focoRetPct", x, y, largura, altura, max_zoom)` | aproxima e destaca um retângulo em % da tela |
| `("destacarRetPct", x, y, largura, altura)` | destaca um retângulo em % (útil em capas feitas de imagem, como uma tela de login) |
| `("legendaEm", "topo" ou "base")` | muda a legenda de lugar quando ela cobriria um botão importante |

## Cartões (capas) e tempo
| Ação | O que faz |
|---|---|
| `("capa", "nome")` | mostra a capa `CAPAS["nome"]` do roteiro, com entrada em cascata (use `{{LOGO}}` para o logo de `CONFIG["logo"]`) |
| `("semCapa",)` | esconde a capa |
| `("espera", segundos)` | segura a tela parada |

Na fala, `capa="abertura"` sem `acao` mostra a capa no começo da fala (usado na primeira e na última).

## Classes prontas para capas
- `.vt-capa` (fundo escuro, `img` = logo, `.k` = etiqueta, `h1`, `p`, `.linha`, `ol`).
- `.vt-plan-f` + `.vt-plan` (quadro branco de planilha; `td.am` amarelo = preencher, `td.vd` verde = automático,
  `td.cz` cinza = base; `.leg` legenda; `.pasta` caminho).

## CONFIG: chaves além das básicas
- `"logo"`: caminho de um PNG (relativo à pasta do vídeo) para `{{LOGO}}` nas capas. Sem ele, usa `motor/arte/logo.png` se existir.
- `"raiz"`: elemento que recebe o zoom (`.app`, `body`...). As peças do vídeo ficam fora dele, no `<html>`.
- `"init_script"`: código que roda antes da página carregar (ex.: marcar tutorial e capa como vistos).
- `"janela"` + `"densidade"`: use o mesmo tamanho dos prints de referência da ferramenta (ex.: 1366 × 768 com 1,875 → 2560 × 1440).
- `"esperar_ms"`: tempo para a página carregar antes de começar.
- `"passo_na_legenda": True`: o passo ("3 · Abas") aparece dentro da caixa da legenda, em vez da etiqueta no topo. Use quando a
  ferramenta tem abas ou botões no topo da tela: assim a etiqueta nunca cobre nada.
