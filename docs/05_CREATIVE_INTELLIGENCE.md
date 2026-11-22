# Creative Intelligence — engenharia reversa criativa e avaliação pré-publicação

Versão 1.0 (biblioteca em `creative-intelligence/`, tag `ci-v1.0.0`). Duas capacidades, três responsabilidades separadas:

| Responsabilidade | O que entra | O que sai | Ferramenta |
|---|---|---|---|
| 1. Pesquisa e engenharia reversa | vídeos de alto desempenho de outros criadores (metadados oficiais, arquivo legítimo, observação) | hipóteses e padrões transferíveis (`CREATIVE_INTELLIGENCE_BRIEF.md`) | skill `engenharia-reversa` |
| 2. Produção | o brief + o roteiro aprovado | vídeo **original** | skills `roteirista` e `gerador-de-video` (o motor não depende da biblioteca) |
| 3. Pré-publicação e analytics | o NOSSO vídeo pronto | QA editorial, comparação A/B, predição opcional, métricas reais | `ci comparar`, `ci prever`, `ci avaliacao`, `ci experimento` |

## Quando usar cada uma

| Tipo de vídeo | Engenharia reversa | Virality Predictor |
|---|---|---|
| Curiosidade, Reels, Shorts, TikTok | sim: gancho e retenção narrativa | opcional, depois do QA, com autorização |
| YouTube longo | sim, na estrutura por capítulos (não esticar roteiro) | só para o gancho (a janela é de ~15 s) |
| Anúncio / campanha | sim, para mensagem e criatividade | opcional; a métrica final é comercial (leads, vendas), não views |
| Tutorial ou vídeo técnico | não é necessária | não é necessária |

## O que cada ferramenta mede — e o que NÃO comprova

| Ferramenta | Mede | Não comprova |
|---|---|---|
| Análise técnica (`ci analisar`) | cortes aproximados, duração dos planos, mudanças visuais, movimento, cor/contraste, intensidade e pausas do áudio, quadros de referência | retenção, desempenho, o que causou o sucesso |
| Brief (`ci brief`) | organiza fatos observados, métricas com fonte e hipóteses com confiança | causa: views altas + uma característica = correlação |
| Comparação A/B (`ci comparar`) | diferenças técnicas de duas aberturas nossas na mesma janela | que uma versão retém mais |
| Virality Predictor (Higgsfield) | estimativa de um modelo para um trecho (~15 s) | probabilidade de viralizar (90/100 ≠ 90% de chance); qualidade do vídeo inteiro |
| Métricas reais (`ci experimento`) | o que aconteceu na plataforma (com fonte e data) | o porquê — só comparando experimentos |

Quatro camadas que nunca viram uma nota única: **QA técnico** (testes objetivos do motor), **QA editorial** (revisão por dimensão),
**predição** (estimativa de modelo), **resultado real** (plataforma).

## Fontes de pesquisa permitidas
- **YouTube Data API v3** (oficial, chave de quem usa): `ci referencia youtube <url>` e a ferramenta `pesquisa_youtube.py`.
- **YouTube Analytics**: só para canais autorizados (dono do canal); importar como entrada manual ou integração oficial futura.
- **vidIQ**: sem API aberta. Se houver um MCP do vidIQ conectado ao Claude Code, use; senão, cole os números com a fonte
  (`ci modelo entrada_manual`). Não presuma que uma integração disponível em outro assistente existe aqui.
- **TikTok Creative Center / Instagram**: só dados públicos copiados à mão, com a fonte.
- **Arquivos de vídeo**: somente os que você tem direito de analisar (seus, licenciados ou fornecidos pelo dono).
- Proibido: scraping, cookies de sessão, contornar bloqueio, baixar vídeo de terceiros, subir vídeo de terceiros no repositório.

## Higgsfield Virality Predictor — ativar com controle de custo
1. **Instalar a CLI** (com sua aprovação; é um programa externo): `npm install -g @higgsfield/cli` (Windows/Mac/Linux) ou
   `brew install higgsfield-ai/tap/higgsfield` (Mac). Conferir: `higgsfield version`.
