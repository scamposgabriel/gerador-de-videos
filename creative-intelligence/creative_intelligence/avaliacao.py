"""QA EDITORIAL (revisão qualitativa), separado do QA técnico (testes objetivos do motor), da predição (estimativa de um
modelo) e do resultado real (métricas da plataforma). Não existe nota única: cada dimensão fica com a sua nota e justificativa.
"""
from __future__ import annotations

import datetime as dt

from .contratos import exigir

DIMENSOES = {
    "gancho": "os primeiros segundos mostram o assunto e criam uma pergunta?",
    "clareza": "quem não conhece o tema entende a ideia principal?",
    "progressao_narrativa": "cada parte acrescenta algo e leva à próxima?",
    "ritmo": "nada arrasta nem atropela; pausas onde precisa?",
    "composicao": "o olho sabe para onde olhar em cada quadro?",
    "legibilidade": "todo texto lê no celular, fora das áreas cobertas pelo app?",
    "animacao": "o movimento explica (não só enfeita)?",
    "audio": "voz clara, volume equilibrado, efeitos no tempo certo?",
    "originalidade": "a forma é nossa (nada copiado de outro criador)?",
    "encerramento": "o final recompensa e convida a interagir?",
}
CAMADAS = {
    "qa_tecnico": "testes objetivos do motor (formato, FPS, sincronia, volume, textos) — aprovado/reprovado",
    "qa_editorial": "revisão qualitativa por dimensão (este módulo) — notas 1 a 5 com justificativa, sem nota única",
    "predicao": "estimativa de um modelo externo (opcional) — não é probabilidade de viralizar",
    "resultado_real": "métricas observadas na plataforma depois de publicar — a única evidência de desempenho",
}


def modelo(video: str, avaliador: str, tipo_avaliador="humano", versao=None) -> dict:
    return {"contrato": "avaliacao_editorial", "video": video, "versao": versao, "avaliador": avaliador,
            "tipo_avaliador": tipo_avaliador, "data": dt.date.today().isoformat(),
            "dimensoes": {k: {"nota": None, "justificativa": f"PENDENTE — {pergunta}", "status": "pendente"}
                          for k, pergunta in DIMENSOES.items()}}


def validar_notas(av: dict) -> dict:
    exigir("avaliacao_editorial", av)
    faltam = set(DIMENSOES) - set(av["dimensoes"])
    if faltam:
        raise ValueError(f"dimensões ausentes: {', '.join(sorted(faltam))}")
    for k, d in av["dimensoes"].items():
        if d["status"] == "avaliado" and not (isinstance(d["nota"], int) and 1 <= d["nota"] <= 5):
            raise ValueError(f"{k}: avaliado exige nota inteira de 1 a 5")
        if d["status"] == "pendente" and d["nota"] is not None:
            raise ValueError(f"{k}: pendente não tem nota")
    return av


def markdown(av: dict) -> str:
    validar_notas(av)
    L = [f"# QA editorial — {av['video']}" + (f" ({av['versao']})" if av.get("versao") else ""), "",
         f"Avaliador: {av['avaliador']} ({av['tipo_avaliador']}) · {av['data']}", "",
         "> Revisão qualitativa. Não é QA técnico, não é predição e não é resultado real. Sem nota única: leia cada dimensão.", "",
         "| Dimensão | Nota | Status | Justificativa |", "|---|---|---|---|"]
    for k in DIMENSOES:
        d = av["dimensoes"][k]
        L.append(f"| {k.replace('_', ' ')} | {d['nota'] if d['nota'] is not None else '—'} | {d['status']} | {d['justificativa']} |")
    pend = [k for k in DIMENSOES if av["dimensoes"][k]["status"] == "pendente"]
    if pend:
        L += ["", f"Pendentes ({len(pend)}): {', '.join(pend)}."]
    return "\n".join(L) + "\n"
