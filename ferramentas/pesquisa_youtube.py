# Pesquisa os vídeos MAIS VISTOS do YouTube por tema ou por canal, pela API oficial (YouTube Data API v3) com a chave gratuita
# de quem usa. Serve para achar o que já funciona (temas, títulos, duração) e criar algo ORIGINAL a partir disso.
#
#   py ferramentas/pesquisa_youtube.py tema "curiosidades sobre cachorros" --dias 365 --idioma pt --regiao BR --duracao short
#   py ferramentas/pesquisa_youtube.py canal @nomedocanal --n 25
#   py ferramentas/pesquisa_youtube.py teste          (sem internet e sem chave: confere os cálculos com dados de exemplo)
#
# Chave: variável de ambiente YOUTUBE_API_KEY ou o arquivo ~/.secrets/youtube/.env com a linha YOUTUBE_API_KEY=...
# (nunca dentro do repositório; o script nunca imprime a chave). Como criar: ver .claude/skills/pesquisa-viral/SKILL.md.
# Cota (documentação oficial conferida em 21/11/2026): 100 buscas (search.list) por dia e 10.000 unidades por dia para as outras
# consultas. Cada comando daqui gasta 1 busca e poucas unidades. A cota zera à meia-noite do horário do Pacífico.
# Saída: pesquisas/<data>-<tema|canal>-<assunto>.md (tabela para ler) e .json (dados completos).
import argparse, datetime as dt, json, os, re, statistics, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

API = "https://www.googleapis.com/youtube/v3/"
RAIZ = Path(__file__).resolve().parent.parent
HOJE = dt.datetime.now(dt.timezone.utc)


def chave():
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if k:
        return k
    arq = Path.home() / ".secrets" / "youtube" / ".env"
    if arq.exists():
        for ln in arq.read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith("YOUTUBE_API_KEY="):
                return ln.split("=", 1)[1].strip()
    sys.exit("Falta a chave da YouTube Data API. Crie o arquivo ~/.secrets/youtube/.env com a linha YOUTUBE_API_KEY=sua_chave\n"
             "(passo a passo em .claude/skills/pesquisa-viral/SKILL.md).")


def chamar(recurso, **params):
    params = {k: v for k, v in params.items() if v not in (None, "")}
    url = API + recurso + "?" + urllib.parse.urlencode({**params, "key": chave()})
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:                   # a mensagem da API não contém a chave
        corpo = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(corpo)["error"]["message"]
        except Exception:
            msg = corpo[:300]
        sys.exit(f"Erro da API do YouTube ({e.code}) em {recurso}: {msg}")
    except urllib.error.URLError as e:
        sys.exit(f"Sem conexão com a API do YouTube: {e.reason}")


