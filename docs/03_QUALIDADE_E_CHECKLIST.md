# Qualidade e checklist

## Padrão técnico (o motor já entrega)
| Item | Padrão |
|---|---|
| Resolução | 2560 × 1440 (janela 1600 × 900, densidade 1,6) |
| Quadros | 30 por segundo, relógio próprio (liso em qualquer máquina) |
| Vídeo | H.264, CRF 17, `yuv420p`, faixa TV, BT.709, `+faststart` (abre rápido no Teams e no navegador) |
| Áudio | AAC 160 kbps, 48 kHz, volume normalizado (-16 LUFS) |
| Tamanho típico | ~13 MB por minuto |

## Conferir antes de entregar
1. **Teste curto primeiro** (`--so`), com uma cena de zoom e texto pequeno.
2. **Nitidez na resolução real**: extraia quadros e recorte um pedaço com texto, inclusive no meio de um zoom:
   `ffmpeg -ss 20.5 -i saida/teste.mp4 -frames:v 1 -vf "crop=1100:500:700:400" recorte.png`
3. **Folha de quadros** do vídeo inteiro para ver se cada cena mostra o que a legenda diz:
   `ffmpeg -i saida/video.mp4 -vf "fps=1/11,scale=640:-1,tile=4x7" -frames:v 1 folha.png`
4. **Sincronia**: a legenda e a voz entram juntas; a ação da tela acompanha a fala.
5. **Ouvir o áudio inteiro** (uma pessoa): pronúncia das siglas, volume, cortes.
6. **Dados**: a tela mostra só o que o público pode ver; o texto falado não tem dado de cliente.
7. **Duração**: 3 a 5 minutos; se passar, corte falas.
8. Assistir no lugar onde vai ser visto (Teams, navegador) antes de mandar.

## Lição do primeiro tutorial (19/11/2026)
- Versão 1: screencast do navegador esticado de 1600 × 900 para 1080p → texto mole; voz do Windows robótica. Reprovada.
- Versão 2: quadro a quadro em QHD, zoom redesenhando o texto, voz Edge Antonio. Aprovada.

## Narração natural (feedback do Gabriel, 20/11/2026)
Sobre um vídeo tutorial: "quando ela fala a sigla ela fala pausadamente e tem coisas que ela acelera muito,
parece que não tem vírgula e não respira, fica na cara que é IA".
- **Frases curtas**: até ~15 palavras, uma ideia por frase. Lista com no máximo 3 itens.
- **Vírgula onde se respira**; ponto final separa ideias. O `vozes.py` gera o Edge frase por frase e cola com 320 ms de respiro.
- **Sigla**: troque pelo nome ("estação de tratamento") ou escreva como se fala numa palavra só e teste numa amostra.
  Soletrada com espaços ("í bê gê é") sai pausada, sílaba por sílaba.
- **Ritmo**: 2,4 a 3,2 palavras por segundo é natural. Acima disso, divida a frase.

## Controle de qualidade automático (21/11/2026)
O `motor/animar.py` roda `motor/qa.py` no fim e só dá APROVADO sem: imagem parada acima de 1 s, tela preta, erro de decodificação, resolução/FPS
errados ou pico de áudio estourado. Avisos (não reprovam): texto < 26 px, volume fora de -16,5 a -12,5 LUFS, cartão final < 2,5 s, muitos quadros
repetidos. Relatório: `saida/controle_de_qualidade.json`. Para vídeos antigos: `py motor/qa.py <arquivo.mp4>`.
