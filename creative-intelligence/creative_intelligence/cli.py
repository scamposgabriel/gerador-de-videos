"""Linha de comando da Creative Intelligence.

  ci verificar                                          FFmpeg, CLI da Higgsfield (sem segredos) e nota sobre o vidIQ
  ci analisar VIDEO --saida PASTA [--inicio S --duracao S] [--sem-quadros]
  ci modelo CONTRATO [--saida ARQ]                      modelos: entrada_manual, observacoes_editoriais, autorizacao_envio,
                                                        avaliacao_editorial, experimento
  ci validar ARQ CONTRATO
  ci referencia youtube URL --tema T --saida ARQ        metadados oficiais (YouTube Data API, chave de quem usa)
  ci referencia manual ENTRADA.json --saida ARQ         números colados de outra ferramenta (vidIQ, TikTok, Instagram)
  ci brief --referencia ARQ --observacoes ARQ [--analise ARQ] --saida PASTA
  ci comparar A B --hipotese "..." --saida PASTA [--janela 15] [--rotulos A,B] [--quadros]
  ci prever VIDEO --projeto P --saida PASTA [--provedor simulado|higgsfield] [--janela 15] [--inicio 0]
            [--modelo-autorizacao] [--autorizacao ARQ] [--politica ARQ] [--enviar]
  ci avaliacao modelo VIDEO --avaliador NOME [--tipo humano|ia] --saida ARQ | ci avaliacao relatorio ARQ
  ci experimento novo --id ID --projeto P --titulo T --versao V --gancho G --saida ARQ
  ci experimento publicar ARQ --plataforma X --data AAAA-MM-DD [--url U]
  ci experimento metricas ARQ --plataforma X --de CSV_OU_JSON --fonte "painel do Instagram, export de AAAA-MM-DD"
  ci experimento relatorio ARQ
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, avaliacao, brief, comparar, experimentos, modelos, preditivo, tecnica
from .autorizacao import Politica, modelo as modelo_autorizacao
from .contratos import validar
from .midia import FerramentaAusente, MidiaInvalida, ffmpeg, ffprobe
from .pesquisa import NOTA_VIDIQ, EntradaManual, ErroPesquisa, YouTubeDataAPI


def _ler(arq):
    return json.loads(Path(arq).read_text(encoding="utf-8"))


def _gravar(dados, arq):
    p = Path(arq)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="ci", description=f"Creative Intelligence v{__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verificar")
    p = sub.add_parser("analisar"); p.add_argument("video"); p.add_argument("--saida", required=True)
    p.add_argument("--inicio", type=float, default=0.0); p.add_argument("--duracao", type=float); p.add_argument("--sem-quadros", action="store_true")
    p = sub.add_parser("modelo"); p.add_argument("contrato"); p.add_argument("--saida")
    p = sub.add_parser("validar"); p.add_argument("arquivo"); p.add_argument("contrato")
    p = sub.add_parser("referencia"); p.add_argument("fonte", choices=["youtube", "manual"]); p.add_argument("entrada")
    p.add_argument("--tema", default=""); p.add_argument("--saida", required=True)
    p = sub.add_parser("brief"); p.add_argument("--referencia", required=True); p.add_argument("--observacoes", required=True)
    p.add_argument("--analise"); p.add_argument("--saida", required=True)
    p = sub.add_parser("comparar"); p.add_argument("a"); p.add_argument("b"); p.add_argument("--hipotese", required=True)
    p.add_argument("--saida", required=True); p.add_argument("--janela", type=float, default=15.0); p.add_argument("--rotulos", default="A,B")
    p.add_argument("--quadros", action="store_true")
    p = sub.add_parser("prever"); p.add_argument("video"); p.add_argument("--projeto", required=True); p.add_argument("--saida", required=True)
    p.add_argument("--provedor", choices=list(preditivo.PROVEDORES), default="simulado")
    p.add_argument("--janela", type=float, default=preditivo.JANELA_PADRAO_S); p.add_argument("--inicio", type=float, default=0.0)
    p.add_argument("--autorizacao"); p.add_argument("--politica"); p.add_argument("--enviar", action="store_true")
    p.add_argument("--modelo-autorizacao", action="store_true"); p.add_argument("--versao"); p.add_argument("--plataforma")
    p = sub.add_parser("avaliacao"); p.add_argument("acao", choices=["modelo", "relatorio"]); p.add_argument("alvo")
    p.add_argument("--avaliador", default="PREENCHER"); p.add_argument("--tipo", default="humano"); p.add_argument("--saida")
    p = sub.add_parser("experimento"); p.add_argument("acao", choices=["novo", "publicar", "metricas", "relatorio"])
    p.add_argument("arquivo", nargs="?"); p.add_argument("--id"); p.add_argument("--projeto"); p.add_argument("--titulo")
    p.add_argument("--versao"); p.add_argument("--gancho"); p.add_argument("--saida"); p.add_argument("--plataforma")
    p.add_argument("--data"); p.add_argument("--url"); p.add_argument("--de"); p.add_argument("--fonte")
    a = ap.parse_args(argv)
    try:
        return _executar(a)
    except (FerramentaAusente, MidiaInvalida, ErroPesquisa, ValueError, KeyError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2


def _executar(a) -> int:
    if a.cmd == "verificar":
        for nome, f in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)):
            try:
                f()
                print(f"{nome}: ok")
            except FerramentaAusente as e:
                print(f"{nome}: FALTA — {e}")
        h = preditivo.HiggsfieldViralityProvider()
        disp = h.disponivel()
        print(f"higgsfield CLI: {'instalada' if disp['disponivel'] else 'não disponível'} ({disp['detalhe']})")
        if disp["disponivel"]:
            print(f"higgsfield sessão: {h.autenticacao()}")
        print(NOTA_VIDIQ)
        return 0
    if a.cmd == "analisar":
        pasta = Path(a.saida)
        r = tecnica.analisar(a.video, a.inicio, a.duracao, None if a.sem_quadros else pasta / "quadros")
        print(_gravar(r, pasta / "analise_tecnica.json"))
        print(f"{r['metadados']['duracao_s']} s · {len(r['cortes'])} cortes · movimento {r['visual']['movimento_nivel']} · "
              f"áudio: {'sim' if r['audio']['tem_audio'] else 'não'}")
        return 0
    if a.cmd == "modelo":
        tudo = modelos.todos()
        if a.contrato not in tudo:
            raise KeyError(f"modelos disponíveis: {', '.join(tudo)}")
        if a.saida:
            print(_gravar(tudo[a.contrato], a.saida))
        else:
            print(json.dumps(tudo[a.contrato], ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "validar":
        erros = validar(a.contrato, _ler(a.arquivo))
        print("válido" if not erros else "\n".join(erros))
        return 0 if not erros else 1
    if a.cmd == "referencia":
        ref = YouTubeDataAPI().referencia(a.entrada, a.tema) if a.fonte == "youtube" else EntradaManual(a.entrada).referencia()
        print(_gravar(ref, a.saida))
        return 0
    if a.cmd == "brief":
        b = brief.montar(_ler(a.referencia), _ler(a.observacoes), _ler(a.analise) if a.analise else None)
        for x in brief.salvar(b, a.saida):
            print(x)
        return 0
    if a.cmd == "comparar":
        rot = tuple(x.strip() for x in a.rotulos.split(","))[:2]
        c = comparar.comparar(a.a, a.b, a.janela, a.hipotese, rot, Path(a.saida) / "quadros" if a.quadros else None)
        for x in comparar.salvar(c, a.saida):
            print(x)
        return 0
    if a.cmd == "prever":
        prov = preditivo.PROVEDORES[a.provedor]()
        prep = preditivo.preparar_clipe(a.video, Path(a.saida), a.inicio, a.janela)
        if a.modelo_autorizacao:
            mod = modelo_autorizacao(prep["sha256"], prov.nome, prep["arquivo_clipe"])
            print(_gravar(mod, Path(a.saida) / "autorizacao_envio.json"), "(modelo: revise e preencha; começa tudo negado)")
        pol = Politica.carregar(a.politica) if a.politica else None
        r = preditivo.executar(prov, prep, a.projeto, _ler(a.autorizacao) if a.autorizacao else None, a.enviar, pol, a.video,
                               a.versao, a.plataforma)
        for x in preditivo.salvar(r, a.saida):
            print(x)
        print(f"status: {r['status']}" + (f" — {r['erro']}" if r.get("erro") else ""))
        return 0 if r["status"] in ("preparado", "concluido") else 1
    if a.cmd == "avaliacao":
        if a.acao == "modelo":
            print(_gravar(avaliacao.modelo(a.alvo, a.avaliador, a.tipo), a.saida or "avaliacao_editorial.json"))
        else:
            print(avaliacao.markdown(_ler(a.alvo)))
        return 0
    if a.cmd == "experimento":
        if a.acao == "novo":
            print(_gravar(experimentos.novo(a.id, a.projeto, a.titulo, a.versao, a.gancho), a.saida))
            return 0
        exp = _ler(a.arquivo)
        if a.acao == "publicar":
            _gravar(experimentos.registrar_publicacao(exp, a.plataforma, a.data, a.url), a.arquivo)
        elif a.acao == "metricas":
            r = experimentos.importar_metricas(exp, a.plataforma, a.de, a.fonte)
            _gravar(r["experimento"], a.arquivo)
            if r["metricas_fora_da_lista"]:
                print(f"aviso: métricas fora da lista padrão: {', '.join(r['metricas_fora_da_lista'])}")
        else:
            print(experimentos.markdown(exp))
            return 0
        print(a.arquivo)
        return 0
    return 1
