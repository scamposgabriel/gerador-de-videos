# Gerador de Vídeos — instruções para o Claude Code

Responda sempre em português. Este repositório é um **pacote de skills** (em `.claude/skills/`) com um motor de vídeo (`motor/`):

| Skill | Para quê |
|---|---|
| `pesquisa-viral` | vídeos mais vistos do YouTube por tema ou canal → ideias originais |
| `roteirista` | roteiro + storyboard + título, capa e legenda do post |
| `gerador-de-video` | grava o vídeo (Reels animado ou tutorial), capa e controle de qualidade |

## Pedido típico: "faz um vídeo sobre <tema>"
1. Se o usuário quiser saber o que funciona, `pesquisa-viral` (pergunte antes: gasta cota da chave dele).
2. `roteirista`: roteiro e storyboard. **Mostre e espere aprovação.**
3. `gerador-de-video`: copie `videos/exemplo-bolinha-vermelha` para `videos/<nome>`, escreva o roteiro, adapte as cenas,
   confira por fotos, grave, gere a capa e verifique os textos.
4. Entregue os caminhos dos arquivos e diga o que a pessoa precisa **ouvir** para aprovar. Nunca publique nada.

## Regras
- O motor (`motor/`) é comum a todos os vídeos. Mudança nele: teste no exemplo (`--fotos` e vídeo inteiro com QA aprovado) e
  descreva o que mudou e como validar.
- Não altere `videos/exemplo-bolinha-vermelha` para fazer um vídeo novo: copie.
- Nunca coloque chave, senha ou dado de cliente em arquivo do repositório nem no texto falado.
- Primeiro uso numa máquina: confira `py --version`, `ffmpeg -version` e `py -m pip install -r requirements.txt` (ver README).
