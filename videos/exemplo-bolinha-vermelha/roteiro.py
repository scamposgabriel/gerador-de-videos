# MODELO de vídeo animado para Reels (1080 x 1920): "Por que seu cachorro pode perder uma bolinha vermelha na grama?"
# Copie esta pasta (videos/exemplo-bolinha-vermelha → videos/<seu-video>), troque as FALAS e adapte as cenas da pagina.html.
#
# Gravar:  py motor/animar.py videos/exemplo-bolinha-vermelha                fotos: --fotos 0,5,12   teste com som: --ate 12
# Capa:    py ferramentas/capa.py videos/exemplo-bolinha-vermelha             (render(t < 0) desenha a capa)
# Textos:  py ferramentas/verificar_textos.py videos/exemplo-bolinha-vermelha (texto cortado ou embaixo dos botões do Instagram)
#
# Como a página usa este roteiro:
#   - cada fala vira uma CENA (cena="misterio" → função cMisterio na pagina.html); as ações entram na palavra falada
#     (quando("misterio", "vermelha") = instante em que a voz diz "vermelha");
#   - qualquer variável em MAIÚSCULAS daqui (MARCA, PERSONAGEM...) chega na página em TL.dados.
#
# Ciência (conferir antes de mudar o texto): o cachorro tem 2 tipos de cone (visão dicromática, sensível a azul-violeta e
# amarelo-esverdeado); nós temos 3. Vermelho e verde ficam parecidos para ele, azul se destaca. A tela mostra uma
# SIMULAÇÃO APROXIMADA (matriz de daltonismo deuteranópico, Machado 2009), rotulada assim no vídeo.

CONFIG = dict(
    pagina="pagina.html",
    tela=(1080, 1920),
    densidade=2,                                   # desenha em 2160 x 3840 e reduz: borda lisa e texto firme
    voz={"motor": "edge", "nome": "pt-BR-AntonioNeural", "ritmo": "+4%", "respiro": 260},
    voz_compressor=True,
    saida="Exemplo - A bolinha vermelha.mp4",
    saida_so_voz="Exemplo - A bolinha vermelha - so voz.mp4",   # sem música: para pôr música do próprio Instagram
    trilha=True, trilha_estilo="lofi", bpm=96, duck_ratio=3,
    intro=0.35, folga=0.32, fim=3.8,
    crf=14,
)

# Nome do canal (etiqueta do topo, cartão final e capa). avatar: caminho de uma imagem quadrada (relativo a esta pasta); vazio = Lumi.
MARCA = dict(nome="Seu Canal", avatar="")

# Seu personagem em PNG (opcional). Sem isto, entra o Lumi desenhado em SVG.
# Poses: apresentando, apontando, olha-so, pensando, rindo, surpreso; arquivos 941 x 1672 com fundo TRANSPARENTE de verdade,
# palma direita do "apresentando" perto de (850, 580) e palma esquerda perto de (90, 830) (é onde as cenas põem as bolinhas).
# Exemplo: PERSONAGEM = dict(pasta="../../marcas/meu-personagem/poses", prefixo="meu-")   → ../../marcas/.../meu-apresentando.png
PERSONAGEM = dict()

FALAS = [
    dict(id="01", cena="misterio", fala="Por que o seu cachorro às vezes perde uma bolinha vermelha? Bem na frente dele!"),
    dict(id="02", cena="surpresa", fala="Pode não ser distração. O problema pode estar nas cores que ele consegue diferenciar."),
    dict(id="03", cena="explicacao", fala="A gente tem três tipos de células que enxergam cor. O cachorro tem só dois. "
                                          "Por isso, azul e amarelo se destacam para ele. Já vermelho e verde ficam bem parecidos."),
    dict(id="04", cena="revelacao", fala="Olha essa bolinha pelos nossos olhos. Agora, pelos olhos dele. "
                                         "Ela não fica invisível. Mas quase se perde no gramado."),
    dict(id="05", cena="solucao", fala="Agora, troca por uma bolinha azul. Fica muito mais fácil de achar! "
                                       "Claro, o faro e o movimento também ajudam."),
    dict(id="06", cena="fechamento", fala="Então, antes de achar que ele se distraiu, pensa nisso. "
                                          "Talvez ele só precise de outra cor. Eu sou o Lumi. E tá explicado!"),
]
