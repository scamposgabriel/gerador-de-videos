---
name: gerador-de-video
description: Grava vídeos narrados em português, nítidos e sem custo, a partir de um roteiro. Modo animado (Reels/TikTok/Shorts 1080 x 1920 com personagem, legenda palavra por palavra, câmera sempre andando, trilha e efeitos, capa e controle de qualidade) e modo tutorial (grava uma página web real com cursor, zoom e destaque, 2560 x 1440). Use quando pedirem para fazer, gravar, montar, ajustar ou revisar um vídeo, Reels, capa, ou para transformar um roteiro em vídeo.
---

# Gerador de Vídeos

Responda em português. Texto de tela e narração sem jargão. Antes de um vídeo novo, leia `docs/04_VIDEO_ANIMADO.md` (animado)
ou `docs/01` e `docs/02` (tutorial), e `docs/03_QUALIDADE_E_CHECKLIST.md`.

## Fluxo de um vídeo animado (o mais pedido)
1. **Roteiro aprovado.** Se não houver, use a skill `roteirista` e mostre o roteiro + storyboard ao usuário antes de gravar.
2. **Copie o modelo**: `videos/exemplo-bolinha-vermelha` → `videos/<nome-curto-do-video>` (pasta nova; nunca altere o exemplo).
3. **roteiro.py**: troque `FALAS` (uma fala = uma cena, `cena="nome"`), `MARCA` (nome do canal, avatar) e, se houver, `PERSONAGEM`
   (pasta com PNGs das poses). Ajuste `saida` e `saida_so_voz`.
4. **pagina.html**: para cada cena, uma função `cNome(r, c)` registrada em `MONTA`. Reaproveite as peças do modelo:
   `quando(cena, "palavra")` (instante em que a voz fala a palavra), `entra()` (entrada sincronizada), `sai()`, `anim()`,
   `personagem()` (troca de pose na palavra certa; objetos na mão via `.extra`), `bola()`/`bolaDiv()`, `jardim()`, `cachorro()`, `som()`, cartão final (`montarFim`) e
   capa (`montarCapa`, desenhada em `render(t < 0)`). Cores em `--fundo`, `--tinta`, `--destaque`.
5. **Confira antes de gravar tudo**: `py motor/animar.py videos/<pasta> --fotos 0,3,8,15` (PNG na resolução real em `saida/fotos`)
   e monte uma folha para olhar cena por cena. Teste com som: `--ate 12`.
6. **Grave**: `py motor/animar.py videos/<pasta>`. Sai o MP4 com música, a versão "só voz" e `saida/controle_de_qualidade.json`
   (QA automático: resolução, FPS, imagem parada > 1 s, quadros repetidos, tela preta, volume -14 LUFS, pico).
7. **Capa**: `py ferramentas/capa.py videos/<pasta>` → `saida/Capa.png`.
8. **Textos**: `py ferramentas/verificar_textos.py videos/<pasta>` (texto cortado, fora da tela ou embaixo dos botões do Instagram).
9. **Entregue** os caminhos dos arquivos e diga o que a pessoa precisa conferir **ouvindo** (você não ouve áudio). Nunca publique.

Folha de quadros (a cada 2 s): `ffmpeg -i saida/<video>.mp4 -vf "fps=1/2,scale=240:427,tile=9x3" -frames:v 1 folha.png`.

## Modo tutorial (página web real)
Copie `modelos/roteiro_modelo.py` para `videos/<pasta>/roteiro.py`; ações em `docs/02_ACOES_DO_ROTEIRO.md`.
Teste `py motor/gravar.py videos/<pasta> --so 02-04`; depois o vídeo inteiro.

## Regras que já custaram caro (não repetir)
- `render(t)` depende **só** de `t` (nada guardado do quadro anterior); paradas de degradê sempre em ordem.
- **Nunca congelar**: câmera sempre andando (aproximação lenta + deriva); clipe que acaba volta de trás para frente; cartão final se mexe.
- **Ação no 1º quadro**: o primeiro segundo já mostra o mistério (nada de cenário vazio esperando).
- Reels (1080 × 1920): título entre 150 e 440 px; legenda em ~1330 px com no máximo ~16 letras por bloco (trava de 860 px);
  nada importante abaixo de 1600 px nem à direita (x > 960) entre 1100 e 1750 px — botões e descrição do Instagram.
- O objeto da demonstração tem que ser **grande**: aproxime a câmera; grama/elementos na frente só na base do objeto.
- Comparação "antes × depois" com o mesmo enquadramento nos dois quadros; transição visível entre eles (ex.: varredura).
- Em pé, nada de faixa horizontal no meio; clipe horizontal entra recortado em pé (ampliação máx. ~1,2×).
- PNG de personagem: confira se o fundo é transparente de verdade (5% de cor vira retângulo no vídeo).
- Zoom proposital pode tirar texto da tela por < 0,5 s; fora isso, o verificador de textos deve sair limpo.
- Não use o screencast do navegador nem o vídeo do Playwright (saem embaçados); o motor fotografa quadro a quadro.
- Caminho do Windows em `roteiro.py` sempre como `r"..."`.
- Voz: frases curtas; o `vozes.py` gera frase por frase com respiro (`voz["respiro"]`). Ritmo natural 2,4 a 3,2 palavras/s
  (o motor mostra a duração; palavras ÷ segundos).
- Clipes de banco de imagem: só licença que permita o uso (Mixkit "Free"; "Restricted" proíbe anúncio); registre em `midia/CREDITOS.md`.

## Segurança
- A fala vai para um serviço externo (Edge TTS ou ElevenLabs): nunca ponha nome, CPF ou dado de cliente no texto falado.
- Chaves só em `~/.secrets/` (ElevenLabs: `~/.secrets/elevenlabs/.env`); nunca imprimir, nunca copiar para o repositório.
- Simulação ou personagem fictício: rotule na tela ("simulação aproximada", "personagem fictício").
- Não gaste crédito de API pago sem o usuário aprovar.
