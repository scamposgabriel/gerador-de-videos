"""Linha de comando de ponta a ponta (regressão da interface pública da biblioteca)."""
import json

from creative_intelligence.cli import main


def test_cli_fluxo(videos, tmp_path, capsys):
    assert main(["modelo", "observacoes_editoriais", "--saida", str(tmp_path / "obs.json")]) == 0
    assert main(["validar", str(tmp_path / "obs.json"), "observacoes_editoriais"]) == 0
    assert main(["analisar", str(videos["com_cortes"]), "--saida", str(tmp_path / "an")]) == 0
    a = json.loads((tmp_path / "an" / "analise_tecnica.json").read_text(encoding="utf-8"))
    assert len(a["cortes"]) == 3 and (tmp_path / "an" / "quadros").is_dir()
    assert main(["comparar", str(videos["sem_cortes"]), str(videos["com_cortes"]), "--hipotese", "h", "--janela", "3",
                 "--saida", str(tmp_path / "ab")]) == 0
    assert main(["prever", str(videos["sem_cortes"]), "--projeto", "t", "--saida", str(tmp_path / "pr"), "--modelo-autorizacao"]) == 0
    aut = json.loads((tmp_path / "pr" / "autorizacao_envio.json").read_text(encoding="utf-8"))
    assert aut["envio_externo_permitido"] is False and aut["contem_dados_pessoais"] is True       # modelo começa negado
    assert main(["analisar", str(videos["invalido"]), "--saida", str(tmp_path / "x")]) == 2
    assert main(["verificar"]) == 0
    assert "vidIQ" in capsys.readouterr().out
