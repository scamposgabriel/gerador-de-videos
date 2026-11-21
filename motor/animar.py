# Gerador de Vídeos — modo ANIMADO (sem ferramenta por trás): uma página HTML desenha cada quadro a partir do tempo e o motor fotografa.
# Serve para vídeo explicativo, Instagram (Reels em pé), abertura animada etc. O modo de tutorial de ferramenta continua no gravar.py.
#
#   py motor/animar.py videos/<pasta>                  vídeo inteiro (e a versão sem música, se o roteiro tiver saida_so_voz)
#   py motor/animar.py videos/<pasta> --ate 12         só os primeiros 12 s (teste);  --de 20 --ate 32 também vale
#   py motor/animar.py videos/<pasta> --fotos 1,8.5    só fotos PNG desses instantes (em saida/fotos), para conferir rápido
#   py motor/animar.py videos/<pasta> --refazer-vozes  gera as vozes de novo (depois de mudar texto ou voz)
#
# O roteiro (roteiro.py) tem CONFIG (pagina, tela, densidade, voz, saida, saida_so_voz, trilha, intro, folga, fim) e FALAS (id, cena, fala).
# A página precisa ter duas funções:
#   async iniciar(TL)  recebe a linha do tempo {cenas: [{id, cena, ini, fim, dur, fala, palavras: [{t, d, w}]}], total}
#                      e devolve a lista de sons [{t, som, vol, nota, dur, pan}] (ver motor/trilha.py);
#   render(t)          desenha o instante t (em segundos). Tem que depender SÓ de t (nada de estado do quadro anterior):
#                      assim qualquer trecho pode ser refeito sozinho e o resultado é sempre o mesmo.
# Nitidez: a página é desenhada com densidade 2 (Reels: 2160 x 3840) e reduzida para 1080 x 1920 com lanczos (borda lisa, texto firme).
import argparse, asyncio, importlib.util, json, math, shutil, subprocess, sys, time, wave
from pathlib import Path

MOTOR = Path(__file__).resolve().parent
sys.path.insert(0, str(MOTOR))
import qa, trilha, vozes  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

FPS = 30


def carregar_roteiro(pasta: Path):
    spec = importlib.util.spec_from_file_location("roteiro", pasta / "roteiro.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def palavras_estimadas(texto, dur):
    """Sem o tempo de cada palavra (voz do Windows/ElevenLabs): reparte a duração pelo tamanho das palavras."""
    ws = texto.split(); tot = sum(len(w) + 2 for w in ws) or 1; t = 0.0; out = []
    for w in ws:
        d = dur * (len(w) + 2) / tot; out.append({"t": round(t, 3), "d": round(d, 3), "w": w.strip(".,!?;:")}); t += d
    return out


def linha_do_tempo(R, aud: Path):
    cfg = R.CONFIG; folga = cfg.get("folga", 0.45); t = cfg.get("intro", 0.5); cenas = []
    for f in R.FALAS:
        dur = vozes.duracao(aud / f"{f['id']}.wav")
        pj = aud / f"{f['id']}.palavras.json"
        pal = json.loads(pj.read_text(encoding="utf-8")) if pj.exists() else palavras_estimadas(f["fala"], dur)
        cenas.append({"id": f["id"], "cena": f["cena"], "ini": round(t, 3), "dur": round(dur, 3), "fala": f["fala"], "palavras": pal})
        t += dur + f.get("folga", folga)
    total = t - folga + cfg.get("fim", 2.5)
    for i, c in enumerate(cenas):
        c["fim"] = cenas[i + 1]["ini"] if i + 1 < len(cenas) else round(total, 3)
    # outros dados do roteiro para a página (ex.: CARTAO com nome e @ do cartão final): todo nome em MAIÚSCULAS além de CONFIG e FALAS
    dados = {k.lower(): v for k, v in vars(R).items() if k.isupper() and k not in ("CONFIG", "FALAS") and isinstance(v, (dict, list, str, int, float))}
    return {"cenas": cenas, "total": round(total, 3), "dados": dados}


def preparar_midia(R, pasta: Path, trabalho: Path) -> dict:
    """Clipes de vídeo reais (MIDIA no roteiro) viram quadros JPEG a 30 q/s no disco LOCAL, mais uma versão desfocada em pé para o
    fundo. A página troca o quadro a cada 1/30 s (sincronia exata, sem depender do player do navegador).
    MIDIA = {"nome": dict(arquivo="midia/66.mp4", ini=0, dur=None)}.  Devolve {nome: {base, fundo, n, fps, larg, alt}}."""
    out = {}
    for nome, m in getattr(R, "MIDIA", {}).items():
        src = (pasta / m["arquivo"]).resolve()
        dest = trabalho / "midia" / nome
        chave = f"{src.stat().st_size}-{src.stat().st_mtime}-{m.get('ini', 0)}-{m.get('dur')}"
        marca = dest / "pronto.json"
        if not (marca.exists() and json.loads(marca.read_text(encoding="utf-8")).get("chave") == chave):
            shutil.rmtree(dest, ignore_errors=True); (dest / "f").mkdir(parents=True)
            corte = ["-ss", str(m.get("ini", 0)), "-i", str(src)] + (["-t", str(m["dur"])] if m.get("dur") else [])
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *corte, "-vf", "fps=30", "-q:v", "2", str(dest / "%05d.jpg")], check=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *corte, "-vf",
                            "fps=30,scale=-2:480,crop=270:480,boxblur=14:3,eq=brightness=-0.12:saturation=1.15", "-q:v", "4",
                            str(dest / "f" / "%05d.jpg")], check=True)
            larg, alt = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                                          "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip().split(",")[:2])
            marca.write_text(json.dumps({"chave": chave, "n": len(list(dest.glob("*.jpg"))), "larg": larg, "alt": alt}), encoding="utf-8")
        info = json.loads(marca.read_text(encoding="utf-8"))
        out[nome] = {"base": dest.as_uri() + "/", "fundo": (dest / "f").as_uri() + "/", "n": info["n"], "fps": 30, "larg": info["larg"], "alt": info["alt"]}
        print(f"  mídia {nome}: {info['n']} quadros ({info['larg']}x{info['alt']})", flush=True)
    return out


