# Gerador de Vídeos — instruções para o Claude Code

Responda sempre em português. Este repositório é um **pacote de skills** (em `.claude/skills/`) com um motor de vídeo (`motor/`):

| Skill | Para quê |
|---|---|
| `pesquisa-viral` | vídeos mais vistos do YouTube por tema ou canal → ideias originais |
| `engenharia-reversa` | dissecar vídeos de alto desempenho → `CREATIVE_INTELLIGENCE_BRIEF`; A/B de ganchos; predição opcional |
| `roteirista` | roteiro + storyboard + título, capa e legenda do post |
| `gerador-de-video` | grava o vídeo (Reels animado ou tutorial), capa e controle de qualidade |

## Pedido típico: "faz um vídeo sobre <tema>"
1. Se o usuário quiser saber o que funciona, `pesquisa-viral` (pergunte antes: gasta cota da chave dele) e, para estudar
   referências a fundo, `engenharia-reversa` (brief com técnicas transferíveis, o que não copiar e 3 ganchos originais).
2. `roteirista`: roteiro e storyboard. **Mostre e espere aprovação.**
3. `gerador-de-video`: copie `videos/exemplo-bolinha-vermelha` para `videos/<nome>`, escreva o roteiro, adapte as cenas,
   confira por fotos, grave, gere a capa e verifique os textos.
4. Entregue os caminhos dos arquivos e diga o que a pessoa precisa **ouvir** para aprovar. Nunca publique nada.
5. Opcional, depois do QA: QA editorial, comparação de ganchos e avaliação preditiva (Higgsfield) — esta só com aprovação
   de custo e autorização do dono do material. Tutoriais não precisam disso.

## Regras
- O motor (`motor/`) é comum a todos os vídeos. Mudança nele: teste no exemplo (`--fotos` e vídeo inteiro com QA aprovado) e
  descreva o que mudou e como validar.
- Não altere `videos/exemplo-bolinha-vermelha` para fazer um vídeo novo: copie.
- Nunca coloque chave, senha ou dado de cliente em arquivo do repositório nem no texto falado.
- Este repositório é **público**: nada de relatório de material privado, autorização, vídeo de cliente ou de terceiros.
- `creative-intelligence/` é uma biblioteca versionada (tag `ci-vX.Y.Z`) usada também por outros projetos: mudou a interface,
  rode `py -m pytest creative-intelligence/tests`, atualize a versão e crie tag nova (nunca reescreva uma tag publicada).
- Primeiro uso numa máquina: confira `py --version`, `ffmpeg -version` e `py -m pip install -r requirements.txt` (ver README).
