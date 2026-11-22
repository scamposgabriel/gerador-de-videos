"""Vídeos SINTÉTICOS gerados pelo FFmpeg na hora (nenhum vídeo de terceiros) e uma CLI falsa da Higgsfield."""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from creative_intelligence.midia import ffmpeg  # noqa: E402

FALSO = Path(__file__).resolve().parent / "falso_higgsfield.py"


def _gerar(saida: Path, *args):
    r = subprocess.run([ffmpeg(), "-v", "error", *args, "-y", str(saida)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return saida


@pytest.fixture(scope="session")
def videos(tmp_path_factory):
    d = tmp_path_factory.mktemp("videos")
    cores = ["red", "blue", "green", "white"]
    ent = []
    for c in cores:
        ent += ["-f", "lavfi", "-i", f"color=c={c}:s=320x240:r=30:d=1"]
    return {
        "sem_cortes": _gerar(d / "sem_cortes.mp4", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=4",
                             "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-shortest"),
        "com_cortes": _gerar(d / "com_cortes.mp4", *ent, "-f", "lavfi", "-i", "sine=frequency=330:duration=4",
                             "-filter_complex", "[0][1][2][3]concat=n=4:v=1:a=0[v]", "-map", "[v]", "-map", "4:a",
                             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"),
        "sem_audio": _gerar(d / "sem_audio.mp4", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=3", "-an",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p"),
        "com_pausa": _gerar(d / "com_pausa.mp4", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=3",
                            "-f", "lavfi", "-i", "aevalsrc='if(between(t,1,2),0,0.5*sin(2*PI*440*t))':s=44100:d=3",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"),
        "longo": _gerar(d / "longo.mp4", "-f", "lavfi", "-i", "testsrc2=s=320x240:r=30:d=20",
                        "-f", "lavfi", "-i", "sine=frequency=500:duration=20", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest"),
        "invalido": (d / "invalido.mp4").write_bytes(b"isto nao e um video") and d / "invalido.mp4",
    }


@pytest.fixture
def falso_higgsfield(tmp_path, monkeypatch):
    """CLI falsa: modo por variável de ambiente; registra cada chamada num log (para provar o que foi ou não enviado)."""
    log = tmp_path / "chamadas.log"
    monkeypatch.setenv("FALSO_HIGGSFIELD_LOG", str(log))

    def fazer(modo="ok", custo=None):
        monkeypatch.setenv("FALSO_HIGGSFIELD_MODO", modo)
        if custo is not None:
            monkeypatch.setenv("FALSO_HIGGSFIELD_CUSTO", str(custo))
        else:
            monkeypatch.delenv("FALSO_HIGGSFIELD_CUSTO", raising=False)
        return [sys.executable, str(FALSO)], log
    return fazer