def segundos(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def mmss(s):
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def montar(itens):
    """itens de videos.list → lista de dicionários com as medidas que interessam."""
    out = []
    for v in itens:
        sn, st, cd = v.get("snippet", {}), v.get("statistics", {}), v.get("contentDetails", {})
        pub = dt.datetime.fromisoformat(sn.get("publishedAt", HOJE.isoformat()).replace("Z", "+00:00"))
        dias = max(1, (HOJE - pub).days)
        views = int(st.get("viewCount", 0))
        dur = segundos(cd.get("duration"))
        out.append({"id": v["id"], "titulo": sn.get("title", ""), "canal": sn.get("channelTitle", ""), "canal_id": sn.get("channelId", ""),
                    "publicado": pub.date().isoformat(), "dias": dias, "duracao_s": dur, "formato": "curto (até 3 min)" if dur <= 180 else "longo",
                    "views": views, "likes": int(st.get("likeCount", 0)), "comentarios": int(st.get("commentCount", 0)),
                    "views_por_dia": round(views / dias), "url": f"https://www.youtube.com/watch?v={v['id']}"})
    return out


def detalhes(ids):
    itens = []
    for i in range(0, len(ids), 50):
        itens += chamar("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]), maxResults=50).get("items", [])
    return montar(itens)


def antes(dias):
    return (HOJE - dt.timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ") if dias and dias > 0 else None


def pesquisar_tema(a):
    r = chamar("search", part="snippet", type="video", q=a.assunto, order="viewCount", maxResults=min(a.n, 50),
               publishedAfter=antes(a.dias), relevanceLanguage=a.idioma, regionCode=a.regiao,
               videoDuration=a.duracao if a.duracao != "any" else None)
    vids = detalhes([x["id"]["videoId"] for x in r.get("items", [])])
    return analisar(vids, base=None), {"tipo": "tema", "assunto": a.assunto, "dias": a.dias, "idioma": a.idioma, "regiao": a.regiao, "duracao": a.duracao}


def pesquisar_canal(a):
    h = a.assunto if a.assunto.startswith("@") else "@" + a.assunto
    c = chamar("channels", part="snippet,statistics,contentDetails", forHandle=h).get("items", [])
    if not c:
        sys.exit(f"Canal {h} não encontrado.")
    c = c[0]
    info = {"tipo": "canal", "assunto": h, "canal": c["snippet"]["title"], "inscritos": int(c["statistics"].get("subscriberCount", 0)),
            "videos_no_canal": int(c["statistics"].get("videoCount", 0)), "views_do_canal": int(c["statistics"].get("viewCount", 0))}
    # linha de base: mediana de views dos últimos uploads (para o "fora da curva", parecido com o outlier do vidIQ)
    up = c["contentDetails"]["relatedPlaylists"]["uploads"]
    recentes = chamar("playlistItems", part="contentDetails", playlistId=up, maxResults=50).get("items", [])
    base_vids = detalhes([x["contentDetails"]["videoId"] for x in recentes])
    base = statistics.median([v["views"] for v in base_vids]) if base_vids else None
    info["mediana_views_ultimos_uploads"] = base
    r = chamar("search", part="snippet", type="video", channelId=c["id"], order="viewCount", maxResults=min(a.n, 50), publishedAfter=antes(a.dias))
    vids = detalhes([x["id"]["videoId"] for x in r.get("items", [])])
    return analisar(vids, base=base), info


def analisar(vids, base):
    """Ordena por views e calcula 'fora da curva' = views ÷ mediana (do canal ou do próprio resultado)."""
    vids.sort(key=lambda v: v["views"], reverse=True)
    ref = base or (statistics.median([v["views"] for v in vids]) if vids else 0)
    for v in vids:
        v["fora_da_curva"] = round(v["views"] / ref, 1) if ref else None
    return vids


def salvar(vids, info):
    pasta = RAIZ / "pesquisas"; pasta.mkdir(exist_ok=True)
    nome = f"{HOJE.date().isoformat()}-{info['tipo']}-" + (re.sub(r"[^a-z0-9]+", "-", info["assunto"].lower()).strip("-")[:40] or "x")
    (pasta / f"{nome}.json").write_text(json.dumps({"pesquisa": info, "gerado_em": HOJE.isoformat(timespec="seconds"), "videos": vids},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    ref = "mediana dos últimos uploads do canal" if info["tipo"] == "canal" else "mediana deste resultado"
    ln = [f"# Pesquisa YouTube — {info['tipo']}: {info['assunto']}", "",
          "Filtros: " + ", ".join(f"{k}={v}" for k, v in info.items() if k not in ("tipo", "assunto") and v not in (None, "", 0)), "",
          f"'Fora da curva' = views do vídeo ÷ {ref}. Acima de 3× costuma indicar um tema/título que pegou além do normal.", "",
          "| # | Título | Canal | Views | Views/dia | Fora da curva | Duração | Publicado |", "|---|---|---|---|---|---|---|---|"]
    for i, v in enumerate(vids, 1):
        t = v["titulo"].replace("|", "/")
        ln.append(f"| {i} | [{t}]({v['url']}) | {v['canal']} | {v['views']:,} | {v['views_por_dia']:,} | "
                  f"{v['fora_da_curva']}× | {mmss(v['duracao_s'])} | {v['publicado']} |".replace(",", "."))
    if vids:
        ln += ["", f"Mediana de duração: {mmss(int(statistics.median(v['duracao_s'] for v in vids)))}; "
                   f"curtos (até 3 min): {sum(v['duracao_s'] <= 180 for v in vids)} de {len(vids)}."]
    (pasta / f"{nome}.md").write_text("\n".join(ln) + "\n", encoding="utf-8")
    print("\n".join(ln[:14 + min(10, len(vids))]))
    print(f"\nsalvo em pesquisas/{nome}.md e .json ({len(vids)} vídeos)")


def teste():
    """Sem internet: dados inventados no formato da API, para conferir os cálculos e a tabela."""
    fake = [{"id": f"v{i}", "snippet": {"title": t, "channelTitle": "Canal Exemplo", "channelId": "c1",
                                         "publishedAt": (HOJE - dt.timedelta(days=d)).isoformat().replace("+00:00", "Z")},
             "statistics": {"viewCount": str(vw), "likeCount": "10", "commentCount": "2"}, "contentDetails": {"duration": du}}
            for i, (t, d, vw, du) in enumerate([("Por que X se Y?", 60, 1_300_000, "PT35M48S"), ("Como Z funciona", 30, 90_000, "PT58S"),
                                                ("O mistério de W", 200, 400_000, "PT1H2M3S"), ("Teste curto", 1, 5_000, "PT2M10S")])]
    vids = analisar(montar(fake), base=None)
    assert [v["views"] for v in vids] == [1_300_000, 400_000, 90_000, 5_000]
    assert vids[0]["duracao_s"] == 35 * 60 + 48 and vids[2]["duracao_s"] == 58 and vids[1]["duracao_s"] == 3723
    assert vids[0]["views_por_dia"] == round(1_300_000 / 60) and vids[0]["fora_da_curva"] == round(1_300_000 / 245_000, 1)
    print("teste ok: duração, views/dia e 'fora da curva' conferem")
    for v in vids:
        print(f"  {v['titulo']:<18} views={v['views']:>9,}  dur={mmss(v['duracao_s']):>8}  views/dia={v['views_por_dia']:>7,}  fora_da_curva={v['fora_da_curva']}×")


def main():
    ap = argparse.ArgumentParser(description="Vídeos mais vistos do YouTube por tema ou por canal (API oficial)")
    ap.add_argument("tipo", choices=["tema", "canal", "teste"]); ap.add_argument("assunto", nargs="?", default="")
    ap.add_argument("--n", type=int, default=25, help="quantos vídeos (máx. 50)")
    ap.add_argument("--dias", type=int, default=0, help="só vídeos publicados nos últimos N dias (0 = qualquer data)")
    ap.add_argument("--idioma", default="pt", help="idioma de relevância (ISO 639-1, ex.: pt, en)")
    ap.add_argument("--regiao", default="BR", help="país (ISO 3166-1, ex.: BR, US)")
    ap.add_argument("--duracao", default="any", choices=["any", "short", "medium", "long"], help="short < 4 min, medium 4-20, long > 20")
    a = ap.parse_args()
    if a.tipo == "teste":
        return teste()
    if not a.assunto:
        ap.error("diga o tema (entre aspas) ou o @ do canal")
    vids, info = pesquisar_tema(a) if a.tipo == "tema" else pesquisar_canal(a)
    salvar(vids, info)


if __name__ == "__main__":
    main()