def narracao(TL, aud: Path, arq: Path):
    with wave.open(str(aud / f"{TL['cenas'][0]['id']}.wav")) as w:
        taxa = w.getframerate()
    buf = bytearray(int(TL["total"] * taxa) * 2)
    for c in TL["cenas"]:
        with wave.open(str(aud / f"{c['id']}.wav")) as w:
            dados = w.readframes(w.getnframes())
        pos = int(c["ini"] * taxa) * 2
        buf[pos:pos + len(dados)] = dados[:max(0, len(buf) - pos)]
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(bytes(buf))


async def desenhar(R, pasta: Path, TL, de=0.0, ate=None, video: Path = None, fotos=None, pasta_fotos: Path = None):
    cfg = R.CONFIG; larg, alt = cfg.get("tela", (1080, 1920)); dens = cfg.get("densidade", 2)
    async with async_playwright() as p:
        nav = await p.chromium.launch(channel="msedge")
        ctx = await nav.new_context(viewport={"width": larg, "height": alt}, device_scale_factor=dens)
        pg = await ctx.new_page()
        pg.on("console", lambda m: print("  página:", m.text, flush=True) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: print("  ERRO NA PÁGINA:", e, flush=True))
        await pg.goto((pasta / cfg["pagina"]).resolve().as_uri())
        await pg.wait_for_load_state("networkidle")
        eventos = await pg.evaluate("TL => iniciar(TL)", TL)
        pequenos = await pg.evaluate(TEXTOS_PEQUENOS)          # texto pequeno demais para o celular (menos de 26 px em 1080)
        for txt, tam in pequenos[:8]:
            print(f"  aviso: texto pequeno ({tam:.0f} px): {txt}", flush=True)
        if fotos:
            pasta_fotos.mkdir(parents=True, exist_ok=True)
            for t in fotos:
                await pg.evaluate(f"render({t})")
                await pg.screenshot(path=str(pasta_fotos / f"foto_{t:06.2f}.png"))
            print(f"fotos em {pasta_fotos}")
        if video:
            n0, n1 = round(de * FPS), math.ceil((ate if ate is not None else TL["total"]) * FPS)
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                   "-vf", f"scale={larg}:{alt}:flags=lanczos:in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p",
                   "-c:v", "libx264", "-preset", "slow", "-crf", str(cfg.get("crf", 16)), "-profile:v", "high",
                   "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(video)]
            ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            ini = time.time()
            for i in range(n0, n1):
                await pg.evaluate(f"render({i / FPS:.5f})")
                ff.stdin.write(await pg.screenshot(type="jpeg", quality=95))
                if (i - n0) % 150 == 0:
                    feito = i - n0 + 1
                    print(f"  quadro {i - n0 + 1}/{n1 - n0} ({i / FPS:.1f} s do vídeo; {time.time() - ini:.0f} s gastos; "
                          f"faltam ~{(time.time() - ini) / feito * (n1 - i):.0f} s)", flush=True)
            ff.stdin.close(); ff.wait()
        await nav.close()
    return eventos


TEXTOS_PEQUENOS = """() => { const out = []; for (const e of document.querySelectorAll("body *")) { if (["SCRIPT", "STYLE"].includes(e.tagName)) continue;
  const t = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(" ").trim();
  if (!t || t.length <= 3) continue; const fs = parseFloat(getComputedStyle(e).fontSize); if (fs < 26) out.push([t.slice(0, 50), fs]); } return out; }"""


