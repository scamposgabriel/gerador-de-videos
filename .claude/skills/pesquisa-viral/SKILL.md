---
name: pesquisa-viral
description: Pesquisa os vídeos mais vistos do YouTube por tema ou por canal (API oficial do YouTube, chave gratuita), calcula visualizações por dia e o quanto cada vídeo ficou "fora da curva" do canal (parecido com o outlier do vidIQ) e transforma os padrões em ideias ORIGINAIS de vídeo. Use quando pedirem para achar vídeos famosos, virais, em alta, temas que funcionam, analisar um canal, ou ideias de vídeo baseadas no que já dá certo.
---

# Pesquisa viral

Responda em português. O objetivo é **aprender o padrão** do que funciona e criar algo próprio — nunca copiar.

## Configurar (uma vez por computador)
A pesquisa usa a **YouTube Data API v3** (oficial, gratuita dentro da cota). Passo a passo para o usuário:
1. Entrar em https://console.cloud.google.com com a conta Google e criar um projeto (ex.: "pesquisa-videos").
2. Em **APIs e serviços → Biblioteca**, procurar **YouTube Data API v3** e clicar em **Ativar**.
3. Em **APIs e serviços → Credenciais → Criar credenciais → Chave de API**. Recomendado: **restringir a chave** à YouTube Data API v3.
4. Salvar a chave no arquivo `~/.secrets/youtube/.env` (no Windows: `C:\Users\<usuário>\.secrets\youtube\.env`) com a linha
   `YOUTUBE_API_KEY=a_chave`. Alternativa: variável de ambiente `YOUTUBE_API_KEY`.
Nunca peça para colar a chave no chat, nunca imprima, nunca salve dentro do repositório.

Conferir sem chave: `py ferramentas/pesquisa_youtube.py teste`.

## Pesquisar
```
py ferramentas/pesquisa_youtube.py tema "curiosidades sobre cachorros" --dias 365 --idioma pt --regiao BR
py ferramentas/pesquisa_youtube.py tema "por que os gatos" --duracao short --n 50
py ferramentas/pesquisa_youtube.py canal @nomedocanal --n 25
```
- `--dias N`: só vídeos dos últimos N dias (0 = qualquer data). `--duracao short|medium|long` (< 4 min, 4–20, > 20).
- Saída em `pesquisas/<data>-<tema|canal>-<assunto>.md` (tabela) e `.json` (dados completos).
- **Fora da curva** = views ÷ mediana. No `canal`, a mediana é dos últimos 50 uploads do canal (3× ou mais = pegou além do normal);
  no `tema`, é a mediana do próprio resultado.
- **Cota** (documentação oficial conferida em 21/11/2026): 100 buscas por dia e 10.000 unidades por dia para o resto; cada comando
  gasta 1 busca. Não faça dezenas de buscas parecidas: refine o termo.
- A API não entrega a transcrição de vídeos de outros canais. Se o usuário quiser a estrutura de um vídeo específico, peça para
  colar a transcrição (no YouTube: "...mais" → "Mostrar transcrição").

## vidIQ
O vidIQ não tem uma API aberta para usar aqui. Se o usuário tem vidIQ (extensão ou site), peça para colar o que ele mostra
(pontuação da palavra-chave, concorrência, "outlier", ideias) e use junto com a pesquisa da API. Não automatize o site.

## Analisar e transformar em ideias
1. Ordene por **fora da curva** e **views por dia** (vídeo novo com muitas views/dia pesa mais que vídeo antigo acumulado).
2. Ache os padrões dos 10 primeiros: fórmula do título (pergunta "Por que...", número, contraste), tema, promessa, duração,
   formato (curto × longo), o que se repete entre canais diferentes.
3. Separe **o que é padrão** (pode usar) de **o que é do criador** (personagem, roteiro, arte, frase exata: não use).
4. Entregue em `pesquisas/<data>-ideias.md`:
   - tabela curta dos vídeos que mais se destacaram (com link) e o padrão de cada um;
   - **5 a 10 ideias originais**, cada uma com: título proposto, gancho de 1 frase, por que deve funcionar (qual padrão),
     formato sugerido e o que o vídeo mostraria;
   - limites da pesquisa (amostra, período, views ≠ retenção).
5. Ofereça passar a melhor ideia para a skill `roteirista`.

## Não faça
- Baixar vídeos de outros canais ou entrar logado em redes sociais por automação (viola os termos das plataformas).
- Prometer que um tema "vai viralizar": a pesquisa mostra o que funcionou, não garante o próximo.
