# Gerador de Vídeos com IA (skills para o Claude Code)

Faça **Reels, Shorts e TikToks narrados em português** — com personagem, legenda palavra por palavra, câmera sempre em movimento,
trilha e efeitos — só pedindo para o Claude Code. Sem programa de edição, sem custo por vídeo e com controle de qualidade automático.

> "Pesquisa os vídeos mais vistos sobre curiosidades de cachorro, escolhe uma ideia, escreve o roteiro e faz o vídeo."

São quatro skills que trabalham juntas:

| Skill | O que faz |
|---|---|
| **pesquisa-viral** | busca os vídeos mais vistos do YouTube por tema ou canal (API oficial) e mostra quais ficaram "fora da curva" |
| **engenharia-reversa** | disseca vídeos de alto desempenho (gancho, mapa temporal, ritmo, o que não copiar) e entrega um *Creative Intelligence Brief*; compara ganchos e prepara a avaliação preditiva opcional |
| **roteirista** | escreve o roteiro com gancho, storyboard cena a cena, título, texto da capa e legenda do post |
| **gerador-de-video** | grava o vídeo 1080 × 1920 (e a versão sem música), a capa e confere a qualidade |

Também grava **tutoriais** de páginas web reais (cursor, zoom e destaque, em 2560 × 1440).

Exemplo incluído: `videos/exemplo-bolinha-vermelha` — "Por que seu cachorro perde uma bolinha vermelha na grama?" (48 s).

---

## 1. Instalar (uma vez)

Testado no **Windows 11**. Com estas versões o resultado sai igual ao nosso:

