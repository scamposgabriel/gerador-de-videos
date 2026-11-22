"""A/B, Higgsfield simulada, falhas, autorização e privacidade (itens 9–14). Nenhuma chamada paga: CLI falsa."""
import json

import pytest

from creative_intelligence import avaliacao, comparar, experimentos, preditivo
from creative_intelligence.autorizacao import Politica, modelo as modelo_aut, verificar


def _aut(sha, **kw):
    a = modelo_aut(sha, "higgsfield", "clipe.mp4", "proprio")
    a.update({"direitos_confirmados": True, "envio_externo_permitido": True, "contem_dados_pessoais": False,
              "orcamento_maximo_creditos": 5, "aceita_custo_nao_estimado": True, "aprovado_por": "dono", "aprovado_em": "2026-11-22"})
    a.update(kw)
    return a


def test_comparacao_ab(videos, tmp_path):
    with pytest.raises(ValueError):
        comparar.comparar(videos["sem_cortes"], videos["com_cortes"], janela=3, hipotese="")
    c = comparar.comparar(videos["sem_cortes"], videos["com_cortes"], janela=3, hipotese="cortes a cada 1 s", rotulos=("v1", "v2"))
    d = {x["medida"]: x for x in c["diferencas"]}
    assert d["cortes na janela"]["v1"] == 0 and d["cortes na janela"]["v2"] == 2 and d["cortes na janela"]["delta_b_menos_a"] == 2
    assert c["predicoes"] == {} and c["resultado_real"] is None and "Não afirma" in c["aviso"]
    _, m = comparar.salvar(c, tmp_path)
    assert "Hipótese criativa da versão v2" in m.read_text(encoding="utf-8")


def test_clipe_de_15s_de_video_longo(videos, tmp_path):
    p = preditivo.preparar_clipe(videos["longo"], tmp_path, janela=15)
    assert p["duracao_s"] == pytest.approx(15, abs=0.1) and p["tem_audio"] and not p["cobre_video_inteiro"]
    r = preditivo.executar(preditivo.ProvedorSimulado(), p, "teste", enviar=True)
    assert r["status"] == "concluido" and r["simulado"]
    assert any("vale só para o trecho" in x for x in r["limitacoes"]) and any("SIMULADO" in x for x in r["limitacoes"])


def test_higgsfield_resposta_simulada(videos, tmp_path, falso_higgsfield):
    cmd, log = falso_higgsfield("ok")
    p = preditivo.preparar_clipe(videos["sem_cortes"], tmp_path)
    prov = preditivo.HiggsfieldViralityProvider(comando=cmd)
    r = preditivo.executar(prov, p, "teste", _aut(p["sha256"]), enviar=True)
    assert r["status"] == "concluido" and r["simulado"] is False
    assert r["campos_retornados"]["result.hook_score"] == 71
    assert r["url_relatorio"] == "https://higgsfield.ai/report/job-123"
    assert r["custo"] == {"result.credits_used": 2}
    texto = json.dumps(r)
    assert "SEGREDO" not in texto and "pessoa@exemplo.com" not in texto           # token e e-mail nunca são guardados
    assert r["checagens"]["creditos"]["saldo"] == {"credits": 42}


def test_falha_de_autenticacao(videos, tmp_path, falso_higgsfield):
    cmd, log = falso_higgsfield("sem_login")
    p = preditivo.preparar_clipe(videos["sem_cortes"], tmp_path)
    r = preditivo.executar(preditivo.HiggsfieldViralityProvider(comando=cmd), p, "teste", _aut(p["sha256"]), enviar=True)
    assert r["status"] == "falhou" and "auth login" in r["erro"]
    assert "create" not in log.read_text(encoding="utf-8")


def test_falha_do_provedor(videos, tmp_path, falso_higgsfield):
    cmd, _ = falso_higgsfield("falha")
    p = preditivo.preparar_clipe(videos["sem_cortes"], tmp_path)
    r = preditivo.executar(preditivo.HiggsfieldViralityProvider(comando=cmd), p, "teste", _aut(p["sha256"]), enviar=True)
    assert r["status"] == "falhou" and "503" in r["erro"] and r["campos_retornados"] == {}


