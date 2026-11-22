"""Contratos e engenharia reversa técnica com vídeos sintéticos (itens 1–5 da missão)."""
import pytest

from creative_intelligence import tecnica
from creative_intelligence.contratos import ContratoInvalido, exigir, validar
from creative_intelligence.midia import MidiaInvalida, sondar


def _ref(**kw):
    r = {"id": "ref-1", "plataforma": "youtube", "url": "https://exemplo.invalid/v", "criador": "Canal X", "tema": "teste",
         "coletado_em": "2026-11-22", "metricas": {}, "acesso_ao_video": "arquivo_local"}
    r.update(kw)
    return r


def test_contrato_valido_e_invalido():
    assert validar("referencia", _ref()) == []
    erros = validar("referencia", _ref(plataforma="orkut", metricas={"visualizacoes": {"valor": 10, "fonte": "x"}}))
    assert any("plataforma" in e for e in erros)
    assert any("coletado_em" in e for e in erros) and any("verificado" in e for e in erros)
    with pytest.raises(ContratoInvalido):
        exigir("referencia", {"id": "só isso"})


def test_booleano_nao_vale_como_numero_e_lista_minima():
    aut = {"arquivo_sha256": "x", "provedor": "p", "finalidade": "f", "classificacao": "proprio", "direitos_confirmados": True,
           "envio_externo_permitido": True, "contem_dados_pessoais": False, "orcamento_maximo_creditos": True,
           "aceita_custo_nao_estimado": False, "aprovado_por": "eu", "aprovado_em": "2026-11-22"}
    assert any("orcamento_maximo_creditos" in e for e in validar("autorizacao_envio", aut))


def test_video_sem_cortes(videos):
    a = tecnica.analisar(videos["sem_cortes"])
    assert a["cortes"] == []
    assert a["planos"]["quantidade"] == 1
    assert a["metadados"]["duracao_s"] == pytest.approx(4, abs=0.1)
    assert a["audio"]["tem_audio"] and a["audio"]["primeiro_som_s"] == pytest.approx(0, abs=0.15)
    assert "retenção" in a["aviso"]


def test_video_com_varios_cortes(videos, tmp_path):
    a = tecnica.analisar(videos["com_cortes"], pasta_quadros=tmp_path / "q")
    ts = [c["t"] for c in a["cortes"]]
    assert len(ts) == 3 and all(abs(t - alvo) <= 0.15 for t, alvo in zip(ts, [1, 2, 3]))
    assert a["planos"]["media_s"] == pytest.approx(1.0, abs=0.15)
    assert a["planos"]["cortes_por_minuto"] == pytest.approx(45, abs=5)
    assert {m["matiz"] for m in a["cor"]["matizes_dominantes"]} >= {"vermelho", "azul", "verde"}
    assert a["quadros_referencia"] and all((tmp_path / "q" / q["arquivo"]).exists() for q in a["quadros_referencia"])
    assert "/" not in a["arquivo"] and "\\" not in a["arquivo"]          # só o nome, nunca o caminho


def test_audio_ausente(videos):
    a = tecnica.analisar(videos["sem_audio"])
    assert a["audio"] == {"tem_audio": False, "observacao": "o arquivo não tem faixa de áudio"}
    assert any("sem áudio" in x for x in a["limitacoes"])
    assert "pausas" not in a["secoes"]["abertura"]


def test_pausa_no_audio(videos):
    a = tecnica.analisar(videos["com_pausa"])
    assert len(a["audio"]["pausas"]) == 1
    p = a["audio"]["pausas"][0]
    assert p["de"] == pytest.approx(1.0, abs=0.15) and p["duracao_s"] == pytest.approx(1.0, abs=0.2)


def test_arquivo_invalido_e_inexistente(videos, tmp_path):
    with pytest.raises(MidiaInvalida):
        sondar(videos["invalido"])
    with pytest.raises(MidiaInvalida):
        tecnica.analisar(tmp_path / "nao-existe.mp4")


def test_janela_de_analise(videos):
    a = tecnica.analisar(videos["longo"], inicio=2.0, duracao=5.0)
    assert a["janela"] == {"inicio_s": 2.0, "duracao_s": 5.0, "video_inteiro": False}
    assert a["secoes"]["abertura"]["de_s"] == 2.0
