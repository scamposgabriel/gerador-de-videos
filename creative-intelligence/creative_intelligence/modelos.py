"""Modelos JSON para preencher (o que a máquina não sabe, quem assistiu escreve). "PREENCHER" bloqueia o uso até ser trocado."""
from __future__ import annotations

import datetime as dt

from . import avaliacao, experimentos
from .autorizacao import modelo as _autorizacao

P = "PREENCHER"


def _obs(dica: str) -> dict:
    return {"texto": f"{P}: {dica}", "tipo": "fato_observado", "evidencia": f"{P}: o que se vê/ouve e onde", "intervalo": [0.0, 0.0]}


def entrada_manual() -> dict:
    return {"referencia": {"id": P, "plataforma": "youtube", "url": P, "criador": P, "tema": P, "titulo": P,
                           "acesso_ao_video": "somente_metadados", "arquivo_video": None, "direitos_do_arquivo": None},
            "metricas": {"visualizacoes": {"valor": None, "fonte": "ex.: vidIQ (colado em AAAA-MM-DD)", "verificado": False},
                         "outlier_score": {"valor": None, "fonte": "ex.: vidIQ", "verificado": False}}}


def observacoes_editoriais(ref_id: str = P) -> dict:
    return {
        "contrato": "observacoes_editoriais", "referencia_id": ref_id, "analista": P,
        "abertura": {"primeira_imagem": _obs("o que aparece no 1º quadro"), "primeira_fala": _obs("primeira frase dita/escrita"),
                     "promessa_ou_pergunta": _obs("o que o vídeo promete responder"),
                     "elemento_curiosidade": _obs("o que faz querer ver o resto"), "tempo_ate_assunto_s": None},
        "desenvolvimento": {"ritmo": _obs("como o ritmo é construído"), "progressao": _obs("como cada parte leva à próxima"),
                            "revelacoes": [_obs("revelação principal e quando acontece")]},
        "conclusao": {"resolucao": _obs("como a pergunta é respondida"), "recompensa": _obs("o que o espectador ganha"),
                      "encerramento": _obs("como termina")},
        "estilo_visual": _obs("cores, texto na tela, enquadramento"), "animacao": [_obs("movimento que ajuda a explicar")],
        "audio": _obs("voz, música, efeitos e pausas"),
        "tecnicas_transferiveis": [f"{P}: padrão que podemos usar com conteúdo próprio"],
        "nao_copiar": [f"{P}: personagem, bordão, arte, roteiro ou frase do criador"],
        "hipoteses": [{"hipotese": f"{P}: o que pode ter ajudado o desempenho", "base": f"{P}: evidência observada",
                       "confianca": "baixa"}],
        "recomendacoes": {"ganchos": [f"{P}: gancho original 1", f"{P}: gancho original 2", f"{P}: gancho original 3"],
                          "progressao": [P], "demonstracoes": [P], "ritmo": [P], "riscos_originalidade": [P], "estrategia": P},
    }


def todos() -> dict:
    hoje = dt.date.today().isoformat()
    return {
        "entrada_manual": entrada_manual(),
        "observacoes_editoriais": observacoes_editoriais(),
        "autorizacao_envio": _autorizacao("SHA256-DO-CLIPE", "higgsfield"),
        "avaliacao_editorial": avaliacao.modelo("NOME-DO-VIDEO", P),
        "experimento": experimentos.novo(f"exp-{hoje}", P, P, "v1", P),
    }