| Item | Versão testada | Como instalar / conferir |
|---|---|---|
| Python | 3.14.6 | [python.org](https://www.python.org/downloads/) (marque "Add to PATH"). Conferir: `py --version` |
| ffmpeg | 9.0.2 | [ffmpeg.org/download](https://ffmpeg.org/download.html) (no Windows, o build "full" do gyan.dev) e coloque a pasta `bin` no PATH. Conferir: `ffmpeg -version` |
| Microsoft Edge | 158 | já vem no Windows (o motor fotografa as páginas com ele) |
| Bibliotecas Python | playwright 1.62.0, edge-tts 7.3.1, numpy 2.5.2 | `py -m pip install -r requirements.txt` |
| Claude Code | — | [claude.com/claude-code](https://claude.com/claude-code) |

```
git clone <endereço deste repositório>
cd <pasta do repositório>
py -m pip install -r requirements.txt
```

Teste o motor gravando o exemplo (leva uns 5 minutos; a voz é gerada na hora, de graça):
```
py motor/animar.py videos/exemplo-bolinha-vermelha
```
O vídeo sai em `videos/exemplo-bolinha-vermelha/saida/`, com o relatório `controle_de_qualidade.json` (deve dizer APROVADO).

## 2. Usar com o Claude Code (o jeito fácil)

Abra o terminal **dentro da pasta do repositório** e rode `claude`. As skills ficam em `.claude/skills/` e o Claude as encontra
sozinho. Depois é só pedir:

- "Faz um Reels sobre por que o gato derruba coisas da mesa."
- "Pesquisa os vídeos mais vistos do canal @algumcanal e me dá 5 ideias originais."
- "Escreve um roteiro de 50 segundos sobre por que o céu é azul, com gancho forte."
- "Grava o vídeo com esse roteiro e gera a capa."
- "Troca o nome do canal para Ciência em 1 Minuto e as cores para verde."

O Claude mostra o roteiro para você aprovar antes de gravar e, no fim, entrega os arquivos e o que você precisa conferir ouvindo.
Ele nunca publica nada sozinho.

## 3. Usar na mão (sem o Claude)

```
py motor/animar.py videos/<pasta> --fotos 0,5,12      fotos de conferência na resolução real (saida/fotos)
py motor/animar.py videos/<pasta> --ate 12            teste com som dos primeiros 12 s
py motor/animar.py videos/<pasta>                     vídeo inteiro + versão "só voz" + controle de qualidade
py ferramentas/capa.py videos/<pasta>                 capa do Reels (saida/Capa.png)
py ferramentas/verificar_textos.py videos/<pasta>     texto cortado ou embaixo dos botões do Instagram
py ferramentas/pesquisa_youtube.py tema "assunto"     vídeos mais vistos de um tema (precisa da chave, ver abaixo)
py motor/qa.py <video.mp4>                            controle de qualidade de qualquer MP4
```

Para um vídeo novo: copie `videos/exemplo-bolinha-vermelha` para `videos/<nome>` e edite o `roteiro.py` (falas, nome do canal,
personagem) e as cenas da `pagina.html`. Detalhes em `docs/04_VIDEO_ANIMADO.md`.

## 4. Personalizar
- **Nome do canal**: `MARCA = dict(nome="...", avatar="caminho/da/imagem.png")` no `roteiro.py`.
- **Personagem**: o exemplo usa o **Lumi** (desenhado em código). Para usar o seu, ponha PNGs transparentes das poses e configure
  `PERSONAGEM` no `roteiro.py` (ver o comentário lá e `docs/04_VIDEO_ANIMADO.md`).
- **Cores**: variáveis `--fundo`, `--tinta` e `--destaque` no começo da `pagina.html`.
- **Voz**: `voz` no `CONFIG` (vozes testadas em `vozes/CATALOGO.md`).

## 5. Chave da pesquisa do YouTube (opcional, gratuita)
A skill `pesquisa-viral` usa a **YouTube Data API v3**. Crie a chave em [console.cloud.google.com](https://console.cloud.google.com)
(projeto → ativar "YouTube Data API v3" → Credenciais → Chave de API) e salve em `C:\Users\<você>\.secrets\youtube\.env` com a linha
`YOUTUBE_API_KEY=sua_chave`. Passo a passo e limites diários em `.claude/skills/pesquisa-viral/SKILL.md`.
Nunca coloque a chave dentro do repositório.

## 6. Creative Intelligence (opcional)
Biblioteca em `creative-intelligence/` (só Python padrão + ffmpeg; nada a instalar): engenharia reversa técnica e editorial,
*brief* para o roteirista, comparação A/B de ganchos, QA editorial, registro de experimentos com métricas reais e integração
**opcional** com o Virality Predictor da Higgsfield (nada é enviado sem autorização e orçamento). O motor não depende dela.
```
py creative-intelligence/ci.py verificar
py creative-intelligence/ci.py analisar videos/<pasta>/saida/<video>.mp4 --saida pesquisas/ci/<nome>
```
Guia: `docs/05_CREATIVE_INTELLIGENCE.md`. Testes: `py -m pip install pytest` e `py -m pytest creative-intelligence/tests`.

## 7. Pastas

| Pasta | O que tem |
|---|---|
| `.claude/skills/` | as quatro skills (`pesquisa-viral`, `engenharia-reversa`, `roteirista`, `gerador-de-video`) |
| `creative-intelligence/` | biblioteca de engenharia reversa e pré-publicação (com testes e exemplos sintéticos) |
| `motor/` | `animar.py` (Reels), `gravar.py` (tutorial), `camada.js`, `vozes.py` (narração), `trilha.py` (música e efeitos), `qa.py` |
| `ferramentas/` | `capa.py`, `verificar_textos.py`, `pesquisa_youtube.py` |
| `videos/` | um vídeo por pasta; `exemplo-bolinha-vermelha` é o modelo |
| `docs/` | guias: tutorial, ações, qualidade, modo animado, Creative Intelligence |
| `modelos/` | roteiro de tutorial comentado |
| `vozes/` | catálogo de vozes testadas |

## 8. Cuidados
- A narração usa o Edge TTS pela biblioteca `edge-tts`, que **não é uma API oficial** da Microsoft e pode mudar sem aviso.
  O texto falado vai para esse serviço: nunca ponha dado de cliente ou de outra pessoa na fala.
- Simulações e personagens fictícios vão rotulados na tela.
- Clipes de banco de imagens não vêm no repositório; use só os de licença que permita o seu uso.
- Engenharia reversa: só analise arquivos que você tem direito de usar; nunca baixe nem suba vídeos de outros criadores.
  Avaliação preditiva externa (Higgsfield) envia o clipe para fora e gasta créditos: só com a sua autorização.

## Colaborar
Ver [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licença
[MIT](LICENSE).
