# Creative Intelligence v1.0

Biblioteca de **engenharia reversa criativa** (antes de produzir) e de **avaliação pré-publicação** (depois do vídeo pronto) para
motores de vídeo. Só a biblioteca padrão do Python (3.10+) e o FFmpeg/FFprobe no PATH. Nenhum serviço externo é obrigatório.

| Módulo | Faz |
|---|---|
| `tecnica` | metadados (FFprobe), cortes aproximados, duração dos planos, mudanças visuais, movimento, cor e contraste, áudio (intensidade, pausas, ataques), quadros de referência, abertura/desenvolvimento/conclusão |
| `pesquisa` | metadados de referências com fonte de cada métrica: YouTube Data API (chave de quem usa) ou entrada manual (vidIQ, TikTok Creative Center, painel do Instagram) |
| `brief` | `CREATIVE_INTELLIGENCE_BRIEF.md` + JSON: gancho, mapa temporal, estrutura, técnicas transferíveis, o que não copiar, hipóteses com confiança, dados indisponíveis, recomendações ao roteirista |
| `comparar` | A/B de duas aberturas **próprias** na mesma janela + hipótese da versão B |
| `preditivo` | interface de provedor preditivo; `HiggsfieldViralityProvider` (CLI oficial, job `brain_activity`) e `ProvedorSimulado` |
| `autorizacao` | nada é enviado para fora sem autorização escrita para aquele arquivo (sha256), provedor e orçamento; política por repositório |
| `avaliacao` | QA editorial por dimensão (sem nota única) |
| `experimentos` | base para Growth Analytics: hipóteses × métricas reais por plataforma, com fonte |

## Usar sem instalar
```
py creative-intelligence/ci.py verificar
py creative-intelligence/ci.py analisar video.mp4 --saida pesquisas/ci/meu-video
```
## Instalar (outros projetos), fixando a versão
```
pip install "creative-intelligence @ git+https://github.com/scamposgabriel/gerador-de-videos@ci-v1.0.0#subdirectory=creative-intelligence"
python -m creative_intelligence verificar
```

## Comandos
```
ci analisar VIDEO --saida PASTA [--inicio S --duracao S] [--sem-quadros]
ci referencia youtube URL --tema "tema" --saida ref.json      metadados oficiais (gasta cota da sua chave)
ci referencia manual entrada.json --saida ref.json            números de outra ferramenta, sempre com a fonte
ci modelo observacoes_editoriais --saida obs.json             modelo para quem assistiu preencher (PREENCHER bloqueia)
ci brief --referencia ref.json --observacoes obs.json [--analise analise_tecnica.json] --saida PASTA
ci comparar A.mp4 B.mp4 --hipotese "o que mudou e por quê" --janela 15 --rotulos v1,v2 --saida PASTA
ci prever VIDEO --projeto P --saida PASTA --provedor higgsfield --modelo-autorizacao     (prepara; nada é enviado)
ci prever VIDEO --projeto P --saida PASTA --provedor higgsfield --autorizacao aut.json --enviar
ci avaliacao modelo VIDEO --avaliador NOME --saida av.json
ci experimento novo --id ID --projeto P --titulo T --versao V --gancho G --saida exp.json
ci experimento publicar exp.json --plataforma instagram --data AAAA-MM-DD
ci experimento metricas exp.json --plataforma instagram --de metricas.csv --fonte "painel, export AAAA-MM-DD"
```

## O que NÃO faz
Não baixa vídeos de terceiros, não faz scraping, não usa cookies, não inventa métricas, não diz o que "causou" o sucesso de um vídeo,
não transforma pontuação de preditor em probabilidade de viralizar e não envia nada sem autorização.

## Testes
`py -m pytest creative-intelligence/tests` (vídeos sintéticos gerados pelo FFmpeg; CLI falsa da Higgsfield; nenhuma chamada paga).

Exemplos: `exemplos/poc01-sintetico/` (engenharia reversa de um vídeo sintético) e `exemplos/poc03-preditor/` (preparação do
clipe, checagens da CLI real e resultado simulado). Guia completo: `docs/05_CREATIVE_INTELLIGENCE.md` na raiz do repositório.
