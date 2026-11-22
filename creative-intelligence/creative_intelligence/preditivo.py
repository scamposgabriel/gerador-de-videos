"""Avaliação PREDITIVA opcional (pré-publicação) por provedor externo, atrás de uma interface genérica.

- `HiggsfieldViralityProvider`: Virality Predictor da Higgsfield pela CLI oficial (`higgsfield`), job `brain_activity`.
  A CLI SOBE qualquer arquivo passado em `--video`; por isso nada é chamado com o vídeo sem autorização (`autorizacao.py`).
- `ProvedorSimulado`: respostas falsas e determinísticas para testes e demonstrações — sempre marcadas `simulado: true`.

Pontuação de um preditor NÃO é probabilidade demonstrada de viralizar (90/100 não é 90% de chance). Nenhum limite de nota é
condição para publicar. Campos que o provedor não devolveu não são preenchidos.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from .autorizacao import Politica, exigir as exigir_autorizacao
from .midia import integro, recortar, sha256, sondar

JANELA_PADRAO_S = 15.0       # janela anunciada na página do Virality Predictor (conferir antes de usar)
AVISO = ("Pontuação de modelo preditivo: estimativa, não probabilidade demonstrada de viralização nem garantia de retenção. "
         "Não use como condição obrigatória para publicar; confronte com as métricas reais.")
SENSIVEIS = re.compile(r"token|secret|senha|password|authorization|api[_-]?key|cookie|email|e-mail", re.I)


class ErroProvedor(Exception):
    pass


class NaoAutenticado(ErroProvedor):
    pass


def _limpar(obj):
    """Remove do retorno bruto qualquer chave com cara de segredo ou dado pessoal."""
    if isinstance(obj, dict):
        return {k: _limpar(v) for k, v in obj.items() if not SENSIVEIS.search(str(k))}
    if isinstance(obj, list):
        return [_limpar(x) for x in obj]
    return obj


def _buscar(obj, padrao: re.Pattern, prefixo=""):
    """(caminho, valor) de todas as chaves que casam com o padrão, em qualquer nível."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            cam = f"{prefixo}.{k}" if prefixo else str(k)
            if padrao.search(str(k)) and not isinstance(v, (dict, list)):
                yield cam, v
            yield from _buscar(v, padrao, cam)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _buscar(v, padrao, f"{prefixo}[{i}]")


class ProvedorPreditivo(ABC):
    nome = "base"
    ferramenta = ""
    externo = True                     # envia o material para fora da máquina?

    @abstractmethod
    def disponivel(self) -> dict: ...

    @abstractmethod
    def autenticacao(self) -> dict: ...

    def creditos(self) -> dict:
        return {"saldo": None, "detalhe": "provedor não informa créditos"}

    def estimar_custo(self) -> dict:
        return {"estimado": None, "detalhe": "provedor não estima custo"}

    @abstractmethod
    def analisar(self, clipe: Path) -> dict:
        """Retorno bruto do provedor (já sem segredos)."""

    @abstractmethod
    def interpretar(self, bruto: dict) -> dict:
        """Só os campos realmente devolvidos: {campos_retornados, url_relatorio, custo}."""


class ProvedorSimulado(ProvedorPreditivo):
    """Para testes e POC. Modos: ok, falha_autenticacao, falha_provedor. Nunca use como resultado real."""
    nome = "simulado"
    ferramenta = "simulador local (sem modelo)"
    externo = False

    def __init__(self, modo="ok"):
        self.modo = modo

    def disponivel(self):
        return {"disponivel": True, "detalhe": "simulador local"}

    def autenticacao(self):
        return {"autenticado": self.modo != "falha_autenticacao", "detalhe": "simulado"}

    def creditos(self):
        return {"saldo": 100, "detalhe": "SIMULADO"}

    def estimar_custo(self):
        return {"estimado": 1, "detalhe": "SIMULADO"}

    def analisar(self, clipe):
        if self.modo == "falha_autenticacao":
            raise NaoAutenticado("simulado: sessão expirada")
        if self.modo == "falha_provedor":
            raise ErroProvedor("simulado: serviço indisponível (HTTP 503)")
        h = int(hashlib.sha256(Path(clipe).read_bytes()).hexdigest()[:8], 16)
        return {"id": f"sim-{h:08x}", "status": "completed", "scores": {"hook": 40 + h % 50, "attention": 30 + (h >> 8) % 60},
                "peak_attention_s": round((h % 140) / 10, 1), "report_url": "https://example.invalid/relatorio-simulado",
                "credits_used": 1}

    def interpretar(self, bruto):
        return {"campos_retornados": {"scores": bruto["scores"], "momento_maior_atencao_s": bruto["peak_attention_s"]},
                "url_relatorio": bruto["report_url"], "custo": {"valor": bruto["credits_used"], "unidade": "créditos (SIMULADO)"},
                "id_externo": bruto["id"]}


