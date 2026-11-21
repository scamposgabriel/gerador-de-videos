# Gerador de Vídeos — grava um vídeo tutorial a partir do roteiro de uma pasta em videos/.
#
#   py motor/gravar.py videos/<pasta>                 vídeo inteiro (gera as vozes que faltarem, grava e monta o MP4)
#   py motor/gravar.py videos/<pasta> --so 04-06      só as falas 04 a 06 (teste rápido de 20 a 30 s)
#   py motor/gravar.py videos/<pasta> --refazer-vozes gera as vozes de novo (depois de mudar o texto ou a voz)
#
# Como funciona (o mesmo princípio do HyperFrames, sem instalar nada além do Playwright):
#   - abre a página no Edge numa janela de 1600 x 900 com densidade 1,6 → cada quadro sai com 2560 x 1440 (QHD) de verdade;
#   - o relógio é do gravador: a cada 1/30 s ele avança as animações da camada (motor/camada.js) e fotografa a tela se algo mexeu;
#     quadro parado não é fotografado de novo, só fica mais tempo na tela. Por isso o vídeo sai liso e nítido em qualquer máquina;
#   - zoom, rolagem, cursor, holofote, legenda e cartões são calculados quadro a quadro; o texto é redesenhado a cada passo do zoom;
#   - cada fala entra no instante em que a legenda dela aparece; o ffmpeg junta quadros + narração (H.264, CRF 17, áudio normalizado).
# Não use o "screencast" do navegador: ele entrega 1600 x 900 mesmo pedindo mais, e o vídeo fica esticado e embaçado.
import asyncio, base64, importlib.util, json, shutil, subprocess, sys, time, wave
from pathlib import Path

MOTOR = Path(__file__).resolve().parent
RAIZ = MOTOR.parent
sys.path.insert(0, str(MOTOR))
import vozes  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

QUADRO = 1000 / 30


