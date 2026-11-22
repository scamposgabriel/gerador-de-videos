"""CREATIVE INTELLIGENCE BRIEF: junta a referência (com a fonte de cada métrica), a análise técnica (quando há arquivo) e as
observações editoriais (escritas por quem assistiu, com intervalo de tempo e evidência) num relatório para o roteirista.

A biblioteca NÃO inventa ideias nem métricas: ganchos, hipóteses e recomendações vêm das observações editoriais; o que falta
vai para `dados_indisponiveis`. Hipóteses sobre desempenho são correlações, nunca causa comprovada.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import __version__
from .contratos import ContratoInvalido, exigir

METRICAS_REFERENCIA = ["visualizacoes", "curtidas", "comentarios", "compartilhamentos", "outlier_score", "retencao_media_pct"]
ORDEM_CONFIANCA = ["baixa", "media", "alta"]
AVISO_HIPOTESES = ("Hipóteses: o vídeo teve bom desempenho E tem estas características. Isso é correlação, não causa — "
                   "views altas não provam que uma cor, corte ou frase específica produziu o resultado.")


def _secao_de(t: float, secoes: dict, padrao: str) -> str:
    for nome, s in secoes.items():
        if s["de_s"] <= t < s["ate_s"]:
            return nome
    return padrao


def _observacoes_planas(obs: dict):
    """(seção de origem, rótulo, observação) para cada observação com texto."""
    for secao in ("abertura", "desenvolvimento", "conclusao"):
        for rotulo, valor in obs[secao].items():
            for item in (valor if isinstance(valor, list) else [valor]):
                if isinstance(item, dict) and "texto" in item:
                    yield secao, rotulo, item
    for rotulo in ("estilo_visual", "audio"):
        yield "desenvolvimento", rotulo, obs[rotulo]
    for item in obs["animacao"]:
        yield "desenvolvimento", "animacao", item


def confianca_geral(referencia: dict, observacoes: dict, analise: dict | None) -> tuple[str, list[str]]:
    motivos = []
    nivel = min((h["confianca"] for h in observacoes["hipoteses"]), key=ORDEM_CONFIANCA.index)
    verificadas = [m for m in referencia["metricas"].values() if m.get("verificado") and m.get("valor") is not None]
    teto = "alta"
    if analise is None:
        teto = "media"
        motivos.append("sem análise técnica do arquivo")
    if not verificadas:
        teto = min(teto, "media", key=ORDEM_CONFIANCA.index)
        motivos.append("nenhuma métrica verificada em fonte oficial")
    if referencia["acesso_ao_video"] == "sem_acesso":
        teto = "baixa"
        motivos.append("sem acesso ao vídeo (só descrição)")
    final = min(nivel, teto, key=ORDEM_CONFIANCA.index)
    if final != nivel:
        motivos.insert(0, f"rebaixada de '{nivel}' para '{final}'")
    return final, motivos


def dados_indisponiveis(referencia: dict, observacoes: dict, analise: dict | None) -> list[str]:
    falta = []
    for m in METRICAS_REFERENCIA:
        reg = referencia["metricas"].get(m)
        if reg is None or reg.get("valor") is None:
            falta.append(f"métrica '{m}' não informada")
    if analise is None:
        falta.append("análise técnica do arquivo (vídeo não disponível para análise local)")
    else:
        falta += [f"metadado '{k}' não informado pelo arquivo" for k in analise["metadados"].get("faltando", [])]
        if not analise["audio"].get("decodificado"):
            falta.append("medidas de áudio (sem áudio decodificável)")
    for secao, campos in (("abertura", ["tempo_ate_assunto_s"]), ("desenvolvimento", ["mudancas_visuais", "humor", "comparacoes", "suspense"]),
                          ("conclusao", ["convite_interacao", "repeticao_natural"])):
        for c in campos:
            if observacoes[secao].get(c) is None:
                falta.append(f"{secao}.{c} não registrado na análise editorial")
    if referencia["metricas"].get("retencao_media_pct") is None:
        falta.append("retenção real do vídeo de referência (só o dono do canal tem esse dado)")
    return list(dict.fromkeys(falta))


def montar(referencia: dict, observacoes: dict, analise: dict | None = None) -> dict:
    exigir("referencia", referencia)
    exigir("observacoes_editoriais", observacoes)
    for nome, d in (("referência", referencia), ("observações", observacoes)):
        if "PREENCHER" in json.dumps(d, ensure_ascii=False):
            raise ContratoInvalido(f"{nome}: ainda há campos 'PREENCHER' — complete antes de gerar o brief")
    if observacoes["referencia_id"] != referencia["id"]:
        raise ContratoInvalido(f"observações são de '{observacoes['referencia_id']}', referência é '{referencia['id']}'")
    if analise is not None and referencia.get("arquivo_video") and analise["arquivo"] != referencia["arquivo_video"]:
        raise ContratoInvalido(f"análise técnica é de '{analise['arquivo']}', referência aponta '{referencia['arquivo_video']}'")
    secoes = analise["secoes"] if analise else {}
    mapa = {nome: {"secao": nome, "de_s": s["de_s"], "ate_s": s["ate_s"], "tecnico": s, "observacoes": []}
            for nome, s in secoes.items()}
    for nome in ("abertura", "desenvolvimento", "conclusao"):
        mapa.setdefault(nome, {"secao": nome, "de_s": None, "ate_s": None, "tecnico": None, "observacoes": []})
    for origem, rotulo, item in _observacoes_planas(observacoes):
        alvo = _secao_de(item["intervalo"][0], secoes, origem) if item.get("intervalo") and secoes else origem
        mapa[alvo]["observacoes"].append(dict(item, rotulo=rotulo))
    for m in mapa.values():
        m["observacoes"].sort(key=lambda o: (o.get("intervalo") or [1e9])[0])
    nivel, motivos = confianca_geral(referencia, observacoes, analise)
    ab, de, co = observacoes["abertura"], observacoes["desenvolvimento"], observacoes["conclusao"]
    tec = analise or {}
    return {
        "contrato": "creative_intelligence_brief", "versao_biblioteca": __version__,
        "gerado_em": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "referencia": {k: referencia.get(k) for k in ("id", "plataforma", "url", "criador", "tema", "titulo", "coletado_em",
                                                       "publicado_em", "duracao_s", "acesso_ao_video")},
        "duracao_s": (tec.get("metadados") or {}).get("duracao_s") or referencia.get("duracao_s"),
        "metricas": referencia["metricas"],
        "fontes_metricas": sorted({m["fonte"] for m in referencia["metricas"].values()}),
        "gancho_inicial": {"primeira_imagem": ab["primeira_imagem"], "primeira_fala": ab["primeira_fala"],
                           "promessa_ou_pergunta": ab["promessa_ou_pergunta"], "elemento_curiosidade": ab["elemento_curiosidade"],
                           "tempo_ate_assunto_s": ab.get("tempo_ate_assunto_s"),
                           "tecnico_abertura": secoes.get("abertura")},
        "mapa_temporal": [mapa[n] for n in ("abertura", "desenvolvimento", "conclusao")],
        "estrutura_narrativa": {"progressao": de["progressao"], "revelacoes": de["revelacoes"], "resolucao": co["resolucao"],
                                "recompensa": co["recompensa"], "encerramento": co["encerramento"],
                                "convite_interacao": co.get("convite_interacao"), "repeticao_natural": co.get("repeticao_natural")},
        "tecnicas_animacao": observacoes["animacao"],
        "ritmo": {"editorial": de["ritmo"],
                  "tecnico": {"planos": tec.get("planos"), "mudancas_relevantes_por_minuto": (tec.get("visual") or {}).get("mudancas_relevantes_por_minuto"),
                              "movimento_nivel": (tec.get("visual") or {}).get("movimento_nivel"),
                              "ataques_sonoros_por_minuto": (tec.get("audio") or {}).get("ataques_por_minuto")} if analise else None},
        "estilo_visual": {"editorial": observacoes["estilo_visual"], "tecnico": tec.get("cor")},
        "audio": {"editorial": observacoes["audio"], "tecnico": tec.get("audio")},
        "tecnicas_transferiveis": observacoes["tecnicas_transferiveis"],
        "nao_copiar": observacoes["nao_copiar"],
        "hipoteses": observacoes["hipoteses"], "aviso_hipoteses": AVISO_HIPOTESES,
        "nivel_confianca": nivel, "motivos_confianca": motivos,
        "dados_indisponiveis": dados_indisponiveis(referencia, observacoes, analise),
        "recomendacoes_roteirista": observacoes["recomendacoes"],
        "limitacoes": (tec.get("limitacoes") or []) + ["observações editoriais são de quem assistiu; confira a evidência de cada uma"],
        "aviso_tecnico": tec.get("aviso"),
    }


def _obs_md(o) -> str:
    if not o:
        return "_não registrado_"
    iv = f" `{o['intervalo'][0]:.1f}–{o['intervalo'][1]:.1f} s`" if o.get("intervalo") else ""
    return f"{o['texto']}{iv} — _{o['tipo'].replace('_', ' ')}; evidência: {o['evidencia']}_"


def markdown(b: dict) -> str:
    r = b["referencia"]
    L = [f"# Creative Intelligence Brief — {r['id']}", "",
         f"**{r.get('titulo') or r['tema']}** · {r['plataforma']} · criador: {r['criador']} · coletado em {r['coletado_em']}",
         f"URL: {r['url']}", f"Duração: {b['duracao_s'] if b['duracao_s'] is not None else 'não informada'} s · "
         f"acesso ao vídeo: {r['acesso_ao_video']} · **confiança geral: {b['nivel_confianca']}**"
         + (f" ({'; '.join(b['motivos_confianca'])})" if b['motivos_confianca'] else ""), "",
         "> Inteligência criativa para produzir algo ORIGINAL. Não é roteiro para copiar.", "", "## Métricas (com fonte)", ""]
    if b["metricas"]:
        L += ["| Métrica | Valor | Fonte | Coletado em | Verificado |", "|---|---|---|---|---|"]
        L += [f"| {k} | {m['valor']} | {m['fonte']} | {m['coletado_em']} | {'sim' if m['verificado'] else 'não'} |" for k, m in b["metricas"].items()]
    else:
        L.append("_nenhuma métrica informada_")
    g = b["gancho_inicial"]
    L += ["", "## Gancho inicial", "", f"- Primeira imagem: {_obs_md(g['primeira_imagem'])}", f"- Primeira fala: {_obs_md(g['primeira_fala'])}",
          f"- Promessa ou pergunta: {_obs_md(g['promessa_ou_pergunta'])}", f"- Curiosidade: {_obs_md(g['elemento_curiosidade'])}",
          f"- Tempo até o assunto: {str(g['tempo_ate_assunto_s']) + ' s' if g['tempo_ate_assunto_s'] is not None else 'não registrado'}"]
    if g["tecnico_abertura"]:
        t = g["tecnico_abertura"]
        L.append(f"- Medidas da abertura ({t['de_s']}–{t['ate_s']} s): {t['cortes']} corte(s), diferença visual média {t['diferenca_media']}, "
                 f"brilho {t['brilho']}, contraste {t['contraste']}, saturação {t['saturacao']}")
    L += ["", "## Mapa temporal", ""]
    for m in b["mapa_temporal"]:
        faixa = f" ({m['de_s']}–{m['ate_s']} s)" if m["de_s"] is not None else ""
        L.append(f"### {m['secao'].capitalize()}{faixa}")
        if m["tecnico"]:
            t = m["tecnico"]
            L.append(f"Medidas: {t['cortes']} corte(s) ({t['cortes_por_minuto']}/min), diferença visual {t['diferenca_media']}, "
                     f"matizes {', '.join(x['matiz'] for x in t['matizes']) or '—'}"
                     + (f", áudio {t.get('audio_dbfs_medio')} dBFS, {t.get('pausas')} pausa(s)" if 'pausas' in t else ""))
        L += [f"- **{o['rotulo']}**: {_obs_md(o)}" for o in m["observacoes"]] or ["- _sem observações_"]
        L.append("")
    if b["ritmo"]["tecnico"]:
        t = b["ritmo"]["tecnico"]
        pl = t["planos"] or {}
        L += ["## Ritmo", "", f"- Editorial: {_obs_md(b['ritmo']['editorial'])}",
              f"- Planos: {pl.get('quantidade')} (média {pl.get('media_s')} s, mais longo {pl.get('mais_longo_s')} s); "
              f"mudanças visuais relevantes: {t['mudancas_relevantes_por_minuto']}/min; movimento: {t['movimento_nivel']}; "
              f"ataques sonoros: {t['ataques_sonoros_por_minuto']}/min", ""]
    L += ["## Técnicas transferíveis", ""] + [f"- {x}" for x in b["tecnicas_transferiveis"]]
    L += ["", "## Não copiar (identidade do outro criador)", ""] + [f"- {x}" for x in b["nao_copiar"]]
    L += ["", "## Hipóteses sobre o desempenho", "", f"> {b['aviso_hipoteses']}", ""]
    L += [f"- ({h['confianca']}) {h['hipotese']} — base: {h['base']}" for h in b["hipoteses"]]
    rec = b["recomendacoes_roteirista"]
    L += ["", "## Para o roteirista", "", "**Três ganchos originais**", ""] + [f"{i}. {x}" for i, x in enumerate(rec["ganchos"], 1)]
    for titulo, chave in (("Progressão narrativa", "progressao"), ("Demonstrações visuais", "demonstracoes"),
                          ("Ritmo", "ritmo"), ("Riscos de originalidade", "riscos_originalidade")):
        L += ["", f"**{titulo}**", ""] + [f"- {x}" for x in rec[chave]]
    L += ["", f"**Estratégia editorial:** {rec['estrategia']}", "", "## Dados indisponíveis", ""] + [f"- {x}" for x in b["dados_indisponiveis"]]
    L += ["", "## Limitações", ""] + [f"- {x}" for x in b["limitacoes"]]
    if b.get("aviso_tecnico"):
        L += ["", f"> {b['aviso_tecnico']}"]
    return "\n".join(L) + "\n"


def salvar(b: dict, pasta) -> tuple[Path, Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    j, m = pasta / "creative_intelligence_brief.json", pasta / "CREATIVE_INTELLIGENCE_BRIEF.md"
    j.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    m.write_text(markdown(b), encoding="utf-8")
    return j, m
