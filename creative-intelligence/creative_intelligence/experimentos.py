"""Base de experimentos para um futuro Growth Analytics: cada vídeo publicado vira um registro que liga referências estudadas,
hipóteses, tipo de gancho, versão, QA, predição (se houve) e as MÉTRICAS REAIS de cada plataforma, com fonte e data de coleta.

Métricas reais entram à mão (CSV/JSON exportado do painel da plataforma) ou por integração oficial autorizada. Nada de
aprendizado automático aqui: o objetivo é poder comparar hipótese × resultado.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from .contratos import exigir

METRICAS_REAIS = ["visualizacoes", "alcance", "retencao_media_pct", "tempo_medio_assistido_s", "curtidas", "comentarios",
                  "compartilhamentos", "salvamentos", "seguidores_ganhos"]
METRICAS_CAMPANHA = ["cliques", "leads", "conversoes", "custo_por_lead", "receita"]


def novo(id_: str, projeto: str, titulo: str, versao: str, tipo_gancho: str, hipoteses=(), referencias=(), sha256=None,
         campanha=None) -> dict:
    exp = {"contrato": "experimento", "id": id_, "projeto": projeto,
           "video": {"titulo": titulo, "versao": versao, "arquivo_sha256": sha256},
           "referencias": list(referencias), "hipoteses": list(hipoteses), "tipo_gancho": tipo_gancho,
           "qa_tecnico": None, "qa_editorial": None, "predicoes": [], "publicacoes": [], "custos": [], "receita": None,
           "campanha": campanha}
    return exigir("experimento", exp)


def registrar_publicacao(exp: dict, plataforma: str, data: str | None, url: str | None = None) -> dict:
    if any(p["plataforma"] == plataforma and p["data"] == data for p in exp["publicacoes"]):
        return exp
    exp["publicacoes"].append({"plataforma": plataforma, "data": data, "url": url, "metricas": {}})
    return exigir("experimento", exp)


def _ler_metricas(arquivo) -> dict:
    p = Path(arquivo)
    if p.suffix.lower() == ".csv":
        with p.open(encoding="utf-8-sig", newline="") as f:
            return {ln["metrica"].strip(): ln["valor"].strip() for ln in csv.DictReader(f) if ln.get("metrica")}
    return json.loads(p.read_text(encoding="utf-8"))


def importar_metricas(exp: dict, plataforma: str, arquivo, fonte: str, coletado_em: str | None = None) -> dict:
    """Importa métricas de um CSV (colunas metrica,valor) ou JSON {metrica: valor}. Valor vazio = não informado (não entra)."""
    pub = next((p for p in exp["publicacoes"] if p["plataforma"] == plataforma), None)
    if pub is None:
        raise ValueError(f"registre a publicação em '{plataforma}' antes de importar métricas")
    quando = coletado_em or dt.date.today().isoformat()
    desconhecidas = []
    for nome, valor in _ler_metricas(arquivo).items():
        if valor in ("", None):
            continue
        if nome not in METRICAS_REAIS + METRICAS_CAMPANHA:
            desconhecidas.append(nome)
        try:
            valor = float(str(valor).replace(",", ".")) if not isinstance(valor, (int, float)) else valor
        except ValueError:
            pass
        pub["metricas"][nome] = {"valor": valor, "fonte": fonte, "coletado_em": quando, "verificado": True}
    exigir("experimento", exp)
    return {"experimento": exp, "metricas_fora_da_lista": desconhecidas}


def anexar_predicao(exp: dict, resultado: dict) -> dict:
    exp["predicoes"].append({k: resultado.get(k) for k in ("provedor", "simulado", "status", "data", "janela", "campos_retornados",
                                                            "url_relatorio", "custo")})
    return exigir("experimento", exp)


def markdown(exp: dict) -> str:
    exigir("experimento", exp)
    v = exp["video"]
    L = [f"# Experimento {exp['id']} — {v['titulo']} ({v['versao']})", "", f"Projeto: {exp['projeto']} · gancho: {exp['tipo_gancho']}", "",
         "## Hipóteses", ""] + ([f"- {h}" for h in exp["hipoteses"]] or ["_nenhuma registrada_"])
    L += ["", "## Camadas (não misturar)", "", "| Camada | Registro |", "|---|---|",
          f"| QA técnico | {json.dumps(exp.get('qa_tecnico'), ensure_ascii=False) if exp.get('qa_tecnico') else '—'} |",
          f"| QA editorial | {json.dumps(exp.get('qa_editorial'), ensure_ascii=False) if exp.get('qa_editorial') else '—'} |",
          f"| Predição | {len(exp['predicoes'])} registro(s)" + (" (há simulados)" if any(p.get('simulado') for p in exp['predicoes']) else "") + " |",
          f"| Resultado real | {sum(len(p['metricas']) for p in exp['publicacoes'])} métrica(s) em {len(exp['publicacoes'])} publicação(ões) |"]
    for p in exp["publicacoes"]:
        L += ["", f"### {p['plataforma']} — publicado em {p['data'] or 'não publicado'}", ""]
        if p["metricas"]:
            L += ["| Métrica | Valor | Fonte | Coletado em |", "|---|---|---|---|"]
            L += [f"| {k} | {m['valor']} | {m['fonte']} | {m['coletado_em']} |" for k, m in p["metricas"].items()]
        else:
            L.append("_sem métricas reais ainda_")
    if exp["custos"]:
        L += ["", "## Custos", ""] + [f"- {c['item']}: {c['valor']} {c['moeda']} ({c['fonte']})" for c in exp["custos"]]
    return "\n".join(L) + "\n"