def test_cli_ausente():
    prov = preditivo.HiggsfieldViralityProvider(comando=["programa-que-nao-existe-xyz"])
    assert prov.disponivel()["disponivel"] is False


def test_sem_autorizacao_nada_e_enviado(videos, tmp_path, falso_higgsfield):
    cmd, log = falso_higgsfield("ok", custo=3)
    p = preditivo.preparar_clipe(videos["sem_cortes"], tmp_path)
    prov = preditivo.HiggsfieldViralityProvider(comando=cmd)
    seco = preditivo.executar(prov, p, "teste", None, enviar=False)
    assert seco["status"] == "preparado" and seco["checagens"]["custo_estimado"]["estimado"] == 3.0
    for aut in (None, _aut("outro-sha"), _aut(p["sha256"], envio_externo_permitido=False),
                _aut(p["sha256"], orcamento_maximo_creditos=2)):                         # custo 3 > orçamento 2
        r = preditivo.executar(prov, p, "teste", aut, enviar=True)
        assert r["status"] == "bloqueado", aut
    assert "create" not in log.read_text(encoding="utf-8")                              # o vídeo nunca saiu


def test_privacidade_classificacao_politica_e_cliente(tmp_path):
    sha = "abc"
    assert any("nunca é enviado" in x for x in verificar(_aut(sha, classificacao="interno"), sha, "higgsfield"))
    assert any("dados pessoais" in x for x in verificar(_aut(sha, contem_dados_pessoais=True), sha, "higgsfield"))
    assert any("cliente" in x for x in verificar(_aut(sha, classificacao="cliente"), sha, "higgsfield"))
    assert verificar(_aut(sha, classificacao="cliente", autorizacao_cliente="e-mail do cliente de 2026-11-20"), sha, "higgsfield") == []
    assert any("vencida" in x for x in verificar(_aut(sha, valido_ate="2020-01-01"), sha, "higgsfield"))
    assert any("não preenchida" in x for x in verificar(modelo_aut(sha, "higgsfield") | {"direitos_confirmados": True}, sha, "higgsfield"))
    (tmp_path / "videos" / "tutorial-sistema").mkdir(parents=True)
    alvo = tmp_path / "videos" / "tutorial-sistema" / "v.mp4"
    alvo.write_bytes(b"x")
    pol_arq = tmp_path / "politica.json"
    pol_arq.write_text(json.dumps({"classificacao_padrao": "privado", "nunca_enviar": ["videos/tutorial-*/*"]}), encoding="utf-8")
    pol = Politica.carregar(pol_arq)
    assert any("política" in x for x in verificar(_aut(sha), sha, "higgsfield", politica=pol, caminho_original=alvo))


def test_avaliacao_editorial_sem_nota_unica(tmp_path):
    av = avaliacao.modelo("v.mp4", "revisor")
    av["dimensoes"]["gancho"] = {"nota": 4, "justificativa": "mostra o fenômeno no 1º segundo", "status": "avaliado"}
    md = avaliacao.markdown(av)
    assert "Sem nota única" in md and "Pendentes (9)" in md
    av["dimensoes"]["ritmo"] = {"nota": 7, "justificativa": "x", "status": "avaliado"}
    with pytest.raises(ValueError):
        avaliacao.validar_notas(av)


def test_experimento_metricas_reais(tmp_path):
    exp = experimentos.novo("exp-1", "canal", "Vídeo", "v2", "pergunta", hipoteses=["gancho visual em 1 s"])
    with pytest.raises(ValueError):
        experimentos.importar_metricas(exp, "instagram", tmp_path / "x.csv", "painel")
    experimentos.registrar_publicacao(exp, "instagram", "2026-11-25", None)
    csv = tmp_path / "m.csv"
    csv.write_text("metrica,valor\nvisualizacoes,1500\nsalvamentos,\nmetrica_estranha,3\n", encoding="utf-8")
    r = experimentos.importar_metricas(exp, "instagram", csv, "painel do Instagram (export 2026-11-30)")
    met = r["experimento"]["publicacoes"][0]["metricas"]
    assert met["visualizacoes"]["valor"] == 1500.0 and "salvamentos" not in met and r["metricas_fora_da_lista"] == ["metrica_estranha"]
    assert "Resultado real" in experimentos.markdown(r["experimento"])
