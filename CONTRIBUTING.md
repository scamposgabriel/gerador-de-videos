# Como colaborar

Obrigado por ajudar! Tudo em português (código comentado, textos e mensagens de commit).

## Fluxo
1. Crie uma branch a partir da `main`: `git checkout -b minha-melhoria`.
2. Faça a mudança. Se usar o Claude Code, ele segue o `CLAUDE.md` e as skills automaticamente.
3. **Teste no exemplo** antes de abrir o pull request:
   ```
   py motor/animar.py videos/exemplo-bolinha-vermelha --fotos 0,5,12,25,40
   py motor/animar.py videos/exemplo-bolinha-vermelha
   py ferramentas/verificar_textos.py videos/exemplo-bolinha-vermelha
   ```
   O `saida/controle_de_qualidade.json` tem que dizer **APROVADO**. Olhe as fotos: o resultado tem que continuar igual (ou melhor).
   Mudou algo em `creative-intelligence/`? Rode também `py -m pytest creative-intelligence/tests` (vídeos sintéticos, sem rede).
4. Abra o pull request dizendo **o que mudou** e **como validar** (comandos e o que olhar).

## Regras do código
- `render(t)` depende só de `t`: nada guardado do quadro anterior (assim qualquer trecho é refeito igual).
- O motor (`motor/`) é comum a todos os vídeos. Mudou o motor? Grave o exemplo inteiro e confira o QA.
- Nada de dependência nova sem necessidade; se precisar, fixe a versão no `requirements.txt`.
- Vídeo novo de exemplo: pasta nova em `videos/`, sem alterar `exemplo-bolinha-vermelha`.

## Nunca suba
- `saida/` e `falas/` (são refeitos pelo motor), clipes de banco de imagens, chaves (`.env`, `~/.secrets`), dados de clientes.
  O `.gitignore` já barra os casos comuns — confira o `git status` antes do commit.

## Ideias de melhoria
- Mais cenas prontas para copiar (gráfico animado, mapa, contagem, antes/depois).
- Mais personagens prontos em SVG (como o Lumi).
- Testes automáticos do motor.
- Verificador de textos dentro do `motor/qa.py`.
