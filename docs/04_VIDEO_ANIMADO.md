# Vídeo animado (Instagram, explicativo) — `motor/animar.py`

Nasceu em 20/11/2026 para testar vídeos de Instagram.
Exemplo completo: `videos/exemplo-bolinha-vermelha` (personagem Lumi + desenho em SVG, capa e cartão final).

## Como funciona
- A pasta do vídeo tem `roteiro.py` (CONFIG + FALAS) e `pagina.html` (o desenho).
- O motor gera a voz de cada fala (frase por frase, com respiro) e o **tempo de cada palavra** (`<id>.palavras.json`).
- Monta a linha do tempo: `intro` → fala 1 → `folga` → fala 2 … → `fim`. Cada fala é uma **cena** (`cena="captacao"` etc.).
- Abre a página no Edge (1080 × 1920, densidade 2 = 2160 × 3840), chama `iniciar(TL)` e, para cada quadro, `render(t)` + foto.
  As fotos vão direto para o ffmpeg (nada em disco), reduzidas para 1080 × 1920 com lanczos: borda lisa e texto firme.
- Som: voz + efeitos (whoosh, pop, plim, splash, bolha) + trilha suave sintetizada (`motor/trilha.py`), que abaixa sozinha quando a voz
  fala. Volume final -14 LUFS (padrão do Instagram). Sai também uma versão **sem música** (`saida_so_voz`) para pôr música do próprio Instagram.

## O que a página precisa ter
| Função | O que faz |
|---|---|
| `async iniciar(TL)` | recebe `{cenas: [{id, cena, ini, fim, dur, fala, palavras: [{t, d, w}]}], total}`, monta o desenho e devolve a lista de sons `[{t, som, vol, nota, dur, pan}]` |
| `render(t)` | desenha o instante `t` (segundos). **Só pode depender de `t`**: assim qualquer trecho é refeito igual |

Dicas que o exemplo usa (copie de lá):
- `quando("cena", "palavra")` devolve o instante em que a voz fala aquela palavra: etiquetas, ícones e checks entram **na palavra**.
- Câmera por quadros-chave (`KCAM`) com suavização; borrão de movimento só nas passagens rápidas.
- Legenda palavra por palavra: blocos de até 4 palavras, a palavra falada em amarelo; sem palavra sozinha no fim da frase.
- Zonas seguras do Reels: título entre 150 e 440 px, legenda em ~1350 px; nada importante abaixo de 1600 px nem colado na direita (botões do app).
- Primeiro quadro = capa do Reels: já com título e a cena principal.

## Comandos
```
py motor/animar.py videos/<pasta> --fotos 0,6,20,45     fotos PNG desses instantes (saida/fotos) — confira o desenho primeiro
py motor/animar.py videos/<pasta> --ate 13              teste com som dos primeiros 13 s
py motor/animar.py videos/<pasta>                       vídeo inteiro (+ versão sem música)
```
Velocidade medida: ~0,2 s por quadro (um vídeo de 72 s leva ~8 minutos).

## Roteiro de Instagram (o que funcionou)
- 60 a 75 s; gancho com pergunta no primeiro segundo; uma etapa por fala; fecho com a mensagem; gancho para o próximo vídeo.
- Frases curtas, uma ideia por frase, nada de sigla soletrada (ver `docs/03`, narração).
- Personagem simples que muda junto com a história (ex.: o Zé trocando de pose na palavra certa) segura a atenção melhor que só diagramas.

## Estilo propaganda (Reels de venda)
- **Legenda é o design**: 1 a 3 palavras por vez, Montserrat 900 em caixa alta com contorno preto, cada palavra entra quando é falada
  (pulo pequeno, 1,22 → 1; maior que isso as palavras se encostam). Palavra-chave positiva em amarelo, negativa em vermelho.
- **Uma cor e um ícone por argumento**; troca de cena com varredura diagonal + whoosh; tremor de câmera nos impactos (`impacto(t, força)`).
- Ícones "adesivo": filtro SVG `adesivo` (borda branca + sombra) em qualquer grupo desenhado.
- Trilha `trilha_estilo="batida"` (bumbo, palma, chimbal, baixo e acordes curtos; `bpm`). Efeitos novos: `kaching`, `carimbo`, `vidro`, `subida`.
- Dados do roteiro para a página: qualquer variável em MAIÚSCULAS do `roteiro.py` (ex.: `CARTAO`) chega em `TL.dados`.
- Capa (primeiro quadro) com frase de impacto grande; chamada final para comentar uma palavra (gera comentário e alcance).

## Estilo premium (referências de Reels bem-sucedidos)
O que as duas referências têm em comum e que o vídeo copia:
- **História com personagem e curiosidade** no gancho ("Como alguém compra à vista sem ter o dinheiro?"), não lista de vantagens.
- **Uma tela por vez**, desenhada como interface de verdade (nota fiscal, celular com notificação, extrato, comentários), em HTML/CSS:
  cartão claro com cantos de 36 px e sombra longa e suave; tudo entra no instante da palavra (`quando()` + `entra()`).
