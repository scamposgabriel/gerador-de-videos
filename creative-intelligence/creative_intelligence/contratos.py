"""Contratos (JSON) da Creative Intelligence e um validador pequeno, sem dependências.

Notação dos esquemas: tipo Python (str, int, bool, dict, list), NUM = int ou float, sufixo "?" na chave = opcional,
Um(...) = um dos valores, Nulo(x) = x ou null, Lista(x, minimo) = lista de x, Mapa(x) = dicionário com valores x.
"""
from __future__ import annotations

NUM = (int, float)
CLASSIFICACOES = ("publico", "proprio", "privado", "cliente", "interno", "confidencial")


class ContratoInvalido(Exception):
    pass


class Um:
    def __init__(self, *opcoes):
        self.opcoes = opcoes


class Nulo:
    def __init__(self, esquema):
        self.esquema = esquema


class Lista:
    def __init__(self, esquema, minimo=0, maximo=None):
        self.esquema, self.minimo, self.maximo = esquema, minimo, maximo


class Mapa:
    def __init__(self, esquema):
        self.esquema = esquema


OBS = {"texto": str, "tipo": Um("fato_observado", "metrica_verificada", "hipotese"), "evidencia": str,
       "intervalo?": Lista(NUM, 2, 2)}
METRICA = {"valor": Nulo((int, float, str)), "fonte": str, "coletado_em": str, "verificado": bool, "observacao?": str}

ESQUEMAS = {
    "referencia": {
        "contrato?": str, "id": str, "plataforma": Um("youtube", "instagram", "tiktok", "outro"), "url": str, "criador": str,
        "tema": str, "titulo?": str, "coletado_em": str, "publicado_em?": Nulo(str), "duracao_s?": Nulo(NUM),
        "metricas": Mapa(METRICA), "acesso_ao_video": Um("arquivo_local", "somente_metadados", "sem_acesso"),
        "arquivo_video?": Nulo(str), "direitos_do_arquivo?": Nulo(str), "observacoes?": str,
    },
    "observacoes_editoriais": {
        "contrato?": str, "referencia_id": str, "analista": str,
        "abertura": {"primeira_imagem": OBS, "primeira_fala": OBS, "promessa_ou_pergunta": OBS, "elemento_curiosidade": OBS,
                     "tempo_ate_assunto_s?": Nulo(NUM)},
        "desenvolvimento": {"ritmo": OBS, "progressao": OBS, "revelacoes": Lista(OBS), "mudancas_visuais?": OBS, "humor?": OBS,
                            "comparacoes?": OBS, "suspense?": OBS},
        "conclusao": {"resolucao": OBS, "recompensa": OBS, "encerramento": OBS, "convite_interacao?": OBS, "repeticao_natural?": OBS},
        "estilo_visual": OBS, "animacao": Lista(OBS), "audio": OBS,
        "tecnicas_transferiveis": Lista(str, 1), "nao_copiar": Lista(str, 1),
        "hipoteses": Lista({"hipotese": str, "base": str, "confianca": Um("baixa", "media", "alta")}, 1),
        "recomendacoes": {"ganchos": Lista(str, 3), "progressao": Lista(str, 1), "demonstracoes": Lista(str, 1),
                          "ritmo": Lista(str, 1), "riscos_originalidade": Lista(str, 1), "estrategia": str},
    },
    "autorizacao_envio": {
        "contrato?": str, "arquivo_sha256": str, "arquivo_nome?": str, "provedor": str, "finalidade": str,
        "classificacao": Um(*CLASSIFICACOES), "direitos_confirmados": bool, "envio_externo_permitido": bool,
        "contem_dados_pessoais": bool, "autorizacao_cliente?": Nulo(str), "orcamento_maximo_creditos": Nulo(NUM),
        "aceita_custo_nao_estimado": bool, "aprovado_por": str, "aprovado_em": str, "valido_ate?": Nulo(str),
    },
    "resultado_preditivo": {
        "contrato?": str, "projeto": str, "video": str, "versao?": Nulo(str), "plataforma?": Nulo(str), "provedor": str,
        "ferramenta": str, "simulado": bool, "data": str,
        "janela": {"inicio_s": NUM, "duracao_s": NUM, "duracao_total_s": Nulo(NUM), "cobre_video_inteiro": bool},
        "status": Um("preparado", "concluido", "falhou", "bloqueado"), "campos_retornados": dict,
        "url_relatorio?": Nulo(str), "custo?": Nulo(dict), "limitacoes": Lista(str), "erro?": Nulo(str),
    },
    "avaliacao_editorial": {
        "contrato?": str, "video": str, "versao?": Nulo(str), "avaliador": str, "tipo_avaliador": Um("humano", "ia"), "data": str,
        "dimensoes": Mapa({"nota": Nulo(int), "justificativa": str, "status": Um("avaliado", "pendente")}),
        "observacoes?": str,
    },
    "experimento": {
        "contrato?": str, "id": str, "projeto": str,
        "video": {"titulo": str, "versao": str, "arquivo_sha256?": Nulo(str)},
        "referencias": Lista(str), "hipoteses": Lista(str), "tipo_gancho": str,
        "qa_tecnico?": Nulo(dict), "qa_editorial?": Nulo(dict), "predicoes": Lista(dict),
        "publicacoes": Lista({"plataforma": str, "data": Nulo(str), "url?": Nulo(str), "metricas": Mapa(METRICA)}),
        "custos": Lista({"item": str, "valor": NUM, "moeda": str, "fonte": str}),
        "receita?": Nulo(dict),
        "campanha?": Nulo({"objetivo": str, "publico": str, "oferta?": Nulo(str), "metrica_principal": str}),
    },
}


