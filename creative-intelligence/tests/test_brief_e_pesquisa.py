"""Brief, metadados incompletos, referência sem acesso ao vídeo e métricas ausentes (itens 6–8)."""
import json

import pytest

from creative_intelligence import brief, modelos, tecnica
from creative_intelligence.contratos import ContratoInvalido
from creative_intelligence.pesquisa import EntradaManual, ErroPesquisa, YouTubeDataAPI, id_youtube


def _obs_ok(ref_id="ref-1"):
    o = json.loads(json.dumps(modelos.observacoes_editoriais(ref_id)).replace("PREENCHER: ", "").replace("PREENCHER", "x"))
    o["abertura"]["primeira_imagem"]["intervalo"] = [0.0, 1.0]
    o["desenvolvimento"]["revelacoes"][0]["intervalo"] = [3.2, 3.8]
    o["hipoteses"] = [{"hipotese": "pergunta concreta no 1º segundo", "base": "abertura", "confianca": "alta"}]
    return o


def _ref(**kw):
    r = {"id": "ref-1", "plataforma": "youtube", "url": "https://exemplo.invalid/v", "criador": "Canal X", "tema": "teste",
         "coletado_em": "2026-11-22", "metricas": {}, "acesso_ao_video": "arquivo_local", "arquivo_video": "com_cortes.mp4"}
    r.update(kw)
    return r


def test_brief_completo_com_analise(videos, tmp_path):
    a = tecnica.analisar(videos["com_cortes"])
    ref = _ref(metricas={"visualizacoes": {"valor": 120000, "fonte": "YouTube Data API v3", "coletado_em": "2026-11-22", "verificado": True}})
    b = brief.montar(ref, _obs_ok(), a)
    assert [m["secao"] for m in b["mapa_temporal"]] == ["abertura", "desenvolvimento", "conclusao"]
    rev = [o for m in b["mapa_temporal"] for o in m["observacoes"] if o["rotulo"] == "revelacoes"][0]
    assert rev["intervalo"] == [3.2, 3.8]
    assert b["nivel_confianca"] == "alta"
    assert "correlação" in b["aviso_hipoteses"]
    j, m = brief.salvar(b, tmp_path)
    texto = m.read_text(encoding="utf-8")
    assert "Três ganchos originais" in texto and "Não copiar" in texto and "Dados indisponíveis" in texto


def test_metadados_incompletos_viram_dados_indisponiveis(videos):
    b = brief.montar(_ref(), _obs_ok(), tecnica.analisar(videos["com_cortes"]))
    falta = " ".join(b["dados_indisponiveis"])
    for m in ("visualizacoes", "outlier_score", "retencao_media_pct"):
        assert m in falta
    assert b["nivel_confianca"] == "media" and any("métrica verificada" in x for x in b["motivos_confianca"])


def test_referencia_sem_acesso_ao_video():
    b = brief.montar(_ref(acesso_ao_video="sem_acesso", arquivo_video=None), _obs_ok(), None)
    assert b["nivel_confianca"] == "baixa"
    assert any("análise técnica do arquivo" in x for x in b["dados_indisponiveis"])
    assert b["mapa_temporal"][0]["de_s"] is None and b["ritmo"]["tecnico"] is None


def test_brief_recusa_modelo_nao_preenchido_e_referencia_trocada():
    with pytest.raises(ContratoInvalido):
        brief.montar(_ref(), modelos.observacoes_editoriais("ref-1"))
    with pytest.raises(ContratoInvalido):
        brief.montar(_ref(), _obs_ok("outra-ref"))
    o = _obs_ok()
    o["recomendacoes"]["ganchos"] = ["só um"]
    with pytest.raises(ContratoInvalido):
        brief.montar(_ref(), o)


def test_metricas_ausentes_e_sem_fonte(tmp_path):
    arq = tmp_path / "entrada.json"
    arq.write_text(json.dumps({"referencia": {"id": "r", "plataforma": "tiktok", "url": "u", "criador": "c", "tema": "t"},
                               "metricas": {"visualizacoes": {"valor": None, "fonte": "TikTok"},
                                            "outlier_score": {"valor": 4.2, "fonte": "vidIQ (colado em 2026-11-22)"}}}), encoding="utf-8")
    ref = EntradaManual(arq).referencia()
    assert list(ref["metricas"]) == ["outlier_score"] and ref["metricas"]["outlier_score"]["verificado"] is False
    arq.write_text(json.dumps({"referencia": {"id": "r", "plataforma": "tiktok", "url": "u", "criador": "c", "tema": "t"},
                               "metricas": {"visualizacoes": {"valor": 10}}}), encoding="utf-8")
    with pytest.raises(ErroPesquisa):
        EntradaManual(arq).referencia()


def test_youtube_data_api_sem_rede():
    resposta = {"items": [{"snippet": {"title": "Por que X?", "channelTitle": "Canal", "publishedAt": "2026-01-01T00:00:00Z"},
                           "statistics": {"viewCount": "1000", "likeCount": "50"}, "contentDetails": {"duration": "PT45S"}}]}
    urls = []
    api = YouTubeDataAPI(chave="CHAVE-TESTE", obter=lambda u: urls.append(u) or resposta)
    ref = api.referencia("https://youtu.be/abcdefghijk", "curiosidade")
    assert ref["duracao_s"] == 45 and ref["metricas"]["visualizacoes"]["valor"] == 1000
    assert "comentarios" not in ref["metricas"]                       # não veio: não é inventado
    assert "CHAVE-TESTE" not in json.dumps(ref)
    assert id_youtube("https://www.youtube.com/shorts/abcdefghijk") == "abcdefghijk"
