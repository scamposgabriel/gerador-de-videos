# Modelo de roteiro do Gerador de Vídeos (modo tutorial). Copie para videos/<nome-do-video>/roteiro.py e ajuste.
# Para quem é e o que a pessoa vai conseguir fazer depois: <escreva aqui em uma frase>
# Gravar teste:  py motor/gravar.py videos/<nome-do-video> --so 02-03
# Gravar tudo:   py motor/gravar.py videos/<nome-do-video>

CONFIG = {
    "titulo": "Como usar <ferramenta>",
    # página a gravar: caminho de HTML (sempre r"...": \3 e \33 num caminho viram caractere de controle) ou endereço http(s)://
    "pagina": r"C:\caminho\da\pagina.html",
    "janela": (1600, 900), "densidade": 1.6,     # 2560 x 1440; não mude sem motivo
    "raiz": ".app",                               # elemento que recebe o zoom (sem ele, o corpo da página)
    "voz": {"motor": "edge", "nome": "pt-BR-FranciscaNeural"},   # ver vozes/CATALOGO.md
    "logo": "",                                   # PNG do logo para {{LOGO}} nas capas (relativo a esta pasta); vazio = sem logo
    "saida": "Como usar - <ferramenta>.mp4",
    "publicar_em": r"",                           # onde publicar (o gravador só avisa; publicar é manual, depois da aprovação)
    "esperar_ms": 2000,                           # tempo para a página carregar antes de começar
}

# Capas: abertura, fim e quadros explicativos. {{LOGO}} vira o logo do CONFIG. Classes prontas: ver docs/02_ACOES_DO_ROTEIRO.md.
CAPAS = {
    "abertura": """<div class="vt-capa"><img src="{{LOGO}}" alt=""><div class="k">Área · Assunto</div>
      <h1>Título do vídeo:<br>como usar</h1><p>Uma linha do que o vídeo ensina.</p><div class="linha"></div></div>""",
    "fim": """<div class="vt-capa"><img src="{{LOGO}}" alt=""><div class="k">Resumo</div><h1>Em três passos</h1>
      <ol><li>Passo um.</li><li>Passo dois.</li><li>Passo três.</li></ol><p style="margin-top:28px">Dúvidas: fale com o responsável pela ferramenta</p></div>""",
}

# CSS a mais só para a gravação (ex.: borrar nomes num vídeo para fora da empresa: "#tabela td:nth-child(2){filter:blur(8px)}")
CSS_EXTRA = ""

FALAS = [
    dict(id="01", passo="", capa="abertura", legenda="",
         fala="Este vídeo mostra, em poucos minutos, como usar a ferramenta: onde abrir, como ler e como alimentar."),
    dict(id="02", passo="1 · Abrir", legenda="Abra pelo atalho ou pelo arquivo na pasta <b>Nome da pasta</b>.",
         fala="Abra a ferramenta pelo atalho na área de trabalho, ou pelo arquivo na pasta da equipe.",
         acao=[("semCapa",), ("cursorEm", "h1")]),
    dict(id="03", passo="2 · Resumo", legenda="Os cartões trazem o resumo.",
         fala="Os cartões trazem o resumo do mês: o valor, a quantidade e a comparação com o mês anterior.",
         acao=[("foco", ".cartoes", 1.3), ("cursorEm", ".cartoes .cartao:nth-child(1)")]),
    dict(id="04", passo="", capa="fim", legenda="",
         fala="Resumindo: abra pelo atalho, leia o resumo e alimente a planilha. Dúvidas, fale com o responsável.",
         acao=[("apagar",), ("soltar",), ("zoom0",), ("capa", "fim")]),
]