2. **Entrar**: `higgsfield auth login` (interativo, no seu terminal). A biblioteca só pergunta se há sessão; nunca lê token.
3. **Conferir**: `py creative-intelligence/ci.py verificar` (CLI e sessão) e `higgsfield account` (créditos).
4. **Preparar sem enviar**: `ci prever VIDEO --provedor higgsfield --projeto P --saida PASTA --modelo-autorizacao` recorta a
   abertura (até 15 s, com áudio), confere integridade, tenta estimar o custo **sem** mandar o vídeo e cria
   `autorizacao_envio.json` com tudo negado.
5. **Autorizar**: o dono do material revisa e preenche a autorização (sha256 do clipe, direitos, envio externo permitido, sem dados
   pessoais, orçamento máximo de créditos, quem aprovou e quando). Material `interno`/`confidencial` ou com dados pessoais nunca vai.
6. **Enviar**: `ci prever ... --autorizacao autorizacao_envio.json --enviar`. Registra só os campos que o provedor devolveu, o link do
   relatório e o custo informado. A CLI sobe o arquivo de `--video`; por isso a estimativa de custo com o vídeo também conta como envio.

## Interpretar resultados
- A janela analisada (ex.: 0–15 s de um vídeo de 47 s) vale só para aquele trecho; o relatório diz isso.
- Score maior entre duas versões é hipótese a testar, não vitória: publique, meça e compare (`ci experimento`).
- Não use nenhuma nota como condição obrigatória para publicar.

## Proteger material privado
- Política por repositório (`ci_politica.json`): classificação padrão e caminhos que nunca saem (ex.: tutoriais de sistemas internos).
- Autorização por arquivo (sha256) e provedor; material de cliente exige a autorização do cliente registrada.
- Relatórios guardam só o nome do arquivo (não o caminho), e removem tokens, e-mails e chaves do retorno do provedor.
- Este repositório é **público**: nunca suba relatórios de material privado, autorizações, tokens, vídeos de clientes ou de terceiros.

## Comparar com dados reais
```
ci experimento novo --id exp-001 --projeto canal --titulo "Por que X?" --versao v2 --gancho pergunta --saida exp.json
ci experimento publicar exp.json --plataforma instagram --data 2026-12-01 --url https://...
ci experimento metricas exp.json --plataforma instagram --de metricas.csv --fonte "painel do Instagram, export 2026-12-08"
ci experimento relatorio exp.json
```
O CSV tem as colunas `metrica,valor` (ex.: `visualizacoes`, `retencao_media_pct`, `tempo_medio_assistido_s`, `compartilhamentos`,
`salvamentos`, `seguidores_ganhos`; campanha: `cliques`, `leads`, `conversoes`, `custo_por_lead`, `receita`). Valor vazio = não informado.

## Pedidos típicos ao Claude Code
- "Faz a engenharia reversa deste vídeo que eu gravei (arquivo X) e me dá o brief." → `engenharia-reversa`.
- "Pesquisa os curtos mais vistos sobre gatos e transforma os 3 melhores em brief." → `pesquisa-viral` → `engenharia-reversa`.
- "Compara o gancho da versão 1 com a 2." → `ci comparar`.
- "Prepara a avaliação do gancho na Higgsfield, mas não envia." → `ci prever ... --modelo-autorizacao`.

## Reuso entre projetos (decisão)
A biblioteca mora neste repositório público porque é genérica e segura. Outros projetos instalam **a mesma versão** pela tag
(`pip install "... @ git+https://github.com/scamposgabriel/gerador-de-videos@ci-v1.0.0#subdirectory=creative-intelligence"`)
como dependência **opcional**: nenhum motor precisa dela para renderizar, e cada projeto mantém um adaptador fino com a sua
política de privacidade. Alternativas descartadas: copiar o código (três cópias divergindo), submódulo Git (acopla o histórico)
e um quarto repositório (mais manutenção sem ganho nesta escala). Nova versão = nova tag (`ci-v1.1.0`); projetos atualizam quando quiserem.
