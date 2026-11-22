---
name: engenharia-reversa
description: Engenharia reversa criativa de vídeos de alto desempenho - investiga gancho, primeiros 3 segundos, construção da curiosidade, estrutura, revelações, cortes, cor, texto, enquadramento, animação, áudio e encerramento, separa fato, métrica verificada e hipótese, e entrega um CREATIVE_INTELLIGENCE_BRIEF com técnicas transferíveis, o que não copiar e recomendações para um roteiro ORIGINAL. Também compara dois ganchos nossos e prepara a avaliação preditiva opcional (Higgsfield Virality Predictor) com controle de custo e autorização. Use quando pedirem para estudar por que um vídeo funcionou, dissecar uma referência, aprender o padrão de um viral, comparar versões de abertura ou avaliar um gancho antes de publicar.
---

# Engenharia reversa criativa

Responda em português. A saída é **inteligência criativa**, nunca um roteiro copiado. Ferramentas: `creative-intelligence/`
(sem instalar: `py creative-intelligence/ci.py ...`). Guia: `docs/05_CREATIVE_INTELLIGENCE.md`.

Fluxo: `pesquisa-viral` → **`engenharia-reversa`** → `roteirista` → `gerador-de-video` → (opcional) avaliação pré-publicação.

## 0. Precisa mesmo?
Tutorial ou vídeo técnico: não. Curiosidade/Reels/Shorts/TikTok: sim (gancho e retenção). YouTube longo: estrutura por capítulos.
Anúncio: mensagem e criatividade; o sucesso se mede em resultado comercial, não em views.

## 1. Referência e métricas (cada número com fonte)
- YouTube: `py creative-intelligence/ci.py referencia youtube <url> --tema "..." --saida pesquisas/ci/<id>/referencia.json`
  (gasta cota da chave do usuário; pergunte antes). Para achar candidatos, use antes a `pesquisa-viral`.
- vidIQ: confira se há uma ferramenta MCP do vidIQ conectada nesta sessão. Se não houver, diga isso e peça os números colados;
  grave com `ci modelo entrada_manual` → `ci referencia manual`. O mesmo para TikTok Creative Center e painel do Instagram.
- Nunca invente métrica. O que faltar aparece em "dados indisponíveis".

## 2. Análise técnica (só com arquivo legítimo)
Somente arquivos que o usuário tem direito de analisar (próprios, licenciados ou enviados pelo dono). **Não baixe vídeos de
terceiros**, não use cookies, não faça scraping, não suba vídeo de terceiros no repositório.
`py creative-intelligence/ci.py analisar <video> --saida pesquisas/ci/<id>` → `analise_tecnica.json` + `quadros/`.
Olhe os quadros de referência (abertura 0/1/3 s, cortes, meio, fim). As medidas são do arquivo: não são retenção.

## 3. Análise editorial (quem assistiu escreve, com tempo e evidência)
`ci modelo observacoes_editoriais --saida pesquisas/ci/<id>/observacoes.json` e preencha:
- **Abertura**: primeira imagem, primeira fala, promessa/pergunta, elemento de curiosidade, tempo até o assunto.
- **Desenvolvimento**: ritmo, progressão, revelações (quando), mudanças visuais, humor, comparações, suspense.
- **Conclusão**: resolução, recompensa, encerramento, convite à interação, repetição natural.
- Estilo visual, animação que explica, áudio; técnicas transferíveis; **o que é identidade do outro criador** (não copiar).
- Hipóteses sobre o desempenho com confiança (baixa/média/alta) e base. **Correlação não é causa.**
Cada item é `fato_observado`, `metrica_verificada` ou `hipotese`. Sem acesso ao vídeo (só título/descrição/transcrição colada),
diga isso: a confiança cai para baixa. "PREENCHER" bloqueia o brief até ser trocado.

## 4. Brief
`ci brief --referencia ... --observacoes ... --analise ... --saida pesquisas/ci/<id>` → `CREATIVE_INTELLIGENCE_BRIEF.md` + JSON.
Entregue ao `roteirista`: 3 ganchos originais, progressão, demonstrações visuais, ritmo, riscos de originalidade e estratégia.

## 5. Depois do vídeo pronto (opcional)
- **A/B de ganchos nossos**: `ci comparar v1.mp4 v2.mp4 --hipotese "o que mudou e por quê" --rotulos v1,v2 --saida ...`.
  Não declare vencedora: é hipótese até a métrica real.
- **Virality Predictor (Higgsfield)**: primeiro `ci verificar`; depois `ci prever <video> --provedor higgsfield --projeto ...
  --modelo-autorizacao` (prepara o clipe de até 15 s e NÃO envia). Mostre o custo/créditos ao usuário e **peça aprovação**.
  Só com a autorização preenchida pelo dono: `--autorizacao ... --enviar`. Nunca envie material interno, de cliente sem
  autorização do cliente, com dados pessoais ou telas de sistemas. Pontuação não é probabilidade de viralizar.
- **QA editorial**: `ci avaliacao modelo <video> --avaliador ... --saida ...` (dimensões separadas, sem nota única).
- **Resultado real**: `ci experimento ...` depois de publicar (métricas com fonte e data).

## Não faça
Copiar roteiro, frase, personagem, arte ou sequência de planos; prometer que algo vai viralizar; apresentar medida técnica
como retenção; gastar crédito sem aprovação; colocar material privado neste repositório público.
