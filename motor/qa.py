# Controle de qualidade do vídeo pronto. Roda sozinho no fim do animar.py; à mão:  py motor/qa.py <video.mp4> [<video2.mp4> ...]
# Pedido do Gabriel (revisão de 21/11/2026): nada de congelamento involuntário acima de 1 s, arquivo íntegro, resolução e FPS certos,
# textos legíveis, chamada final visível. O relatório diz o que passou, o que falhou e o que é só aviso.
import json, re, subprocess, sys
from pathlib import Path


def _ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr


def verificar(video, tela=(1080, 1920), fps=30, limite_congelado=1.0, ignorar_congelado=()):
    """Devolve {problemas: [...], avisos: [...], medidas...}. ignorar_congelado = [(ini, fim)] de pausas intencionais."""
    v = str(video)
    rel = {"arquivo": Path(v).name, "problemas": [], "avisos": []}
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                    "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels,nb_frames",
                                    "-of", "json", v], capture_output=True, text=True).stdout or "{}")
    vid = next((s for s in pr.get("streams", []) if s["codec_type"] == "video"), None)
    aud = next((s for s in pr.get("streams", []) if s["codec_type"] == "audio"), None)
    if not vid:
        rel["problemas"].append("arquivo sem vídeo (ou corrompido)")
        return rel
    rel["duracao_s"] = round(float(pr["format"]["duration"]), 2)
    rel["tamanho_mb"] = round(int(pr["format"]["size"]) / 1e6, 1)
    rel["video"] = f'{vid["codec_name"]} {vid["width"]}x{vid["height"]} {vid["r_frame_rate"]} q/s {vid.get("pix_fmt", "")}'
    rel["audio"] = f'{aud["codec_name"]} {aud["sample_rate"]} Hz, {aud["channels"]} canais' if aud else None
    if (int(vid["width"]), int(vid["height"])) != tuple(tela):
        rel["problemas"].append(f'resolução {vid["width"]}x{vid["height"]} (esperado {tela[0]}x{tela[1]})')
    num, den = (int(x) for x in vid["r_frame_rate"].split("/"))
    if abs(num / den - fps) > 0.01:
        rel["problemas"].append(f"FPS {num / den:.2f} (esperado {fps})")
    if not aud:
        rel["problemas"].append("sem áudio")
    # integridade: decodifica o arquivo inteiro
    erros = _ff(["-v", "error", "-i", v, "-f", "null", "-"]).strip()
    if erros:
        rel["problemas"].append("erros ao decodificar: " + erros.splitlines()[0][:160])
    # congelamentos (imagem praticamente igual por mais de limite_congelado segundos)
    # -50 dB: calibrado em 21/11/2026 com o Teste 01 (acha os mesmos 2,5 s parados do início que o GPT mediu; legenda trocando
    # sobre um clipe congelado não conta como movimento). -45 dB ou menos já marca estrada lenta como parada.
    out = _ff(["-i", v, "-vf", f"freezedetect=n=-50dB:d={limite_congelado}", "-map", "0:v", "-f", "null", "-"])
    ini = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", out)]
    fim = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", out)]
    congel = []
    for i, a in enumerate(ini):
        b = fim[i] if i < len(fim) else rel["duracao_s"]
        intencional = any(x <= a and b <= y for x, y in ignorar_congelado)
        congel.append({"de": round(a, 2), "ate": round(b, 2), "dur": round(b - a, 2), "intencional": intencional})
    rel["congelamentos"] = congel
    for c in congel:
        (rel["avisos"] if c["intencional"] else rel["problemas"]).append(
            f'imagem parada de {c["de"]:.2f} s a {c["ate"]:.2f} s ({c["dur"]:.2f} s){" — pausa intencional" if c["intencional"] else ""}')
    # quadros repetidos (mpdecimate descarta quadros praticamente iguais ao anterior)
    out = _ff(["-i", v, "-vf", "mpdecimate=hi=200:lo=64:frac=0.33,showinfo", "-map", "0:v", "-f", "null", "-"])
    mantidos = len(re.findall(r"\] n:\s*\d+", out))
    total = round(rel["duracao_s"] * fps)
    if total:
        rel["quadros_repetidos_pct"] = round(100 * max(0, total - mantidos) / total, 1)
        if rel["quadros_repetidos_pct"] > 25:
            rel["avisos"].append(f'{rel["quadros_repetidos_pct"]}% de quadros quase iguais ao anterior (pouco movimento)')
    # tela preta
    out = _ff(["-i", v, "-vf", "blackdetect=d=0.4:pix_th=0.06", "-map", "0:v", "-f", "null", "-"])
    for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", out):
        rel["problemas"].append(f"tela preta de {float(a):.2f} s a {float(b):.2f} s")
    # volume (Instagram/TikTok normalizam perto de -14 LUFS)
    out = _ff(["-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out); p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    if m:
        rel["volume_lufs"] = float(m[-1])
        if not -16.5 <= rel["volume_lufs"] <= -12.5:
            rel["avisos"].append(f'volume {rel["volume_lufs"]} LUFS (alvo -14)')
    if p:
        rel["pico_dbfs"] = float(p[-1])
        if rel["pico_dbfs"] > -0.5:
            rel["problemas"].append(f'pico de áudio {rel["pico_dbfs"]} dBFS (pode distorcer)')
    return rel


def imprimir(rel):
    print(f'\n== Controle de qualidade: {rel["arquivo"]}')
    for k in ("duracao_s", "tamanho_mb", "video", "audio", "volume_lufs", "pico_dbfs", "quadros_repetidos_pct"):
        if k in rel:
            print(f"   {k}: {rel[k]}")
    for p in rel["problemas"]:
        print("   PROBLEMA:", p)
    for a in rel["avisos"]:
        print("   aviso:", a)
    print("   resultado:", "APROVADO" if not rel["problemas"] else f'REPROVADO ({len(rel["problemas"])} problema(s))', flush=True)


if __name__ == "__main__":
    for arq in sys.argv[1:]:
        imprimir(verificar(arq))
