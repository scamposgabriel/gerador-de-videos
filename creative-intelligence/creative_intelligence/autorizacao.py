"""Controle de envio externo: nada sai da máquina sem uma autorização escrita para AQUELE arquivo (sha256), AQUELE provedor e
um orçamento. Material interno, confidencial ou com dados pessoais nunca é enviado; material de cliente exige a permissão
do cliente registrada. Cada repositório pode ter uma política com pastas que nunca são enviadas.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
from pathlib import Path

from .contratos import validar

BLOQUEADAS = {"interno", "confidencial"}


class EnvioNaoAutorizado(Exception):
    pass


class Politica:
    """Política do repositório: classificação padrão do material e padrões de caminho que nunca saem (glob, relativo à raiz)."""

    def __init__(self, classificacao_padrao="privado", bloqueios=(), raiz=None):
        self.classificacao_padrao = classificacao_padrao
        self.bloqueios = list(bloqueios)
        self.raiz = Path(raiz) if raiz else None

    @classmethod
    def carregar(cls, arquivo) -> "Politica":
        d = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        return cls(d.get("classificacao_padrao", "privado"), d.get("nunca_enviar", []), Path(arquivo).resolve().parent)

    def bloqueado(self, caminho) -> str | None:
        if not caminho:
            return None
        p = Path(caminho).resolve()
        rel = p.relative_to(self.raiz).as_posix() if self.raiz and p.is_relative_to(self.raiz) else p.name
        for padrao in self.bloqueios:
            if fnmatch.fnmatch(rel, padrao) or fnmatch.fnmatch(p.name, padrao):
                return padrao
        return None


def modelo(sha256: str, provedor: str, nome_arquivo: str = "", classificacao: str = "privado") -> dict:
    """Modelo para o dono do material preencher. Começa tudo NEGADO: só vale depois de revisado à mão."""
    aut = {"contrato": "autorizacao_envio", "arquivo_sha256": sha256, "provedor": provedor,
           "finalidade": "avaliar o gancho antes de publicar", "classificacao": classificacao,
           "direitos_confirmados": False, "envio_externo_permitido": False, "contem_dados_pessoais": True,
           "autorizacao_cliente": None, "orcamento_maximo_creditos": None, "aceita_custo_nao_estimado": False,
           "aprovado_por": "PREENCHER", "aprovado_em": "PREENCHER (AAAA-MM-DD)", "valido_ate": None}
    if nome_arquivo:
        aut["arquivo_nome"] = nome_arquivo
    return aut


def verificar(aut: dict | None, sha256: str, provedor: str, custo_estimado: float | None = None,
              politica: Politica | None = None, caminho_original=None, hoje: dt.date | None = None) -> list[str]:
    """Lista de motivos para NÃO enviar (vazia = pode enviar)."""
    if aut is None:
        return ["sem autorização escrita para envio externo (crie com `ci prever ... --modelo-autorizacao` e preencha)"]
    problemas = validar("autorizacao_envio", aut)
    if problemas:
        return problemas
    if aut["arquivo_sha256"] != sha256:
        problemas.append("a autorização é de outro arquivo (sha256 diferente do clipe preparado)")
    if aut["provedor"] != provedor:
        problemas.append(f"a autorização é para o provedor '{aut['provedor']}', não '{provedor}'")
    if aut["classificacao"] in BLOQUEADAS:
        problemas.append(f"material '{aut['classificacao']}' nunca é enviado a serviço externo")
    if aut["contem_dados_pessoais"]:
        problemas.append("o material contém dados pessoais: não enviar")
    if not aut["direitos_confirmados"]:
        problemas.append("direitos sobre o material não confirmados")
    if not aut["envio_externo_permitido"]:
        problemas.append("envio externo não permitido na autorização")
    if aut["classificacao"] == "cliente" and not (aut.get("autorizacao_cliente") or "").strip():
        problemas.append("material de cliente: falta registrar a autorização do cliente para envio externo")
    if "PREENCHER" in (aut["aprovado_por"] + aut["aprovado_em"]):
        problemas.append("autorização ainda não preenchida (aprovado_por / aprovado_em)")
    if aut.get("valido_ate"):
        try:
            if dt.date.fromisoformat(aut["valido_ate"]) < (hoje or dt.date.today()):
                problemas.append(f"autorização vencida em {aut['valido_ate']}")
        except ValueError:
            problemas.append("valido_ate não é uma data AAAA-MM-DD")
    orc = aut["orcamento_maximo_creditos"]
    if custo_estimado is not None:
        if orc is None or custo_estimado > orc:
            problemas.append(f"custo estimado ({custo_estimado}) acima do orçamento autorizado ({orc})")
    elif not aut["aceita_custo_nao_estimado"]:
        problemas.append("o custo não pôde ser estimado e a autorização não aceita custo não estimado")
    if politica:
        padrao = politica.bloqueado(caminho_original)
        if padrao:
            problemas.append(f"a política do repositório proíbe enviar este caminho (regra '{padrao}')")
    return problemas


def exigir(*args, **kw) -> None:
    problemas = verificar(*args, **kw)
    if problemas:
        raise EnvioNaoAutorizado("envio externo BLOQUEADO:\n  - " + "\n  - ".join(problemas))
