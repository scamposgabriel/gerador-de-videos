# Como fazer um vídeo tutorial (modo tutorial, `motor/gravar.py`)

Para Reels e vídeos explicativos desenhados, ver `docs/04_VIDEO_ANIMADO.md`.

## 1. Antes de escrever
- **Para quem é o vídeo e o que a pessoa precisa conseguir fazer depois de assistir?** Escreva isso em uma frase no topo do roteiro.
- **Qual página vai ser gravada?** Arquivo HTML (caminho) ou endereço web. Ela precisa abrir sem login no Edge, ou já com os
  dados de exemplo carregados.
- **Quanto tempo?** Tutorial bom tem de 3 a 5 minutos. Cada fala tem de 8 a 20 segundos (1 a 3 frases).

## 2. Estrutura que funciona
1. Abertura (capa com logo, título e uma linha do que o vídeo ensina).
2. Onde abrir e de quando são os dados.
3. Uma cena por parte da tela, na ordem em que a pessoa usa: primeiro o resumo, depois o detalhe.
4. Como a pessoa alimenta a ferramenta (planilha, filtros), com um quadro de exemplo se precisar (dados fictícios, rotulado "exemplo").
5. Onde estão as regras e a quem perguntar.
6. Fechamento em 3 ou 4 passos.

Na tela aparece uma etiqueta com o passo ("2 · Resumo"): use os mesmos números do fechamento.

## 3. Escrever o roteiro
Copie `modelos/roteiro_modelo.py` para `videos/<nome>/roteiro.py`. Cada fala é um dicionário:

```python
dict(id="05", passo="2 · Resumo",
     legenda="Os cartões trazem o <b>resumo</b> do mês.",               # aparece escrito (pode ter <b>)
     fala="Os cartões trazem o resumo: o valor, a quantidade e a meta.",  # o que a voz lê
     acao=[("foco", ".cartoes", 1.3), ("cursorEm", ".cartoes .cartao:nth-child(1)")]),
```

- `id` em ordem ("01", "02"...). O teste `--so 05-07` grava só essas falas.
- Legenda curta (uma linha, no máximo duas). A fala pode ser mais completa que a legenda.
- Siglas na fala do jeito que se fala, numa palavra só ("pedeéfe" testado numa amostra), ou troque pelo nome.
- As ações estão em `docs/02_ACOES_DO_ROTEIRO.md`. Para achar o seletor de um elemento: no Edge, botão direito → Inspecionar.

## 4. Escolher a voz
Ver `vozes/CATALOGO.md` e pôr no `CONFIG`:
```python
"voz": {"motor": "edge", "nome": "pt-BR-FranciscaNeural", "ritmo": "+0%", "tom": "+0Hz"},
```
Ritmo -3% e tom -2Hz deixaram o Antonio mais calmo. Vozes multilíngues às vezes não aceitam ajuste de tom: deixe sem.

## 5. Gravar
```
py motor/gravar.py videos/<nome> --so 02-04      (teste de 20 a 30 s: confira nitidez, zoom, cursor e sincronia)
py motor/gravar.py videos/<nome>                 (vídeo inteiro; ~1 min de gravação por minuto de vídeo)
py motor/gravar.py videos/<nome> --refazer-vozes (depois de mudar o texto de alguma fala ou a voz)
```
As vozes ficam guardadas em `videos/<nome>/falas/`; só são geradas de novo se faltarem ou com `--refazer-vozes`.

## 6. Revisar e entregar
Siga `docs/03_QUALIDADE_E_CHECKLIST.md`. Depois de aprovado pelo dono do vídeo, copie o MP4 de `videos/<nome>/saida/` para onde
ele vai ser publicado (`publicar_em` no CONFIG é só um lembrete: o gravador não publica sozinho).