def _tipo_ok(valor, tipo) -> bool:
    tipos = tipo if isinstance(tipo, tuple) else (tipo,)
    if isinstance(valor, bool) and bool not in tipos:  # True/False não valem como número
        return False
    return isinstance(valor, tipos)


def _checar(valor, esq, caminho: str, erros: list):
    if isinstance(esq, Nulo):
        if valor is not None:
            _checar(valor, esq.esquema, caminho, erros)
        return
    if valor is None:
        erros.append(f"{caminho}: vazio (null) não permitido")
        return
    if isinstance(esq, Um):
        if valor not in esq.opcoes:
            erros.append(f"{caminho}: '{valor}' não é um de {list(esq.opcoes)}")
        return
    if isinstance(esq, Lista):
        if not isinstance(valor, list):
            erros.append(f"{caminho}: esperado lista")
            return
        if len(valor) < esq.minimo:
            erros.append(f"{caminho}: precisa de pelo menos {esq.minimo} item(ns), tem {len(valor)}")
        if esq.maximo is not None and len(valor) > esq.maximo:
            erros.append(f"{caminho}: no máximo {esq.maximo} item(ns)")
        for i, item in enumerate(valor):
            _checar(item, esq.esquema, f"{caminho}[{i}]", erros)
        return
    if isinstance(esq, Mapa):
        if not isinstance(valor, dict):
            erros.append(f"{caminho}: esperado objeto")
            return
        for k, item in valor.items():
            _checar(item, esq.esquema, f"{caminho}.{k}", erros)
        return
    if isinstance(esq, dict):
        if not isinstance(valor, dict):
            erros.append(f"{caminho}: esperado objeto")
            return
        for chave, sub in esq.items():
            opcional = chave.endswith("?")
            nome = chave.rstrip("?")
            if nome not in valor:
                if not opcional:
                    erros.append(f"{caminho}.{nome}: obrigatório")
                continue
            _checar(valor[nome], sub, f"{caminho}.{nome}", erros)
        return
    if not _tipo_ok(valor, esq):
        nome = esq.__name__ if isinstance(esq, type) else "/".join(t.__name__ for t in esq)
        erros.append(f"{caminho}: esperado {nome}, veio {type(valor).__name__}")
        return
    if esq is str and not valor.strip():
        erros.append(f"{caminho}: texto vazio")


def validar(nome: str, dados) -> list[str]:
    if nome not in ESQUEMAS:
        raise KeyError(f"contrato desconhecido: {nome} (há: {', '.join(ESQUEMAS)})")
    erros: list[str] = []
    _checar(dados, ESQUEMAS[nome], nome, erros)
    return erros


def exigir(nome: str, dados) -> dict:
    erros = validar(nome, dados)
    if erros:
        raise ContratoInvalido(f"contrato '{nome}' inválido:\n  - " + "\n  - ".join(erros[:25]))
    return dados
