"""Engenharia reversa TÉCNICA de um arquivo de vídeo (FFprobe/FFmpeg + medidas simples em quadros pequenos):
metadados, cortes aproximados, duração dos planos, frequência de mudanças visuais, movimento, cor e contraste, áudio
(intensidade, pausas, ataques) e quadros de referência para inspeção local.

São medidas do ARQUIVO. Não são retenção, nem desempenho, nem causa de sucesso.
"""
from __future__ import annotations

import datetime as dt
import math
import statistics
from operator import sub
from pathlib import Path

from . import __version__
from .midia import amostras_audio, extrair_quadro, quadros, sha256, sondar

AVISO = ("Medidas visuais e sonoras do arquivo. NÃO são métricas de retenção nem de desempenho na plataforma, "
         "e não provam o que causou o resultado de um vídeo.")
MATIZES = ["vermelho", "laranja", "amarelo", "lima", "verde", "verde-água", "ciano", "azul-celeste", "azul", "violeta",
           "magenta", "rosa"]                                    # 12 faixas de 30°
PARAMETROS = {"fps_analise": 10.0, "largura_analise": 64, "corte_limiar_abs": 25.0, "corte_fator_vizinhanca": 3.0,
              "corte_intervalo_min_s": 0.3, "mudanca_relevante_limiar": 10.0, "cor_a_cada_s": 0.5,
              "silencio_dbfs": -45.0, "som_dbfs": -40.0, "pausa_min_s": 0.3, "ataque_db": 12.0}


def _diferenca(a: bytes, b: bytes) -> float:
    """Diferença média absoluta por canal (0–255) entre dois quadros pequenos."""
    return sum(map(abs, map(sub, a, b))) / len(a)


def _cor(buf: bytes):
    n = len(buf) // 3
    sy = sy2 = ss = 0.0
    hist = [0.0] * 12
    for i in range(0, len(buf), 3):
        r, g, b = buf[i], buf[i + 1], buf[i + 2]
        y = 0.299 * r + 0.587 * g + 0.114 * b
        sy += y
        sy2 += y * y
        mx, mn = max(r, g, b), min(r, g, b)
        s = (mx - mn) / mx if mx else 0.0
        ss += s
        if s > 0.25 and mx > 40:
            d = mx - mn
            h = ((g - b) / d) % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4
            hist[int(h * 2) % 12] += s
    media = sy / n
    return media / 255, math.sqrt(max(0.0, sy2 / n - media * media)) / 255, ss / n, hist


def _matizes(hist, n=3):
    total = sum(hist)
    if total <= 0:
        return []
    ordem = sorted(range(12), key=lambda i: -hist[i])
    return [{"matiz": MATIZES[i], "peso": round(hist[i] / total, 3)} for i in ordem[:n] if hist[i] / total >= 0.05]


def _cortes(difs, p):
    cortes = []
    for i in range(1, len(difs)):
        t, d = difs[i]
        if d < p["corte_limiar_abs"]:
            continue
        viz = [difs[j][1] for j in range(max(1, i - 5), min(len(difs), i + 6)) if j != i]
        base = statistics.median(viz) if viz else 0.0
        if d >= p["corte_fator_vizinhanca"] * (base + 1) and (not cortes or t - cortes[-1]["t"] >= p["corte_intervalo_min_s"]):
            cortes.append({"t": round(t, 2), "intensidade": round(d, 1)})
    return cortes