def carregar_roteiro(pasta: Path):
    spec = importlib.util.spec_from_file_location("roteiro", pasta / "roteiro.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


async def gravar(R, falas, aud: Path, quadros_dir: Path):
    cfg = R.CONFIG
    larg, alt = cfg.get("janela", (1600, 900))
    if quadros_dir.exists():
        shutil.rmtree(quadros_dir)
    quadros_dir.mkdir(parents=True)
    quadros, marcas = [], []
    estado = {"t": 0.0, "sujo": True}
    arq_logo = Path(R.__file__).parent / cfg["logo"] if cfg.get("logo") else MOTOR / "arte" / "logo.png"   # logo opcional ({{LOGO}} nas capas)
    logo = "data:image/png;base64," + base64.b64encode(arq_logo.read_bytes()).decode("ascii") if arq_logo.exists() else ""
    folga = cfg.get("folga_s", 0.7)
    async with async_playwright() as p:
        nav = await p.chromium.launch(channel="msedge")
        ctx = await nav.new_context(viewport={"width": larg, "height": alt}, device_scale_factor=cfg.get("densidade", 1.6))
        pg = await ctx.new_page()
        if cfg.get("init_script"):                      # roda antes da página (ex.: marcar tutorial e capa como vistos)
            await pg.add_init_script(cfg["init_script"])
        pagina = str(cfg["pagina"])
        await pg.goto(pagina if "://" in pagina else Path(pagina).resolve().as_uri())
        await pg.wait_for_timeout(cfg.get("esperar_ms", 2000))
        await pg.evaluate("([c, l, css, raiz]) => { window.VT_CAPAS = c; window.VT_LOGO = l; window.VT_CSS = css; window.VT_RAIZ = raiz; }",
                          [getattr(R, "CAPAS", {}), logo, getattr(R, "CSS_EXTRA", ""), cfg.get("raiz", "")])
        await pg.add_script_tag(path=str(MOTOR / "camada.js"))
        await pg.mouse.move(5, 5)

        async def foto():
            arq = quadros_dir / f"q{len(quadros) + 1:05d}.jpg"
            await pg.screenshot(path=str(arq), type="jpeg", quality=94)
            quadros.append((estado["t"], arq))
            estado["sujo"] = False

        async def passar(ms):
            for _ in range(max(1, round(ms / QUADRO))):
                mexeu = await pg.evaluate(f"VT.avancar({QUADRO})")
                estado["t"] += QUADRO
                if mexeu or estado["sujo"]:
                    await foto()

        async def assentar(limite=4000):
            n = 0
            while await pg.evaluate("VT.ativos()") and n * QUADRO < limite:
                await passar(QUADRO); n += 1

        js = lambda nome, *arg: pg.evaluate(f"VT.{nome}({', '.join(json.dumps(x) for x in arg)})")  # noqa: E731

        async def faz(a):
            nome, *arg = a
            if nome == "espera":
                await passar(arg[0] * 1000)
            elif nome == "foco":                       # câmera aproxima + holofote no mesmo ponto
                await js("zoom", arg[0], arg[1] if len(arg) > 1 else 1.4); await assentar(); await js("destacar", arg[0])
            elif nome == "zoom":
                await js("zoom", arg[0], arg[1] if len(arg) > 1 else 1.4); await assentar()
            elif nome == "zoom0":
                if await js("zoom0"): await assentar()
            elif nome == "rolarDentro":
                await js("rolarDentro", *arg); await assentar()
            elif nome == "menu":                       # clica num item de menu: arg = seletor CSS do item
                await js("apagar")
                if await js("zoom0"): await assentar()
                await js("cursorEm", arg[0], 0.35); await assentar()
                await js("clique"); await pg.click(arg[0]); await pg.mouse.move(5, 5)
                estado["sujo"] = True; await passar(250)
            elif nome == "clicar":                     # leva o cursor e clica de verdade
                await js("cursorEm", arg[0]); await assentar(); await js("clique"); await pg.click(arg[0]); await pg.mouse.move(5, 5)
                estado["sujo"] = True; await passar(250)
            elif nome == "clicarSemCursor":
                await pg.click(arg[0]); await pg.mouse.move(5, 5); estado["sujo"] = True; await passar(100)
            elif nome == "pairar":                     # cursor até o elemento e o mouse de verdade em cima (abre dicas de :hover)
                xy = await js("cursorEm", arg[0]); await assentar()
                if xy: await pg.mouse.move(xy[0], xy[1])
                estado["sujo"] = True; await passar(100)
            elif nome == "pairarFaixa":                # idem, numa faixa de SVG com data-tip que começa com o texto dado
                xy = await js("faixa", arg[0])
                if xy:
                    await js("cursor", xy[0], xy[1]); await assentar(); await pg.mouse.move(xy[0], xy[1])
                estado["sujo"] = True; await passar(100)
            elif nome == "soltar":
                await pg.mouse.move(5, 5); estado["sujo"] = True
            elif nome == "digitar":                    # escreve num campo: ("digitar", seletor, texto)
                await js("cursorEm", arg[0]); await assentar(); await js("clique"); await pg.click(arg[0])
                for ch in arg[1]:
                    await pg.keyboard.type(ch); estado["sujo"] = True; await passar(90)
            elif nome == "js":                         # roda um código na página (ex.: avisar a capa para entrar)
                await pg.evaluate(arg[0]); estado["sujo"] = True
            elif nome == "aguardar":                   # espera a página ficar pronta SEM andar o relógio do vídeo (o carregamento não aparece)
                try:
                    await pg.wait_for_function(arg[0], timeout=arg[1] if len(arg) > 1 else 90000)
                except Exception:
                    print(f"  aviso: demorou ({arg[0][:60]})", flush=True)
                await pg.wait_for_timeout(arg[2] if len(arg) > 2 else 800); estado["sujo"] = True
            elif nome == "esperarReal":                # espera de verdade (mapa, gráficos), sem andar o relógio do vídeo
                await pg.wait_for_timeout(arg[0]); estado["sujo"] = True
            elif nome == "focoPct":                    # ponto do tutorial (x %, y % da tela sem zoom): aproxima e destaca o bloco que está lá
                sel = await js("alvoPct", arg[0], arg[1])
                if sel:
                    await js("zoom", sel, arg[2] if len(arg) > 2 else 1.5); await assentar(); await js("destacar", sel)
                    await js("cursorPct", arg[0], arg[1])
                else:
                    await js("cursorPct", arg[0], arg[1])
            elif nome in ("focoFaixa", "focoRetPct"):  # aproxima e destaca uma faixa entre dois elementos, ou um retângulo em % da tela
                if await js("zoom0"): await assentar()
                n = 2 if nome == "focoFaixa" else 4
                sel = await js("marcarFaixa" if nome == "focoFaixa" else "marcarRetPct", *arg[:n])
                if sel:
                    await js("zoom", sel, arg[n] if len(arg) > n else 1.5); await assentar(); await js("destacar", sel, 6)
            elif nome == "destacarPct":
                sel = await js("alvoPct", arg[0], arg[1])
                if sel: await js("destacar", sel)
            elif nome == "clicarFrame":                # clica num elemento dentro de uma moldura (iframe): ("clicarFrame", "parte da url", seletor)
                fr = next((f for f in pg.frames if arg[0] in f.url), None)
                el = await fr.query_selector(arg[1]) if fr else None
                if el:
                    bx = await el.bounding_box()
                    await js("cursor", bx["x"] + bx["width"] * 0.4, bx["y"] + bx["height"] * 0.5); await assentar(); await js("clique")
                    await el.click(); estado["sujo"] = True; await passar(250)
            elif nome in ("rolar", "rolarTexto", "topo"):
                if await js("zoom0"): await assentar()
                await js(nome, *arg); await assentar()
            else:                                      # destacar, destacarFaixa, destacarColunas, destacarTexto, apagar, cursorEm,
                await js(nome, *arg)                   # clique, capa, semCapa, legenda, passo ... (ver docs/02_ACOES_DO_ROTEIRO.md)

        if falas[0].get("capa"):
            await js("capa", falas[0]["capa"])
        inicio = time.time()
        for f in falas:
            dur = vozes.duracao(aud / f"{f['id']}.wav")
            ini = estado["t"]
            marcas.append((f["id"], ini))
            legenda, passo = f.get("legenda", ""), f.get("passo", "")
            if cfg.get("passo_na_legenda"):           # o passo vai dentro da caixa da legenda (não cobre nada da tela)
                legenda = f'<span class="vt-passo">{passo}</span>{legenda}' if passo and legenda else legenda
                passo = ""
            await js("legenda", legenda); await js("passo", passo)
            if f.get("capa") and not f.get("acao") and f is not falas[0]:
                await js("capa", f["capa"])
            for a in f.get("acao", []):
                await faz(a)
            resta = (dur + folga) * 1000 - (estado["t"] - ini)
            if resta > 0:
                await passar(resta)
            print(f"fala {f['id']} ok ({len(quadros)} quadros, {time.time() - inicio:.0f} s)", flush=True)
        await passar(1200)
        await nav.close()
    return quadros, marcas, estado["t"]


def montar(quadros, marcas, fim, aud: Path, trabalho: Path, saida: Path, crf=17):
    lista = trabalho / "quadros.txt"
    linhas = ["ffconcat version 1.0"]
    for i, (t, arq) in enumerate(quadros):
        prox = quadros[i + 1][0] if i + 1 < len(quadros) else fim
        linhas += [f"file '{arq.as_posix()}'", f"duration {max(1.0, prox - t) / 1000:.5f}"]
    linhas.append(f"file '{quadros[-1][1].as_posix()}'")
    lista.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    with wave.open(str(aud / f"{marcas[0][0]}.wav")) as w:
        taxa, larg, canais = w.getframerate(), w.getsampwidth(), w.getnchannels()
    buf = bytearray(int(fim / 1000 * taxa) * larg * canais)
    for fid, ini in marcas:
        with wave.open(str(aud / f"{fid}.wav")) as w:
            dados = w.readframes(w.getnframes())
        pos = int((ini / 1000 + 0.12) * taxa) * larg * canais
        buf[pos:pos + len(dados)] = dados[:max(0, len(buf) - pos)]
    narr = trabalho / "narracao.wav"
    with wave.open(str(narr), "wb") as w:
        w.setnchannels(canais); w.setsampwidth(larg); w.setframerate(taxa); w.writeframes(bytes(buf))
    saida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(narr),
           "-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2:0:0,fps=30,scale=in_range=pc:out_range=tv,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-movflags", "+faststart", "-shortest", str(saida)]
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) < 2:
        raise SystemExit("uso: py motor/gravar.py videos/<pasta> [--so 04-06] [--refazer-vozes]")
    pasta = Path(sys.argv[1]).resolve()
    R = carregar_roteiro(pasta)
    falas = list(R.FALAS)
    teste = "--so" in sys.argv
    if teste:
        a, b = sys.argv[sys.argv.index("--so") + 1].split("-")
        falas = [f for f in falas if a <= f["id"] <= b]
    voz = R.CONFIG["voz"]
    trabalho = Path.home() / "AppData" / "Local" / "Temp" / "gerador_videos" / pasta.name   # quadros ficam no disco local (rápido)
    aud = vozes.gerar(voz, list(R.FALAS), pasta / "falas" / f"{voz['motor']}-{voz['nome']}", "--refazer-vozes" in sys.argv)
    print(f"vozes prontas ({voz['motor']} {voz['nome']}). Gravando {len(falas)} falas...", flush=True)
    q, m, fim = asyncio.run(gravar(R, falas, aud, trabalho / "quadros"))
    local = trabalho / ("teste.mp4" if teste else "video.mp4")
    montar(q, m, fim, aud, trabalho, local, R.CONFIG.get("crf", 17))
    destino = pasta / "saida" / ("teste.mp4" if teste else Path(R.CONFIG["saida"]).name)
    destino.parent.mkdir(exist_ok=True)
    shutil.copyfile(local, destino)                 # arquivo grande: grava local e copia para a rede
    print(f"pronto: {destino} ({destino.stat().st_size / 1e6:.1f} MB, {fim / 1000:.0f} s, {len(q)} quadros fotografados)")
    if not teste and R.CONFIG.get("publicar_em"):
        print(f"para publicar, copie para: {R.CONFIG['publicar_em']} (o gravador não sobrescreve a pasta da equipe sozinho)")


if __name__ == "__main__":
    main()
