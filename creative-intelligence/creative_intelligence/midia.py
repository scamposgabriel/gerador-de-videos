"""Acesso a FFmpeg/FFprobe: metadados, quadros pequenos (RGB), áudio mono, quadros de referência e recortes.

Os relatórios guardam só o NOME do arquivo (nunca o caminho completo), para não vazar pastas pessoais.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from array import array
from pathlib import Path


class MidiaInvalida(Exception):
    """Arquivo ausente, corrompido ou sem faixa de vídeo."""


class FerramentaAusente(Exception):
    """FFmpeg/FFprobe não encontrados."""


def _bin(nome: str) -> str:
    env = os.environ.get(f"{nome.upper()}_BIN")
    if env and Path(env).exists():
        return env
    achado = shutil.which(nome)
    if achado:
        return achado
    raise FerramentaAusente(f"{nome} não encontrado: instale o FFmpeg e coloque a pasta bin no PATH, ou defina {nome.upper()}_BIN")


def ffmpeg() -> str:
    return _bin("ffmpeg")


def ffprobe() -> str:
    return _bin("ffprobe")


def _rodar(cmd: list[str], binario=False, timeout=600) -> subprocess.CompletedProcess:
    if binario:
        return subprocess.run(cmd, capture_output=True, timeout=timeout)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def _num(x):
    try:
        v = float(x)
        return v if v == v else None          # NaN → None
    except (TypeError, ValueError):
        return None


def _fracao(x):
    if not x or x in ("0/0", "N/A"):
        return None
    if "/" in str(x):
        a, b = str(x).split("/", 1)
        a, b = _num(a), _num(b)
        return round(a / b, 3) if a is not None and b else None
    return _num(x)


def sha256(arquivo) -> str:
    h = hashlib.sha256()
    with open(arquivo, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def sondar(arquivo) -> dict:
    """Metadados do arquivo. Campos que o contêiner não informa ficam None e entram em `faltando`."""
    p = Path(arquivo)
    if not p.is_file():
        raise MidiaInvalida(f"arquivo não encontrado: {p.name}")
    r = _rodar([ffprobe(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(p)])
    if r.returncode != 0:
        raise MidiaInvalida(f"não é um vídeo legível ({p.name}): {r.stderr.strip()[:200]}")
    d = json.loads(r.stdout or "{}")
    streams = d.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if v is None:
        raise MidiaInvalida(f"sem faixa de vídeo: {p.name}")
    fmt = d.get("format", {})
    info = {
        "arquivo": p.name,
        "duracao_s": _num(fmt.get("duration")) or _num(v.get("duration")),
        "largura": v.get("width"), "altura": v.get("height"),
        "fps": _fracao(v.get("avg_frame_rate")) or _fracao(v.get("r_frame_rate")),
        "codec_video": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
        "tem_audio": a is not None,
        "codec_audio": a.get("codec_name") if a else None,
        "taxa_audio_hz": int(a["sample_rate"]) if a and a.get("sample_rate") else None,
        "canais": a.get("channels") if a else None,
        "bitrate_kbps": round(_num(fmt.get("bit_rate")) / 1000) if _num(fmt.get("bit_rate")) else None,
        "tamanho_bytes": p.stat().st_size,
    }
    opcionais_audio = {"codec_audio", "taxa_audio_hz", "canais"}
    info["faltando"] = [k for k, val in info.items() if val is None and not (k in opcionais_audio and not info["tem_audio"])]
    return info


def altura_proporcional(info: dict, largura: int) -> int:
    if not info.get("largura") or not info.get("altura"):
        return max(2, round(largura * 9 / 16 / 2) * 2)
    return max(2, round(largura * info["altura"] / info["largura"] / 2) * 2)


def quadros(arquivo, fps=10.0, largura=64, inicio=0.0, duracao=None):
    """Gera (t, bytes RGB24 de largura × altura) em ritmo fixo. Pequeno de propósito: é para medir, não para ver."""
    info = sondar(arquivo)
    alt = altura_proporcional(info, largura)
    cmd = [ffmpeg(), "-v", "error"]
    if inicio:
        cmd += ["-ss", f"{inicio:.3f}"]
    cmd += ["-i", str(arquivo)]
    if duracao:
        cmd += ["-t", f"{duracao:.3f}"]
    cmd += ["-vf", f"fps={fps},scale={largura}:{alt}:flags=area,format=rgb24", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    tam = largura * alt * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    i = 0
    try:
        while True:
            buf = proc.stdout.read(tam)
            if len(buf) < tam:
                break
            yield inicio + i / fps, buf, largura, alt
            i += 1
    finally:
        proc.stdout.close()
        proc.wait()


def amostras_audio(arquivo, taxa=16000, inicio=0.0, duracao=None) -> array:
    """Áudio mono 16 bits. Vídeo sem áudio → array vazio (quem chama confere `tem_audio`)."""
    cmd = [ffmpeg(), "-v", "error"]
    if inicio:
        cmd += ["-ss", f"{inicio:.3f}"]
    cmd += ["-i", str(arquivo)]
    if duracao:
        cmd += ["-t", f"{duracao:.3f}"]
    cmd += ["-vn", "-ac", "1", "-ar", str(taxa), "-f", "s16le", "pipe:1"]
    r = _rodar(cmd, binario=True)
    a = array("h")
    if r.returncode == 0 and r.stdout:
        a.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
    return a


def extrair_quadro(arquivo, t: float, saida, largura=540) -> Path:
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    r = _rodar([ffmpeg(), "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(arquivo), "-frames:v", "1",
                "-vf", f"scale={largura}:-2", "-y", str(saida)])
    if r.returncode != 0 or not saida.exists():
        raise MidiaInvalida(f"não consegui extrair o quadro em {t:.2f} s: {r.stderr.strip()[:200]}")
    return saida


def integro(arquivo) -> tuple[bool, str]:
    """Decodifica o arquivo inteiro; qualquer erro do decodificador = não íntegro."""
    r = _rodar([ffmpeg(), "-v", "error", "-i", str(arquivo), "-f", "null", "-"])
    erros = r.stderr.strip()
    return (r.returncode == 0 and not erros), erros[:300]


def recortar(arquivo, inicio: float, duracao: float, saida) -> Path:
    """Recorta recodificando (H.264 + AAC) para manter áudio e vídeo alinhados desde o 1º quadro."""
    info = sondar(arquivo)
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg(), "-v", "error", "-ss", f"{inicio:.3f}", "-i", str(arquivo), "-t", f"{duracao:.3f}",
           "-map", "0:v:0", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p"]
    if info["tem_audio"]:
        cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-movflags", "+faststart", "-y", str(saida)]
    r = _rodar(cmd)
    if r.returncode != 0 or not saida.exists():
        raise MidiaInvalida(f"falha ao recortar {Path(arquivo).name}: {r.stderr.strip()[:200]}")
    return saida