def _audio(arquivo, info, inicio, duracao, p, taxa=16000, janela=0.1):
    if not info["tem_audio"]:
        return {"tem_audio": False, "observacao": "o arquivo não tem faixa de áudio"}
    a = amostras_audio(arquivo, taxa, inicio, duracao)
    if len(a) == 0:
        return {"tem_audio": True, "decodificado": False, "observacao": "faixa de áudio presente, mas não decodificou"}
    n = int(taxa * janela)
    dbs = []
    for i in range(0, len(a) - n + 1, n):
        bloco = a[i:i + n]
        rms = math.sqrt(sum(x * x for x in bloco) / n)
        dbs.append(20 * math.log10(rms / 32768) if rms > 0 else -120.0)
    if not dbs:
        return {"tem_audio": True, "decodificado": False, "observacao": "áudio curto demais para medir"}
    tt = lambda k: round(inicio + k * janela, 2)
    ativos = [d for d in dbs if d > p["silencio_dbfs"]]
    pausas, k = [], 0
    while k < len(dbs):
        if dbs[k] <= p["silencio_dbfs"]:
            j = k
            while j < len(dbs) and dbs[j] <= p["silencio_dbfs"]:
                j += 1
            if (j - k) * janela >= p["pausa_min_s"]:
                pausas.append({"de": tt(k), "ate": tt(j), "duracao_s": round((j - k) * janela, 2)})
            k = j
        else:
            k += 1
    primeiro = next((tt(k) for k, d in enumerate(dbs) if d > p["som_dbfs"]), None)
    ataques = sum(1 for k in range(1, len(dbs)) if dbs[k] - dbs[k - 1] >= p["ataque_db"] and dbs[k] > p["som_dbfs"])
    dur = len(dbs) * janela
    por_s = []
    por_seg = round(1 / janela)
    for s0 in range(0, len(dbs), por_seg):
        blocos = dbs[s0:s0 + por_seg]
        pot = sum(10 ** (d / 10) for d in blocos) / len(blocos)
        por_s.append(round(10 * math.log10(pot), 1) if pot > 0 else -120.0)
    return {
        "tem_audio": True, "decodificado": True,
        "primeiro_som_s": primeiro,
        "intensidade_media_dbfs": round(statistics.fmean(ativos), 1) if ativos else None,
        "variacao_db": round(statistics.pstdev(ativos), 1) if len(ativos) > 1 else 0.0,
        "pico_janela_dbfs": round(max(dbs), 1),
        "pausas": pausas, "pausas_total_s": round(sum(x["duracao_s"] for x in pausas), 2),
        "ataques": ataques, "ataques_por_minuto": round(ataques / dur * 60, 1) if dur else None,
        "dbfs_por_segundo": por_s,
    }


def _secoes(dur):
    if dur <= 6:
        return {"abertura": (0.0, dur / 2), "desenvolvimento": (dur / 2, dur / 2), "conclusao": (dur / 2, dur)}
    fim = min(max(3.0, 0.15 * dur), dur / 3)
    return {"abertura": (0.0, 3.0), "desenvolvimento": (3.0, dur - fim), "conclusao": (dur - fim, dur)}


