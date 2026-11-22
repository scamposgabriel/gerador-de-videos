"""Comparação A/B de duas aberturas PRÓPRIAS: mede as duas na mesma janela e registra diferenças e a hipótese da versão B.

Diferença técnica não prova que uma versão retém mais. A comparação prepara o experimento; quem decide é o resultado real.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import __version__
from .tecnica import analisar

AVISO = ("Comparação de características técnicas na mesma janela de tempo. Não afirma que uma versão é melhor: score maior de "
         "um preditor ou mais cortes não comprovam retenção. Confronte com as métricas reais depois de publicar.")

MEDIDAS = [  # (rótulo, função que extrai da análise, casas decimais)
    ("primeiro corte (s)", lambda a: a["planos"]["primeiro_corte_s"], 2),
    ("cortes na janela", lambda a: len(a["cortes"]), 0),
    ("cortes por minuto", lambda a: a["planos"]["cortes_por_minuto"], 1),
    ("duração média do plano (s)", lambda a: a["planos"]["media_s"], 2),
    ("mudanças visuais relevantes por minuto", lambda a: a["visual"]["mudancas_relevantes_por_minuto"], 1),
    ("movimento médio (0–255)", lambda a: a["visual"]["movimento_medio"], 2),
    ("brilho médio (0–1)", lambda a: a["cor"]["brilho_medio"], 3),
    ("contraste médio (0–1)", lambda a: a["cor"]["contraste_medio"], 3),
    ("saturação média (0–1)", lambda a: a["cor"]["saturacao_media"], 3),
    ("primeiro som (s)", lambda a: a["audio"].get("primeiro_som_s"), 2),
    ("intensidade sonora média (dBFS)", lambda a: a["audio"].get("intensidade_media_dbfs"), 1),
    ("pausas sonoras", lambda a: len(a["audio"].get("pausas", [])) if a["audio"].get("decodificado") else None, 0),
    ("ataques sonoros por minuto", lambda a: a["audio"].get("ataques_por_minuto"), 1),
    ("abertura 0–3 s: diferença visual média", lambda a: (a["secoes"].get("abertura") or {}).get("diferenca_media"), 2),
]


def _resumo(a: dict) -> dict:
    out = {}
    for rotulo, f, casas in MEDIDAS:
        try:
            v = f(a)
        except (KeyError, TypeError):
            v = None
        out[rotulo] = None if v is None else round(v, casas) if casas else int(v)
    out["matizes dominantes"] = ", ".join(x["matiz"] for x in a["cor"]["matizes_dominantes"]) or "—"
    return out


def comparar(arquivo_a, arquivo_b, janela=15.0, hipotese="", rotulos=("A", "B"), pasta_quadros=None, inicio=0.0) -> dict:
    if not hipotese.strip():
        raise ValueError("registre a hipótese criativa da versão B (o que mudou e por que deveria funcionar)")
    analises = []
    for arq, rot in zip((arquivo_a, arquivo_b), rotulos):
        pq = Path(pasta_quadros) / rot if pasta_quadros else None
        analises.append(analisar(arq, inicio=inicio, duracao=janela, pasta_quadros=pq))
    ra, rb = (_resumo(x) for x in analises)
    diferencas = []
    for rotulo in ra:
        va, vb = ra[rotulo], rb[rotulo]
        delta = round(vb - va, 3) if isinstance(va, (int, float)) and isinstance(vb, (int, float)) else None
        diferencas.append({"medida": rotulo, rotulos[0]: va, rotulos[1]: vb, "delta_b_menos_a": delta})
    return {
        "contrato": "comparacao_ab", "versao_biblioteca": __version__,
        "gerado_em": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "janela": {"inicio_s": inicio, "duracao_s": janela},
        "versoes": {rotulos[0]: {"arquivo": analises[0]["arquivo"], "sha256": analises[0]["sha256"],
                                 "duracao_total_s": analises[0]["metadados"]["duracao_s"]},
                    rotulos[1]: {"arquivo": analises[1]["arquivo"], "sha256": analises[1]["sha256"],
                                 "duracao_total_s": analises[1]["metadados"]["duracao_s"]}},
        "hipotese_versao_b": hipotese,
        "diferencas": diferencas,
        "analises": {rotulos[0]: analises[0], rotulos[1]: analises[1]},
        "predicoes": {},                         # preenchido só com resultados reais (ou simulados, marcados) de um provedor
        "resultado_real": None,                  # preenchido depois de publicar (contrato experimento)
        "aviso": AVISO,
    }


def anexar_predicao(comp: dict, rotulo: str, resultado: dict) -> dict:
    comp["predicoes"][rotulo] = {"provedor": resultado["provedor"], "simulado": resultado["simulado"], "status": resultado["status"],
                                 "campos_retornados": resultado["campos_retornados"], "url_relatorio": resultado.get("url_relatorio")}
    return comp


def markdown(c: dict) -> str:
    ra, rb = list(c["versoes"])
    L = [f"# Comparação de ganchos — {ra} × {rb}", "",
         f"Janela: {c['janela']['inicio_s']}–{c['janela']['inicio_s'] + c['janela']['duracao_s']} s · gerado em {c['gerado_em']}", "",
         f"> {c['aviso']}", "", "## Versões", ""]
    for r, v in c["versoes"].items():
        L.append(f"- **{r}**: `{v['arquivo']}` (duração total {v['duracao_total_s']} s, sha256 {v['sha256'][:12]}…)")
    L += ["", f"**Hipótese criativa da versão {rb}:** {c['hipotese_versao_b']}", "", "## Medidas técnicas na janela", "",
          f"| Medida | {ra} | {rb} | {rb} − {ra} |", "|---|---|---|---|"]
    for d in c["diferencas"]:
        fmt = lambda x: "—" if x is None else x
        L.append(f"| {d['medida']} | {fmt(d[ra])} | {fmt(d[rb])} | {fmt(d['delta_b_menos_a'])} |")
    L += ["", "## Predição", ""]
    if c["predicoes"]:
        for r, p in c["predicoes"].items():
            tag = " (SIMULADO — não é resultado real)" if p["simulado"] else ""
            L.append(f"- {r}: {p['provedor']}{tag}, status {p['status']}, campos: {json.dumps(p['campos_retornados'], ensure_ascii=False)}")
    else:
        L.append("_nenhuma predição executada (opcional; exige autorização e créditos)_")
    L += ["", "## Próximo passo", "", "Publicar (com aprovação) e registrar as métricas reais no contrato `experimento` para "
          "confrontar esta hipótese com o resultado observado."]
    return "\n".join(L) + "\n"


def salvar(c: dict, pasta) -> tuple[Path, Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    j, m = pasta / "comparacao_ganchos.json", pasta / "COMPARACAO_GANCHOS.md"
    j.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    m.write_text(markdown(c), encoding="utf-8")
    return j, m
