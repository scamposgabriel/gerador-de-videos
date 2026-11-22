"""Provedores de pesquisa e de metadados de referências. Cada métrica guarda valor, fonte, data de coleta e se foi verificada.

- `YouTubeDataAPI`: metadados oficiais de um vídeo (videos.list) com a chave de quem usa (YOUTUBE_API_KEY ou ~/.secrets/youtube/.env).
- `EntradaManual`: números colados pelo usuário de outra ferramenta (vidIQ, TikTok Creative Center, painel do Instagram),
  sempre com a fonte. É o caminho quando não há integração oficial conectada.

Sem scraping, sem cookies, sem baixar vídeos de terceiros. Se o vidIQ estiver conectado ao Claude Code como MCP, a skill usa a
ferramenta dele e grava o resultado aqui como entrada manual (fonte "vidIQ (MCP)").
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from pathlib import Path

NOTA_VIDIQ = ("vidIQ: não há API aberta. Use o MCP do vidIQ se estiver conectado ao Claude Code (confira as ferramentas "
              "disponíveis); senão, cole os números (outlier, palavra-chave) num arquivo de entrada manual com a fonte.")


class ErroPesquisa(Exception):
    pass


def _agora() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def metrica(valor, fonte: str, verificado: bool, coletado_em: str | None = None, observacao: str | None = None) -> dict:
    m = {"valor": valor, "fonte": fonte, "coletado_em": coletado_em or _agora(), "verificado": verificado}
    if observacao:
        m["observacao"] = observacao
    return m


class ProvedorMetadados(ABC):
    nome = "base"

    @abstractmethod
    def referencia(self, identificador: str, tema: str) -> dict:
        """Contrato `referencia` com o que a fonte realmente informa."""


class EntradaManual(ProvedorMetadados):
    """Arquivo JSON {"referencia": {...}, "metricas": {nome: {"valor", "fonte"}}} preenchido à mão."""
    nome = "manual"

    def __init__(self, arquivo):
        self.arquivo = Path(arquivo)

    def referencia(self, identificador=None, tema=None) -> dict:
        d = json.loads(self.arquivo.read_text(encoding="utf-8"))
        ref = dict(d["referencia"])
        ref.setdefault("coletado_em", _agora())
        ref.setdefault("acesso_ao_video", "somente_metadados")
        ref["metricas"] = {}
        for nome, m in (d.get("metricas") or {}).items():
            if m.get("valor") in (None, ""):
                continue                                          # não informado: fica fora (vai para dados indisponíveis)
            if not m.get("fonte"):
                raise ErroPesquisa(f"métrica '{nome}' sem fonte: toda métrica precisa dizer de onde veio")
            ref["metricas"][nome] = metrica(m["valor"], m["fonte"], bool(m.get("verificado", False)), m.get("coletado_em"),
                                            m.get("observacao"))
        return ref


def _chave_youtube() -> str:
    k = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if k:
        return k
    arq = Path.home() / ".secrets" / "youtube" / ".env"
    if arq.exists():
        for ln in arq.read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith("YOUTUBE_API_KEY="):
                return ln.split("=", 1)[1].strip()
    raise ErroPesquisa("falta a chave da YouTube Data API (YOUTUBE_API_KEY ou ~/.secrets/youtube/.env)")


def id_youtube(texto: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", texto)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", texto):
        return texto
    raise ErroPesquisa(f"não reconheci um ID de vídeo do YouTube em: {texto[:80]}")


def _segundos(iso: str):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


class YouTubeDataAPI(ProvedorMetadados):
    nome = "youtube_data_api"
    FONTE = "YouTube Data API v3 (videos.list)"

    def __init__(self, chave: str | None = None, obter=None):
        self._chave = chave
        self._obter = obter or self._http                        # injetável nos testes (sem rede)

    def _http(self, url: str) -> dict:
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:                       # a mensagem da API não contém a chave
            raise ErroPesquisa(f"YouTube Data API respondeu {e.code}") from None
        except urllib.error.URLError as e:
            raise ErroPesquisa(f"sem conexão com a YouTube Data API: {e.reason}") from None

    def referencia(self, identificador: str, tema: str) -> dict:
        vid = id_youtube(identificador)
        q = urllib.parse.urlencode({"part": "snippet,statistics,contentDetails", "id": vid, "key": self._chave or _chave_youtube()})
        d = self._obter(f"https://www.googleapis.com/youtube/v3/videos?{q}")
        itens = d.get("items") or []
        if not itens:
            raise ErroPesquisa(f"vídeo {vid} não encontrado ou não público")
        it = itens[0]
        sn, st, cd = it.get("snippet", {}), it.get("statistics", {}), it.get("contentDetails", {})
        agora = _agora()
        met = {}
        for nome, chave in (("visualizacoes", "viewCount"), ("curtidas", "likeCount"), ("comentarios", "commentCount")):
            if st.get(chave) is not None:
                met[nome] = metrica(int(st[chave]), self.FONTE, True, agora)
        pub = sn.get("publishedAt")
        if pub and "visualizacoes" in met:
            dias = max(1.0, (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(pub.replace("Z", "+00:00"))).total_seconds() / 86400)
            met["visualizacoes_por_dia"] = metrica(round(met["visualizacoes"]["valor"] / dias, 1), self.FONTE + " (calculado)", True, agora)
        return {"contrato": "referencia", "id": f"youtube-{vid}", "plataforma": "youtube", "url": f"https://www.youtube.com/watch?v={vid}",
                "criador": sn.get("channelTitle") or "desconhecido", "tema": tema, "titulo": sn.get("title"), "coletado_em": agora,
                "publicado_em": pub, "duracao_s": _segundos(cd.get("duration")), "metricas": met,
                "acesso_ao_video": "somente_metadados",
                "observacoes": "A API não entrega o arquivo nem a transcrição de vídeos de terceiros; a análise editorial é feita "
                               "assistindo no próprio YouTube."}
