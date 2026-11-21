# Confere os TEXTOS de um vídeo animado a cada 0,25 s (e na capa): texto cortado no cartão, fora da tela, ou nas áreas que o
# Instagram cobre (descrição embaixo, abaixo de 1600 px; coluna de botões à direita, x > 960 entre 1100 e 1750 px).
#   py ferramentas/verificar_textos.py videos/<pasta>
# Antes, rode o vídeo pelo menos uma vez (ex.: --fotos 0) para existir a linha do tempo. Resultado: saida/verificacao_textos.json.
# Mede a caixa das LETRAS (não do bloco). Algarismo muito grande pode acusar "cortado" só pela altura da fonte: confira numa foto.
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

JS = """() => { const out = [];
  const vis = (e) => { let op = 1; for (let x = e; x && x.nodeType === 1; x = x.parentElement || x.parentNode) { const cs = getComputedStyle(x);
    if (cs.display === "none" || cs.visibility === "hidden") return 0; op *= parseFloat(cs.opacity); } return op; };
  for (const e of document.querySelectorAll("body *")) { if (["SCRIPT", "STYLE"].includes(e.tagName)) continue;
    const txt = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(" ").trim(); if (!txt) continue;
    if (vis(e) < 0.3) continue;
    let r = null; for (const nd of e.childNodes) { if (nd.nodeType !== 3 || !nd.textContent.trim()) continue; const rg = document.createRange(); rg.selectNodeContents(nd);
      const b = rg.getBoundingClientRect(); r = r ? { left: Math.min(r.left, b.left), top: Math.min(r.top, b.top), right: Math.max(r.right, b.right), bottom: Math.max(r.bottom, b.bottom) } : b; }
    if (!r || r.right - r.left < 1) continue;
    const prob = [];
    if (r.left < -2 || r.right > 1082 || r.top < -2 || r.bottom > 1922) prob.push("fora da tela");
    const cart = e.closest(".cartao"); if (cart) { const c = cart.getBoundingClientRect();
      if (r.left < c.left - 2 || r.right > c.right + 2 || r.top < c.top - 2 || r.bottom > c.bottom + 2) prob.push("cortado no cartao"); }
    if (r.bottom > 1600) prob.push("abaixo de 1600 px (descricao do Instagram)");
    if (r.right > 960 && r.bottom > 1100 && r.top < 1750) prob.push("coluna de botoes do Instagram");
    if (prob.length) out.push({ texto: txt.slice(0, 40), problemas: prob });
  } return out; }"""


async def main():
    pasta = Path(sys.argv[1]).resolve()
    tl_arq = Path.home() / "AppData" / "Local" / "Temp" / "gerador_videos" / pasta.name / "linha_do_tempo.json"   # mesmo lugar do animar.py
    if not tl_arq.exists():
        sys.exit(f"Rode antes: py motor/animar.py {sys.argv[1]} --fotos 0   (cria a linha do tempo)")
    tl = json.loads(tl_arq.read_text(encoding="utf-8"))
    res = []
    async with async_playwright() as p:
        nav = await p.chromium.launch(channel="msedge")
        pg = await (await nav.new_context(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)).new_page()
        await pg.goto((pasta / "pagina.html").as_uri()); await pg.wait_for_load_state("networkidle")
        await pg.evaluate("TL => iniciar(TL)", tl)
        ts = [round(i * 0.25, 2) for i in range(int(tl["total"] / 0.25) + 1)] + [-1]
        for t in ts:
            await pg.evaluate(f"render({t})")
            res += [dict(t=t, **x) for x in await pg.evaluate(JS)]
        await nav.close()
    resumo = {}
    for o in res:
        resumo.setdefault(f'{o["texto"]} | {", ".join(o["problemas"])}', []).append(o["t"])
    rel = {"instantes": len(ts), "ocorrencias": {k: {"de": min(v), "ate": max(v), "vezes": len(v)} for k, v in resumo.items()}}
    (pasta / "saida").mkdir(exist_ok=True)
    (pasta / "saida" / "verificacao_textos.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ts)} instantes conferidos (t = -1 é a capa)")
    for k, v in rel["ocorrencias"].items():
        print(f"  {k}: t = {v['de']} a {v['ate']} ({v['vezes']}x)")
    print("nenhum problema" if not res else "confira cada ocorrência numa foto (--fotos) antes de corrigir")


asyncio.run(main())