def analisar(arquivo, inicio=0.0, duracao=None, pasta_quadros=None, parametros=None) -> dict:
    """Análise técnica completa (ou de uma janela [inicio, inicio + duracao])."""
    p = dict(PARAMETROS, **(parametros or {}))
    info = sondar(arquivo)
    total = info["duracao_s"]
    if total is not None and duracao is not None:
        duracao = min(duracao, max(0.0, total - inicio))
    difs, cores, anterior = [], [], None
    passo_cor = max(1, round(p["cor_a_cada_s"] * p["fps_analise"]))
    for i, (t, buf, _, _) in enumerate(quadros(arquivo, p["fps_analise"], p["largura_analise"], inicio, duracao)):
        difs.append((t, _diferenca(anterior, buf) if anterior is not None else 0.0))
        if i % passo_cor == 0:
            cores.append((t,) + _cor(buf))
        anterior = buf
    if not difs:
        raise ValueError(f"nenhum quadro decodificado em {info['arquivo']}")
    fim = difs[-1][0] + 1 / p["fps_analise"]
    dur = (duracao if duracao is not None else (total if total is not None else fim - inicio))
    cortes = _cortes(difs, p)
    limites = [inicio] + [c["t"] for c in cortes] + [inicio + dur]
    planos = [round(b - a, 2) for a, b in zip(limites, limites[1:]) if b - a > 0]
    t_corte = {c["t"] for c in cortes}
    mov = [d for t, d in difs[1:] if round(t, 2) not in t_corte]
    por_s = {}
    for t, d in difs[1:]:
        por_s.setdefault(int(t - inicio), []).append(d)
    serie_dif = [round(statistics.fmean(por_s[k]), 2) for k in sorted(por_s)]
    relevantes = sum(1 for x in serie_dif if x >= p["mudanca_relevante_limiar"])
    mov_medio = statistics.fmean(mov) if mov else 0.0
    nivel = "parado" if mov_medio < 2 else "baixo" if mov_medio < 6 else "medio" if mov_medio < 15 else "alto"
    hist = [sum(c[4][k] for c in cores) for k in range(12)]
    audio = _audio(arquivo, info, inicio, duracao, p)

    def resumo(a, b):
        sel_d = [d for t, d in difs[1:] if a <= t - inicio < b]
        sel_c = [c for c in cores if a <= c[0] - inicio < b]
        n_c = sum(1 for c in cortes if a <= c["t"] - inicio < b)
        r = {"de_s": round(inicio + a, 2), "ate_s": round(inicio + b, 2), "cortes": n_c,
             "cortes_por_minuto": round(n_c / (b - a) * 60, 1) if b > a else None,
             "diferenca_media": round(statistics.fmean(sel_d), 2) if sel_d else None,
             "brilho": round(statistics.fmean(c[1] for c in sel_c), 3) if sel_c else None,
             "contraste": round(statistics.fmean(c[2] for c in sel_c), 3) if sel_c else None,
             "saturacao": round(statistics.fmean(c[3] for c in sel_c), 3) if sel_c else None,
             "matizes": _matizes([sum(c[4][k] for c in sel_c) for k in range(12)]) if sel_c else []}
        if audio.get("decodificado"):
            seg = audio["dbfs_por_segundo"][int(a):max(int(a) + 1, int(math.ceil(b)))]
            vivos = [x for x in seg if x > p["silencio_dbfs"]]
            r["audio_dbfs_medio"] = round(statistics.fmean(vivos), 1) if vivos else None
            r["pausas"] = sum(1 for x in audio["pausas"] if a <= x["de"] - inicio < b)
        return r

    secoes = {nome: resumo(a, b) for nome, (a, b) in _secoes(dur).items() if b > a}
    refs = []
    if pasta_quadros:
        pasta = Path(pasta_quadros)
        alvo = {round(inicio, 2), round(inicio + min(1.0, dur), 2), round(inicio + min(3.0, max(0.0, dur - 0.05)), 2),
                round(inicio + dur / 2, 2), round(inicio + max(0.0, dur - 0.2), 2)}
        alvo |= {round(c["t"] + 0.1, 2) for c in cortes[:3]}
        for t in sorted(alvo):
            nome = f"quadro_{t:07.2f}.png"
            extrair_quadro(arquivo, t, pasta / nome)
            refs.append({"t": t, "arquivo": nome})
    limitacoes = ["cortes detectados por diferença entre quadros: transições graduais (fusões) podem não contar como corte",
                  "movimento e cor medidos em quadros reduzidos (64 px de largura) — valores aproximados"]
    if info["faltando"]:
        limitacoes.append(f"metadados não informados pelo arquivo: {', '.join(info['faltando'])}")
    if not info["tem_audio"]:
        limitacoes.append("sem áudio: ritmo sonoro, pausas e primeira fala não puderam ser medidos")
    return {
        "contrato": "analise_tecnica", "versao_biblioteca": __version__,
        "gerado_em": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "arquivo": info["arquivo"], "sha256": sha256(arquivo),
        "janela": {"inicio_s": round(inicio, 2), "duracao_s": round(dur, 2), "video_inteiro": inicio == 0 and duracao is None},
        "metadados": info,
        "cortes": cortes,
        "planos": {"quantidade": len(planos), "duracoes_s": planos,
                   "media_s": round(statistics.fmean(planos), 2) if planos else None,
                   "mediana_s": round(statistics.median(planos), 2) if planos else None,
                   "mais_longo_s": max(planos) if planos else None,
                   "primeiro_corte_s": cortes[0]["t"] if cortes else None,
                   "cortes_por_minuto": round(len(cortes) / dur * 60, 1) if dur else None},
        "visual": {"diferenca_por_segundo": serie_dif, "mudancas_relevantes": relevantes,
                   "mudancas_relevantes_por_minuto": round(relevantes / dur * 60, 1) if dur else None,
                   "movimento_medio": round(mov_medio, 2), "movimento_nivel": nivel},
        "cor": {"brilho_medio": round(statistics.fmean(c[1] for c in cores), 3),
                "contraste_medio": round(statistics.fmean(c[2] for c in cores), 3),
                "saturacao_media": round(statistics.fmean(c[3] for c in cores), 3),
                "matizes_dominantes": _matizes(hist)},
        "audio": audio,
        "secoes": secoes,
        "quadros_referencia": refs,
        "parametros": p, "aviso": AVISO, "limitacoes": limitacoes,
    }
