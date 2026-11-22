"""Gera o vídeo SINTÉTICO da POC 01 (12 s, 1080 × 1920, sem material de terceiros) só com geradores do FFmpeg:
0–2 s fractal em zoom · 2–5 s autômato celular · 5–9 s padrão de teste · 9–12 s cor sólida com fade.
Áudio: tom com "sílabas" (modulação), pausa de 7,9 a 8,6 s e um bipe no fim.

    py creative-intelligence/exemplos/poc01-sintetico/gerar_video.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_intelligence.midia import ffmpeg  # noqa: E402

AQUI = Path(__file__).resolve().parent
S = "1080x1920"
partes = [f"mandelbrot=s={S}:r=30,trim=duration=2", f"life=s={S}:r=30:mold=10:ratio=0.2,trim=duration=3",
          f"testsrc2=s={S}:r=30,trim=duration=4", f"color=c=orange:s={S}:r=30,trim=duration=3,fade=t=out:st=2:d=1"]
entradas = []
for p in partes:
    entradas += ["-f", "lavfi", "-i", p]
voz = "aevalsrc='if(between(t,7.9,8.6),0,0.4*sin(2*PI*220*t)*(0.5+0.5*sin(2*PI*4*t)))+if(gt(t,11.5),0.5*sin(2*PI*880*t),0)':s=48000:d=12"
saida = AQUI / "poc01_sintetico.mp4"
cmd = [ffmpeg(), "-v", "error", *entradas, "-f", "lavfi", "-i", voz,
       "-filter_complex", "[0][1][2][3]concat=n=4:v=1:a=0,format=yuv420p[v]", "-map", "[v]", "-map", "4:a",
       "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", "-y", str(saida)]
subprocess.run(cmd, check=True)
print(saida)
