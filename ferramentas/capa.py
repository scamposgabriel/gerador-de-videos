# Gera a CAPA do Reels (1080 x 1920) de um vídeo animado cuja página desenha a capa em render(t < 0) (ver o exemplo).
#   py ferramentas/capa.py videos/<pasta>          →  videos/<pasta>/saida/Capa.png
import subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
pasta = Path(sys.argv[1]).resolve()
subprocess.run([sys.executable, str(RAIZ / "motor" / "animar.py"), str(pasta), "--fotos=-1"], check=True)
foto, capa = pasta / "saida" / "fotos" / "foto_-01.00.png", pasta / "saida" / "Capa.png"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(foto), "-vf", "scale=1080:1920:flags=lanczos", str(capa)], check=True)
foto.unlink()
print(f"capa: {capa}")
