---
name: roteirista
description: Escreve roteiros de vídeo curtos (Reels, TikTok, Shorts) e tutoriais em português, prontos para o gerador de vídeo - gancho, estrutura, falas que soam naturais na voz sintética, storyboard cena a cena (o que aparece na tela em cada palavra), título, texto da capa e legenda do post. Use quando pedirem um roteiro, ideia de vídeo, gancho, título, legenda, ou "faz um vídeo sobre X" (antes de gravar).
---

# Roteirista

Responda em português. O roteiro é para **ouvir e ver**, não para ler: frases curtas, uma imagem forte por cena.

## 1. Entender o pedido (pergunte só o que faltar)
- **Tema** e **objetivo**: ensinar uma curiosidade, vender, ensinar a usar algo.
- **Público** (quem é, o que já sabe) e **formato**: Reels/Shorts de 45 a 75 s (padrão) ou tutorial de 3 a 5 min.
- **Narrador/personagem** (ex.: o personagem do canal) e **bordão** de fechamento, se houver.
- **Chamada final**: comentar, seguir, pedir simulação...
- **Restrições**: marca, regras do setor (ex.: consórcio não pode prometer prazo), o que não pode aparecer.

Se o usuário quiser saber o que está funcionando, use antes a skill `pesquisa-viral` e parta dos padrões encontrados.
**Nunca copie** roteiro, título ou estrutura cena a cena de outro criador: use o padrão (o tipo de pergunta, o ritmo) com
conteúdo, ângulo e personagem próprios.

## 2. Escolher o ângulo (o gancho)
Uma pergunta que parece óbvia e não tem resposta imediata, com um detalhe concreto:
- "Por que [fato que surpreende] se [o que a pessoa esperava]?" — *Por que seu cachorro perde uma bolinha vermelha bem na frente dele?*
- "O que acontece se...?", "Você já reparou que...?", "Isso já [consequência forte]".
O gancho cabe em **até 2 segundos de fala** e a primeira imagem já mostra o mistério acontecendo.

## 3. Estruturas que funcionaram
**Curiosidade (≈ 50 s, 6 cenas)** — modelo `videos/exemplo-bolinha-vermelha`:
1. Mistério (0–5 s): a cena acontecendo + a pergunta.
2. Virada: "Não é [o que você pensa]. É [a causa real]."
3. Explicação: **um** mecanismo, comparando dois lados (nós × eles, antes × depois).
4. Demonstração visual: a recompensa do vídeo — a pessoa **vê** o fenômeno.
5. Aplicação: o que fazer com isso (a solução), com a ressalva honesta.
6. Fecho: a lição numa frase + bordão + pergunta para comentar.

**Venda / história (≈ 40 a 60 s)**: gancho (dúvida reconhecível) → personagem com problema concreto → descoberta do produto →
demonstração → convite claro. A venda nasce dentro da história; lista de vantagens com imagem bonita não segura ninguém.
Publicidade regulada: não prometa prazo, resultado ou ganho; aviso legal curto na tela; personagem fictício rotulado.

**Tutorial (3 a 5 min)**: para quem é e o que vai conseguir → onde abrir → resumo → detalhe na ordem de uso → como alimentar →
a quem perguntar → fecho em 3 passos.

## 4. Regras da fala (voz sintética)
- Frases de **até ~15 palavras**, uma ideia por frase; listas de no máximo 3 itens. Vírgula onde se respira.
- Ritmo: o vídeo sai com **2,4 a 3,2 palavras por segundo**. Estimativa: duração ≈ palavras ÷ 2,8.
- Siglas: troque pelo nome, ou escreva como se fala numa palavra só. Nada de parênteses, barras ou abreviações na fala.
- Números simples por extenso ("três tipos"); valores com unidade, como se fala ("dois por cento").
- Fale com a pessoa ("você", "seu cachorro"); verbos no presente; uma pergunta a cada duas ou três cenas segura a atenção.

## 5. Storyboard: cada fala é uma cena
Para cada fala, descreva:
- **Visual**: o que aparece e o que se mexe (objeto grande, câmera aproximando, personagem em qual pose).
- **Texto grande na tela**: no máximo 4 palavras (ex.: "ELE NÃO VIU?!", "NÃO É INVISÍVEL!").
- **Gatilhos**: que palavra da fala dispara o quê (ex.: em "vermelha" → anel em volta da bolinha; em "azul" → a bolinha vira azul).
Isso é o que o gerador usa para sincronizar (`quando(cena, "palavra")`).

## 6. Verdade e segurança
- Confira cada fato. Se não tiver certeza, pesquise em fonte confiável e cite na entrega; use "pode", "geralmente" quando for o caso.
  Não invente número. Simulação vai rotulada ("simulação aproximada").
- Nada de dado de cliente ou de pessoa real na fala (ela vai para um serviço de voz externo).
- Não use música, trecho ou imagem de terceiros sem licença.

## 7. O que entregar
1. **roteiro.py** pronto para a pasta do vídeo (copie o CONFIG do modelo; `FALAS` com `id`, `cena`, `fala`).
2. **Storyboard** em tabela: cena · tempo estimado · fala · visual · texto na tela · gatilhos.
3. **Título** do post (até 60 caracteres), **texto da capa** (até 5 palavras, legível pequeno), **legenda do post** curta com
   pergunta no fim e 3 a 5 hashtags. Não prometa viralização.
4. **Duração estimada** e ritmo (palavras/s) de cada fala.
5. **Fatos a conferir**, com a fonte de cada um.

Mostre ao usuário e **espere a aprovação** antes de passar para a skill `gerador-de-video`.

## Exemplo (resumo do modelo)
| Cena | Fala | Visual | Na tela |
|---|---|---|---|
| mistério | "Por que o seu cachorro às vezes perde uma bolinha vermelha? Bem na frente dele!" | cachorro passa correndo pela bolinha, volta, fareja, "?" | ELE NÃO VIU?! |
| virada | "Pode não ser distração. O problema pode estar nas cores que ele consegue diferenciar." | lupa no olho do cachorro | NÃO É ~~DISTRAÇÃO~~ / É A COR! |
| explicação | "A gente tem três tipos de células que enxergam cor. O cachorro tem só dois..." | HUMANOS 3 × CÃES 2 | CÉLULAS DE COR |
| demonstração | "Olha essa bolinha pelos nossos olhos. Agora, pelos olhos dele..." | mesma cena, varredura para a visão do cão | NÃO É INVISÍVEL! |
| solução | "Agora, troca por uma bolinha azul. Fica muito mais fácil de achar!..." | vermelha vira azul; cachorro acha | TROCA A COR! |
| fecho | "...Talvez ele só precise de outra cor. Eu sou o Lumi. E tá explicado!" | personagem + cachorro | TÁ EXPLICADO! |