class HiggsfieldViralityProvider(ProvedorPreditivo):
    """Virality Predictor (job `brain_activity`) pela CLI oficial da Higgsfield (github.com/higgsfield-ai/cli)."""
    nome = "higgsfield"
    ferramenta = "Higgsfield Virality Predictor (CLI, job brain_activity)"
    externo = True
    PONTUACOES = re.compile(r"score|virality|hook|attention|retention|engagement|distraction|potential", re.I)
    URLS = re.compile(r"report|result_url|url", re.I)
    CUSTOS = re.compile(r"cost|credit|price", re.I)

    def __init__(self, comando=None, timeout_s=900):
        self.comando = list(comando) if comando else None
        self.timeout_s = timeout_s

    def _cmd(self) -> list[str]:
        if self.comando:
            return self.comando
        achado = shutil.which("higgsfield")
        if not achado:
            raise ErroProvedor("CLI 'higgsfield' não instalada (ver docs: npm install -g @higgsfield/cli, ou brew/curl)")
        return [achado]

    def _rodar(self, *args, timeout=60) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(self._cmd() + list(args), capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise ErroProvedor(f"tempo esgotado ({timeout} s) em 'higgsfield {' '.join(args[:3])}'") from e
        except OSError as e:
            raise ErroProvedor(f"não consegui executar a CLI da Higgsfield: {e}") from e

    @staticmethod
    def _json(texto: str):
        texto = (texto or "").strip()
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            ini = min([i for i in (texto.find("{"), texto.find("[")) if i >= 0], default=-1)
            if ini >= 0:
                try:
                    return json.loads(texto[ini:])
                except json.JSONDecodeError:
                    pass
        return None

    @staticmethod
    def _sem_login(r) -> bool:
        return bool(re.search(r"not authenticated|session expired|unauthori[sz]ed|login", (r.stderr or "") + (r.stdout or ""), re.I))

    def disponivel(self):
        try:
            r = self._rodar("version", timeout=30)
        except ErroProvedor as e:
            return {"disponivel": False, "detalhe": str(e)}
        return {"disponivel": r.returncode == 0, "detalhe": (r.stdout or r.stderr).strip()[:120]}

    def autenticacao(self):
        """Só diz se há sessão; não guarda conta, e-mail nem token."""
        try:
            r = self._rodar("account", "status", "--json", timeout=60)
        except ErroProvedor as e:
            return {"autenticado": None, "detalhe": str(e)}
        if r.returncode == 0:
            return {"autenticado": True, "detalhe": "sessão ativa"}
        return {"autenticado": False if self._sem_login(r) else None,
                "detalhe": "rode `higgsfield auth login`" if self._sem_login(r) else (r.stderr or "").strip()[:160]}

    def creditos(self):
        try:
            r = self._rodar("account", "status", "--json", timeout=60)
        except ErroProvedor as e:
            return {"saldo": None, "detalhe": str(e)}
        d = _limpar(self._json(r.stdout)) if r.returncode == 0 else None
        achados = dict(_buscar(d, re.compile(r"credit|balance", re.I))) if d else {}
        return {"saldo": achados or None, "detalhe": "lido de `higgsfield account status --json`" if achados else
                "a CLI não informou saldo; confira em `higgsfield account` ou no site"}

    def estimar_custo(self):
        """Tenta estimar SEM mandar o vídeo. Se a CLI exigir o arquivo, não estima (estimar enviaria o vídeo)."""
        try:
            r = self._rodar("generate", "cost", "brain_activity", "--json", timeout=60)
        except ErroProvedor as e:
            return {"estimado": None, "detalhe": str(e)}
        d = self._json(r.stdout) if r.returncode == 0 else None
        valores = [v for _, v in _buscar(d, self.CUSTOS) if isinstance(v, (int, float))] if d else []
        if valores:
            return {"estimado": float(valores[0]), "detalhe": "estimativa da CLI (`generate cost brain_activity`)"}
        return {"estimado": None, "detalhe": "a CLI não estimou o custo sem o vídeo; estimar com o vídeo o enviaria (envio externo)"}

    def analisar(self, clipe):
        minutos = max(1, int(self.timeout_s // 60))
        r = self._rodar("generate", "create", "brain_activity", "--video", str(clipe), "--wait", "--wait-timeout", f"{minutos}m",
                        "--json", timeout=self.timeout_s + 60)
        if r.returncode != 0:
            if self._sem_login(r):
                raise NaoAutenticado("Higgsfield: sessão ausente ou expirada — rode `higgsfield auth login`")
            raise ErroProvedor(f"Higgsfield falhou (código {r.returncode}): {(r.stderr or r.stdout).strip()[:300]}")
        d = self._json(r.stdout)
        if d is None:
            raise ErroProvedor("a CLI não devolveu JSON legível; resultado não registrado")
        return _limpar(d)

    def interpretar(self, bruto):
        campos = {cam: v for cam, v in _buscar(bruto, self.PONTUACOES) if isinstance(v, (int, float, str))}
        url = next((v for _, v in _buscar(bruto, self.URLS) if isinstance(v, str) and v.startswith("http")), None)
        custo = {cam: v for cam, v in _buscar(bruto, self.CUSTOS) if isinstance(v, (int, float))}
        ident = next((v for cam, v in _buscar(bruto, re.compile(r"^(job_)?id$", re.I))), None)
        return {"campos_retornados": campos, "url_relatorio": url, "custo": custo or None, "id_externo": ident}


PROVEDORES = {"higgsfield": HiggsfieldViralityProvider, "simulado": ProvedorSimulado}


def preparar_clipe(video, pasta, inicio=0.0, janela=JANELA_PADRAO_S) -> dict:
    """Recorta a abertura (com áudio), confere duração e integridade. Nada é enviado aqui."""
    info = sondar(video)
    total = info["duracao_s"]
    dur = min(janela, total - inicio) if total else janela
    if dur <= 0:
        raise ValueError(f"início {inicio} s fora do vídeo ({total} s)")
    clipe = recortar(video, inicio, dur, Path(pasta) / f"clipe_{Path(video).stem}_{inicio:g}s_{dur:g}s.mp4")
    ci = sondar(clipe)
    ok, erros = integro(clipe)
    problemas = []
    if not ok:
        problemas.append(f"clipe não íntegro: {erros}")
    if ci["duracao_s"] is None or ci["duracao_s"] > janela + 0.1:
        problemas.append(f"clipe com {ci['duracao_s']} s, acima da janela de {janela} s")
    if info["tem_audio"] and not ci["tem_audio"]:
        problemas.append("o vídeo tem áudio e o clipe ficou sem")
    if problemas:
        raise ValueError("clipe inválido: " + "; ".join(problemas))
    return {"clipe": str(clipe), "arquivo_clipe": clipe.name, "sha256": sha256(clipe), "video_original": info["arquivo"],
            "inicio_s": inicio, "duracao_s": round(ci["duracao_s"], 2), "duracao_total_s": total,
            "cobre_video_inteiro": bool(total) and inicio == 0 and total <= janela + 0.05, "tem_audio": ci["tem_audio"]}


def executar(provedor: ProvedorPreditivo, preparo: dict, projeto: str, autorizacao: dict | None = None, enviar=False,
             politica: Politica | None = None, caminho_original=None, versao=None, plataforma=None) -> dict:
    """Checagens → (só com --enviar e autorização válida) chamada ao provedor → resultado_preditivo."""
    agora = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    janela = {k: preparo[k] for k in ("inicio_s", "duracao_s", "duracao_total_s", "cobre_video_inteiro")}
    lim = [AVISO]
    if not preparo["cobre_video_inteiro"]:
        lim.append(f"o resultado vale só para o trecho {preparo['inicio_s']}–{preparo['inicio_s'] + preparo['duracao_s']:g} s de um "
                   f"vídeo de {preparo['duracao_total_s']} s; não é avaliação do vídeo inteiro")
    base = {"contrato": "resultado_preditivo", "projeto": projeto, "video": preparo["video_original"], "versao": versao,
            "plataforma": plataforma, "provedor": provedor.nome, "ferramenta": provedor.ferramenta,
            "simulado": isinstance(provedor, ProvedorSimulado), "data": agora, "janela": janela, "campos_retornados": {},
            "url_relatorio": None, "custo": None, "limitacoes": lim, "erro": None}
    if base["simulado"]:
        lim.insert(0, "SIMULADO: números falsos para testar o fluxo; não é resultado real")
    disp = provedor.disponivel()
    autent = provedor.autenticacao()
    custo = provedor.estimar_custo()
    base["checagens"] = {"disponibilidade": disp, "autenticacao": autent, "creditos": provedor.creditos(), "custo_estimado": custo}
    if not enviar:
        return dict(base, status="preparado", erro=None)
    if provedor.externo:
        try:
            exigir_autorizacao(autorizacao, preparo["sha256"], provedor.nome, custo.get("estimado"), politica, caminho_original)
        except Exception as e:                                   # EnvioNaoAutorizado
            return dict(base, status="bloqueado", erro=str(e))
    if not disp["disponivel"]:
        return dict(base, status="falhou", erro=f"provedor indisponível: {disp['detalhe']}")
    if autent.get("autenticado") is False:
        return dict(base, status="falhou", erro=f"sem autenticação: {autent['detalhe']}")
    try:
        bruto = provedor.analisar(Path(preparo["clipe"]))
    except ErroProvedor as e:
        return dict(base, status="falhou", erro=str(e))
    info = provedor.interpretar(bruto)
    if not info["campos_retornados"]:
        lim.append("o provedor respondeu, mas sem campos de pontuação reconhecidos; veja `bruto`")
    return dict(base, status="concluido", campos_retornados=info["campos_retornados"], url_relatorio=info["url_relatorio"],
                custo=info["custo"], id_externo=info.get("id_externo"), bruto=bruto)


def markdown(r: dict) -> str:
    L = [f"# Avaliação preditiva — {r['video']}", "", f"Provedor: {r['ferramenta']}" + (" · **SIMULADO**" if r["simulado"] else ""),
         f"Status: **{r['status']}** · data {r['data']}",
         f"Janela: {r['janela']['inicio_s']}–{r['janela']['inicio_s'] + r['janela']['duracao_s']:g} s "
         f"(vídeo de {r['janela']['duracao_total_s']} s)", ""]
    if r.get("erro"):
        L += ["## Motivo", "", "```", r["erro"], "```", ""]
    if r["campos_retornados"]:
        L += ["## Campos devolvidos pelo provedor", "", "| Campo | Valor |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in r["campos_retornados"].items()]
        L.append("")
    if r.get("url_relatorio"):
        L += [f"Relatório do provedor: {r['url_relatorio']}", ""]
    if r.get("custo"):
        L += [f"Custo informado: {json.dumps(r['custo'], ensure_ascii=False)}", ""]
    ch = r.get("checagens") or {}
    if ch:
        L += ["## Checagens antes do envio", "", f"- Disponível: {ch['disponibilidade']}", f"- Autenticação: {ch['autenticacao']}",
              f"- Créditos: {ch['creditos']}", f"- Custo estimado: {ch['custo_estimado']}", ""]
    L += ["## Limitações", ""] + [f"- {x}" for x in r["limitacoes"]]
    return "\n".join(L) + "\n"


def salvar(r: dict, pasta) -> tuple[Path, Path]:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"predicao_{r['provedor']}_{Path(r['video']).stem}"
    j, m = pasta / f"{nome}.json", pasta / f"{nome}.md"
    j.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    m.write_text(markdown(r), encoding="utf-8")
    return j, m