- **Fundo quente** (#F4EFE9) com piso em perspectiva e poeira; paleta de 3 cores (tinta #1E1A17, terracota #B4634F, sálvia #4E7D5E).
- **Legenda elegante**: 1 a 3 palavras, Outfit; palavra falada em negrito escuro, as anteriores em cinza claro; palavras-chave em itálico
  serifado (Newsreader) terracota e sublinhadas.
- **Etiquetas mono numeradas** ("Nº 01 · O GRUPO", JetBrains Mono, caixa escura) — vem do vídeo do corretor.
- **Som como nas referências**: música contínua por baixo da voz (nenhum silêncio), voz comprimida, -14 LUFS. `trilha_estilo="lofi"`,
  `voz_compressor=True`, `duck_ratio=3`. Efeitos de interface: `tique`, `notificacao`, `risco`, `roleta`.
- Final com chamada para comentar uma palavra + nome/função em mono + aviso legal pequeno.
Limite honesto: as referências usam imagem real (drone) ou interface de produto; ilustração desenhada em código fica abaixo de foto/vídeo
real. Para o próximo nível: imagens reais (banco de imagens com licença ou do próprio cliente) por trás da tipografia.

## Estilo cinema com imagem real
- `MIDIA` no roteiro (`{"nome": dict(arquivo="midia/x.mp4")}`): o `animar.py` transforma cada clipe em quadros JPEG a 30 q/s no disco
  local (mais uma versão desfocada em pé para o fundo) e passa para a página em `TL.midia`. A página troca o quadro a cada 1/30 s e
  espera decodificar (`render(t)` assíncrono): sincronia exata, sem depender do player do navegador.
- Clipe 720p NÃO vai em tela cheia em pé (esticaria 2,7×, embaçado). Vai numa **faixa de cinema de 1080 × 608** (até menor que o original),
  com o próprio clipe desfocado de fundo, título editorial em cima e legenda embaixo. Camadas com `z-index` explícito
  (fundo 0, véu 1, faixa 2, cenas 3, legenda 4, final 5): sem isso o vídeo cobre os cartões.
- **Licença (armadilha paga em 21/11/2026):** no Mixkit há "Free" (comercial, anúncio e rede social de empresa liberados) e "Restricted"
  (só uso pessoal: proíbe anúncio e perfil de empresa). A licença aparece na página de cada clipe (`data-license="videoFree"`).
  Conferir clipe por clipe e registrar em `midia/CREDITOS.md`. Pexels e Pixabay bloqueiam download por programa (403).
- Para qualidade máxima: imagem real do próprio cliente (celular em pé, 1080 × 1920) entra em tela cheia, sem faixa.

## Revisão v2 (21/11/2026, crítica do ChatGPT do Gabriel) — regras que valem daqui para frente
- **História antes de benefício**: gancho (dúvida ou situação reconhecível) → personagem com problema concreto → descoberta do produto →
  demonstração → convite. A venda nasce dentro da história. Lista de vantagens com imagens bonitas não segura ninguém.
- **Nada de faixa horizontal no meio da tela em pé.** Vídeo real entra em pé: clipe vertical em cartão ou tela cheia; clipe horizontal
  recortado em pé dentro de celular ou cartão vertical (ampliação de no máximo ~1,2×); fundo em tela cheia só com clipe vertical
  (ex.: fogo).
- **Nunca congelar**: clipe que acaba volta de trás para frente (`quadro()` em vai-e-volta); câmera de cada cena sempre andando (aproximação lenta
  + deriva); o cartão final também se mexe (celular com vídeo, texto flutuando).
- **Controle de qualidade automático** (`motor/qa.py`, roda no fim do `animar.py` e grava `saida/controle_de_qualidade.json`): resolução, FPS,
  decodificação completa, **imagem parada acima de 1 s** (freezedetect a -50 dB, calibrado com o Teste 01), quadros repetidos, tela preta,
  volume (-14 LUFS) e pico; o `animar.py` também avisa texto menor que 26 px e cartão final com menos de 2,5 s. Pausa intencional: `pausas_intencionais`
  no CONFIG. À mão: `py motor/qa.py video.mp4`.
- Personagem fictício com pessoa real de banco de imagens: sem rosto e com "personagem fictícia" escrito (não vira "cliente real").

## Personagem, marca, capa e verificação (21/11/2026)
- **Personagem**: o modelo (`videos/exemplo-bolinha-vermelha`) traz o Lumi, desenhado em SVG. Para usar o seu, ponha PNGs com
  fundo **transparente de verdade**, 941 × 1672, um por pose (`apresentando`, `apontando`, `olha-so`, `pensando`, `rindo`,
  `surpreso`), com a palma direita do "apresentando" perto de (850, 580) e a esquerda perto de (90, 830), e configure
  `PERSONAGEM = dict(pasta="...", prefixo="...")` no roteiro. Fundo com 5% de cor vira um retângulo em volta do personagem.
- **Marca**: `MARCA = dict(nome="Seu Canal", avatar="")` no roteiro (etiqueta do topo, cartão final e capa). Cores da página nas
  variáveis `--fundo`, `--tinta` e `--destaque`.
- **Capa**: a página desenha a capa em `render(t < 0)`; `py ferramentas/capa.py videos/<pasta>` grava `saida/Capa.png`
  (1080 × 1920). Título grande dentro do recorte 3:4 da grade do perfil (de 240 a 1680 px de altura).
- **Textos**: `py ferramentas/verificar_textos.py videos/<pasta>` confere a cada 0,25 s se algum texto ficou cortado, fora da tela
  ou embaixo da interface do Instagram. Legenda com no máximo ~16 letras por bloco e trava de largura de 860 px.
- **Abertura**: a ação começa no 1º quadro (o mistério já acontecendo); o título do gancho dá lugar ao carimbo da virada.
- **Demonstração**: o objeto principal grande e perto da câmera; elementos na frente (grama) só na base dele; os dois lados da
  comparação com o mesmo enquadramento e uma transição visível entre eles.
- **Mixagem**: com `duck_ratio=3`, a música fica ~21 LU abaixo da voz durante as falas (medido no exemplo): a voz fica à frente.