def mixar(video, narr, efx, mus, saida, de, dur, cfg=None):
    """Junta o vídeo (sem áudio) com voz + efeitos (+ música, que abaixa sozinha quando a voz fala). Volume final -14 LUFS (Instagram).
    cfg: voz_compressor (voz mais constante, "de locutor") e duck_ratio (quanto a música abaixa sob a voz; padrão 6, as referências ~3)."""
    cfg = cfg or {}
    trecho = ["-ss", f"{de:.3f}", "-t", f"{dur:.3f}"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), *trecho, "-i", str(narr), *trecho, "-i", str(efx)]
    comp = ",acompressor=threshold=-22dB:ratio=3:attack=6:release=140:makeup=3" if cfg.get("voz_compressor") else ""
    voz = f"[1:a]aresample=48000{comp},pan=stereo|c0=c0|c1=c0"
    if mus:
        cmd += [*trecho, "-i", str(mus)]
        filtro = (f"{voz},asplit=2[voz][vsc];"
                  f"[3:a]aresample=48000[m];[m][vsc]sidechaincompress=threshold=0.015:ratio={cfg.get('duck_ratio', 6)}:attack=20:release=450[duck];"
                  "[voz][2:a][duck]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        filtro = f"{voz}[voz];[voz][2:a]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    cmd += ["-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-shortest", str(saida)]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description="Vídeo animado: página HTML desenhada quadro a quadro + voz + trilha")
    ap.add_argument("pasta"); ap.add_argument("--de", type=float, default=0.0); ap.add_argument("--ate", type=float)
    ap.add_argument("--fotos"); ap.add_argument("--refazer-vozes", action="store_true")
    a = ap.parse_args()
    pasta = Path(a.pasta).resolve(); R = carregar_roteiro(pasta); cfg = R.CONFIG; voz = cfg["voz"]
    aud = vozes.gerar(voz, list(R.FALAS), pasta / "falas" / f"{voz['motor']}-{voz['nome']}", a.refazer_vozes)
    TL = linha_do_tempo(R, aud)
    print(f"vozes prontas ({voz['nome']}); vídeo de {TL['total']:.1f} s, {len(TL['cenas'])} cenas", flush=True)
    trabalho = Path.home() / "AppData" / "Local" / "Temp" / "gerador_videos" / pasta.name   # arquivo grande: monta no disco local
    trabalho.mkdir(parents=True, exist_ok=True)
    TL["midia"] = preparar_midia(R, pasta, trabalho)
    (trabalho / "linha_do_tempo.json").write_text(json.dumps(TL, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.fotos:
        asyncio.run(desenhar(R, pasta, TL, fotos=[float(x) for x in a.fotos.split(",")], pasta_fotos=pasta / "saida" / "fotos"))
        return
    teste = a.ate is not None or a.de > 0
    ate = min(a.ate if a.ate is not None else TL["total"], TL["total"])
    video = trabalho / "so_imagem.mp4"
    eventos = asyncio.run(desenhar(R, pasta, TL, a.de, ate, video))
    narr, efx, mus = trabalho / "narracao.wav", trabalho / "efeitos.wav", trabalho / "musica.wav"
    narracao(TL, aud, narr)
    trilha.efeitos(eventos, TL["total"], efx)
    if cfg.get("trilha"):                          # "suave" (explicativo) ou "batida" (propaganda)
        if cfg.get("trilha_estilo") == "batida":
            trilha.batida(TL["total"], mus, cfg.get("bpm", 118))
        elif cfg.get("trilha_estilo") == "lofi":
            trilha.lofi(TL["total"], mus, cfg.get("bpm", 92))
        else:
            trilha.musica(TL["total"], mus)
    saidas = [(cfg["saida"], cfg.get("trilha"))]
    if cfg.get("saida_so_voz") and not teste:
        saidas.append((cfg["saida_so_voz"], False))
    for nome, com_musica in saidas:
        local = trabalho / ("teste.mp4" if teste else Path(nome).name)
        mixar(video, narr, efx, mus if com_musica else None, local, a.de, ate - a.de, cfg)
        destino = pasta / "saida" / local.name
        destino.parent.mkdir(exist_ok=True)
        shutil.copyfile(local, destino)                 # grava local e copia para a rede
        print(f"pronto: {destino} ({destino.stat().st_size / 1e6:.1f} MB, {ate - a.de:.1f} s)")
        if teste:
            break
    if not teste:                                   # controle de qualidade do vídeo principal (relatório ao lado do MP4)
        rel = qa.verificar(pasta / "saida" / Path(cfg["saida"]).name, tuple(cfg.get("tela", (1080, 1920))), FPS,
                           ignorar_congelado=cfg.get("pausas_intencionais", ()))
        rel["chamada_final_s"] = round(TL["total"] - max(c["ini"] + c["dur"] for c in TL["cenas"]), 2)
        if rel["chamada_final_s"] < 2.5:
            rel["avisos"].append(f'cartão final só {rel["chamada_final_s"]} s na tela (mínimo 2,5 s)')
        qa.imprimir(rel)
        (pasta / "saida" / "controle_de_qualidade.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
