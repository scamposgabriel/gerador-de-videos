// Camada do Gerador de Vídeos: legenda, passo, holofote, cursor, clique, câmera (zoom e rolagem) e cartões.
// As capas (abertura, fim e quadros explicativos) vêm do roteiro de cada vídeo (window.VT_CAPAS); {{LOGO}} vira o logo do CONFIG["logo"] (opcional).
// Nenhuma animação roda sozinha no navegador: tudo anda pelo relógio do gravador (VT.avancar), 1/30 s por quadro,
// e cada quadro é fotografado na resolução real (QHD). É o mesmo princípio do HyperFrames: o vídeo sai liso e nítido,
// sem depender da velocidade da máquina. Só existe durante a gravação: a página gravada não é alterada.
window.VT = (() => {
  const css = `
  *,*::before,*::after{transition:none!important;animation:none!important}
  html,body{overflow-x:hidden!important;scroll-behavior:auto!important}
  .app,body{transform-origin:0 0}
  .vt-cap{position:fixed;left:50%;bottom:34px;max-width:1180px;width:max-content;z-index:2147482000;opacity:0;
    background:rgba(11,22,44,.93);color:#fff;font:600 25px/1.38 "Segoe UI",system-ui,sans-serif;padding:16px 28px;border-radius:16px;
    box-shadow:0 12px 40px rgba(0,0,0,.35);text-align:center;letter-spacing:.1px;transform:translate(-50%,0)}
  .vt-cap b{color:#93C5FD;font-weight:700}
  .vt-cap.topo{bottom:auto;top:64px}
  .vt-cap .vt-passo{display:block;font-size:13px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#93C5FD;margin-bottom:5px}
  .vt-chip{position:fixed;top:18px;left:50%;transform:translateX(-50%);z-index:2147482100;background:#3B82F6;color:#fff;font:700 15px "Segoe UI",sans-serif;
    padding:7px 16px;border-radius:30px;letter-spacing:.04em;opacity:0;box-shadow:0 6px 18px rgba(0,0,0,.2)}
  .vt-spot{position:fixed;z-index:2147480000;border-radius:14px;pointer-events:none;opacity:0;box-shadow:0 0 0 4px #3B82F6,0 0 0 9999px rgba(8,18,38,.46)}
  .vt-cur{position:fixed;left:0;top:0;z-index:2147483000;width:30px;height:30px;pointer-events:none;opacity:0;filter:drop-shadow(0 3px 5px rgba(0,0,0,.35))}
  .vt-rip{position:fixed;z-index:2147482500;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;border:3px solid #3B82F6;pointer-events:none}
  .vt-card{position:fixed;inset:0;z-index:2147479000;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none}
  .vt-capa{position:absolute;inset:0;background:radial-gradient(1200px 700px at 75% 20%,#1E293B 0%,#0F172A 45%,#0B1120 100%);color:#fff;
    display:flex;flex-direction:column;justify-content:center;padding:0 120px;font-family:"Segoe UI",sans-serif}
  .vt-capa img{width:250px;margin-bottom:46px;filter:brightness(0) invert(1)}
  .vt-capa .k{font-size:20px;letter-spacing:.18em;text-transform:uppercase;color:#93C5FD;font-weight:700}
  .vt-capa h1{font-size:66px;line-height:1.08;margin:14px 0 18px;font-weight:800;max-width:1100px}
  .vt-capa p{font-size:27px;color:#c9d6e8;margin:0;max-width:1050px;line-height:1.4}
  .vt-capa .linha{width:120px;height:5px;background:#3B82F6;border-radius:3px;margin:30px 0 0;transform-origin:0 50%}
  .vt-capa ol{font-size:27px;line-height:1.75;color:#e6eefb;margin:22px 0 0;padding-left:34px}
  .vt-capa ol b{color:#93C5FD}
  .vt-plan-f{position:absolute;inset:0;background:rgba(8,18,38,.86)}
  .vt-plan{position:relative;background:#fff;border-radius:18px;box-shadow:0 30px 80px rgba(0,0,0,.4);padding:26px 28px 22px;width:1500px;font-family:Calibri,"Segoe UI",sans-serif}
  .vt-plan .t{display:flex;align-items:center;gap:12px;font:700 22px "Segoe UI",sans-serif;color:#0f1b33;margin-bottom:16px}
  .vt-plan .t i{width:34px;height:34px;border-radius:8px;background:#1d6f42;display:inline-block}
  .vt-plan table{border-collapse:collapse;font-size:15px;width:100%;table-layout:fixed}
  .vt-plan td{border:1px solid #d6dbe1;padding:7px 8px;height:34px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#1f2a33}
  .vt-plan tr.letras td{background:#eef1f4;color:#5b6672;text-align:center;font-weight:600;height:24px;padding:2px}
  .vt-plan td.n{background:#eef1f4;color:#5b6672;text-align:center;width:34px}
  .vt-plan tr.cab td{font-weight:700;text-align:center;white-space:normal;line-height:1.15;height:46px;font-size:14px}
  .vt-plan td.am{background:#fff2cc}.vt-plan tr.cab td.am{color:#5a3b00;border-bottom:2px solid #334155}
  .vt-plan td.vd{background:#e2f0d9}.vt-plan tr.cab td.vd{color:#1f4d1f;border-bottom:2px solid #334155}
  .vt-plan td.cz{background:#eef2f5;color:#5b6672}.vt-plan tr.cab td.cz{background:#dde6ec;color:#1f2a33;border-bottom:2px solid #334155}
  .vt-plan .leg{display:flex;gap:26px;margin-top:16px;font:15px "Segoe UI",sans-serif;color:#4a5670}
  .vt-plan .leg span{display:flex;align-items:center;gap:8px}.vt-plan .leg i{width:16px;height:16px;border-radius:4px;display:inline-block;border:1px solid #c9d3da}
  .vt-plan .pasta{margin-top:16px;display:inline-flex;align-items:center;gap:10px;background:#f3f5f9;border:1px solid #e4e8f0;border-radius:10px;padding:10px 14px;font:15px "Segoe UI",sans-serif;color:#4a5670}
  .vt-plan .pasta b{color:#0f1b33}
  `;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  if (window.Chart && Chart.defaults) Chart.defaults.animation = false;
  // as peças do vídeo ficam no <html>, fora do <body>: o zoom pode ser no próprio body sem levar legenda, cursor e holofote junto
  const el = (c) => { const e = document.createElement('div'); e.className = c; document.documentElement.appendChild(e); return e; };
  let nAlvo = 0;
  const spot = el('vt-spot'), card = el('vt-card'), cap = el('vt-cap'), chip = el('vt-chip'), cur = el('vt-cur');
  cur.innerHTML = '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M4 2l15 11.2-6.6.9 3.9 7.4-2.6 1.4-3.9-7.5L4 20z" fill="#fff" stroke="#0b1f3a" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  // elemento que recebe o zoom: CONFIG['raiz'] do roteiro (padrão .app; sem ela, o corpo da página)
  const app = document.querySelector(window.VT_RAIZ || '.app') || document.body;

  // ---------------------------------------------------------------- relógio e animações
  let T = 0;
  const tw = new Map();
  const suave = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);   // entra e sai devagar
  const mistura = (a, b, e) => (Array.isArray(a) ? a.map((x, i) => x + (b[i] - x) * e) : a + (b - a) * e);
  function anima(canal, de, para, dur, aplicar, atraso, fim) {
    const a = { de, para, ini: T + (atraso || 0), dur: Math.max(1, dur), aplicar, fim };
    tw.set(canal, a); if (!atraso) aplicar(de);
  }
  // estado atual de cada peça (o tween parte sempre de onde a peça está)
  let cx = 800, cy = 450, curOp = 0, sp = { x: 0, y: 0, w: 0, h: 0, o: 0 }, capOp = 0, chipOp = 0, cardOp = 0, zs = 1, ztx = 0, zty = 0;
  const pCur = () => { cur.style.transform = `translate(${(cx - 4).toFixed(1)}px,${(cy - 2).toFixed(1)}px)`; cur.style.opacity = curOp; };
  const pSpot = () => { spot.style.left = sp.x + 'px'; spot.style.top = sp.y + 'px'; spot.style.width = sp.w + 'px'; spot.style.height = sp.h + 'px'; spot.style.opacity = sp.o; };
  const pZoom = () => { app.style.transform = zs === 1 && ztx === 0 && zty === 0 ? '' : `translate(${ztx.toFixed(2)}px,${zty.toFixed(2)}px) scale(${zs.toFixed(4)})`; };

  const q = (s) => (typeof s === 'string' ? document.querySelector(s) : s);
  const porTexto = (t) => [...document.querySelectorAll('h1,h2,h3,th,td,b,span,div')].find((e) => e.children.length < 3 && e.textContent.trim().startsWith(t));
  function uniao(a, b) { const l = Math.min(a.left, b.left), t = Math.min(a.top, b.top), r = Math.max(a.right, b.right), bt = Math.max(a.bottom, b.bottom); return { left: l, top: t, right: r, bottom: bt, width: r - l, height: bt - t }; }
  function caixa(r, pad) {
    const alvo = [r.left - pad, r.top - pad, r.width + 2 * pad, r.height + 2 * pad, 1];
    // holofote apagado: nasce um pouco maior no lugar novo; aceso: desliza do lugar antigo
    const de = sp.o < 0.05 ? [alvo[0] - 14, alvo[1] - 10, alvo[2] + 28, alvo[3] + 20, 0] : [sp.x, sp.y, sp.w, sp.h, sp.o];
    anima('spot', de, alvo, 600, (v) => { [sp.x, sp.y, sp.w, sp.h, sp.o] = v; pSpot(); });
    return true;
  }
  const LOGO = window.VT_LOGO || '';
  const CAPAS = Object.fromEntries(Object.entries(window.VT_CAPAS || {}).map(([k, v]) => [k, String(v).split('{{LOGO}}').join(LOGO)]));
  if (window.VT_CSS) { const s2 = document.createElement('style'); s2.textContent = window.VT_CSS; document.head.appendChild(s2); }
  // retângulo que cobre as colunas ini..fim (contando da 0) de todas as linhas de uma tabela
  function colunas(selTabela, ini, fim) {
    const t = q(selTabela); if (!t) return null;
    return [...t.rows].flatMap((r) => [...r.cells].slice(ini, fim + 1)).map((c) => c.getBoundingClientRect()).reduce((a, b) => uniao(a, b));
  }

  return {
    // avança o relógio; devolve quantas peças mexeram neste quadro (0 = quadro igual ao anterior)
    avancar(ms) {
      T += ms; let mexeu = 0;
      for (const [k, a] of [...tw]) {
        if (T < a.ini) continue;
        const p = Math.min(1, (T - a.ini) / a.dur);
        a.aplicar(mistura(a.de, a.para, suave(p))); mexeu++;
        if (p >= 1) { tw.delete(k); if (a.fim) a.fim(); }
      }
      return mexeu;
    },
    ativos() { return tw.size; },
    legenda(h) {
      if (!h) { anima('cap', [capOp, 0], [0, 10], 300, (v) => { capOp = v[0]; cap.style.opacity = v[0]; cap.style.transform = `translate(-50%,${v[1]}px)`; }); return; }
      cap.innerHTML = h; anima('cap', [0, 14], [1, 0], 420, (v) => { capOp = v[0]; cap.style.opacity = v[0]; cap.style.transform = `translate(-50%,${v[1]}px)`; });
    },
    legendaEm(lugar) { cap.classList.toggle('topo', lugar === 'topo'); },   // 'topo' ou 'base' (padrão): para não cobrir botão importante
    passo(t) {
      if (!t) { anima('chip', chipOp, 0, 300, (v) => { chipOp = v; chip.style.opacity = v; }); return; }
      if (chip.textContent === t && chipOp > 0.9) return;
      chip.textContent = t; anima('chip', 0, 1, 400, (v) => { chipOp = v; chip.style.opacity = v; });
    },
    destacar(s, pad) {
      const e = q(s); if (!e) { this.apagar(); return false; } return caixa(e.getBoundingClientRect(), pad === undefined ? 10 : pad);
    },
    destacarColunas(selTabela, ini, fim, pad) { const r = colunas(selTabela, ini, fim); return r ? caixa(r, pad === undefined ? 6 : pad) : false; },
    destacarFaixa(a, b, pad) { const ea = q(a), eb = q(b); if (!ea || !eb) return false; return caixa(uniao(ea.getBoundingClientRect(), eb.getBoundingClientRect()), pad || 10); },
    destacarTexto(t) { const e = porTexto(t); const s = e && e.closest('section'); if (!s) return false; const r = s.getBoundingClientRect();
      return caixa({ left: r.left, top: r.top, width: r.width, height: Math.min(r.height, innerHeight - r.top - 150) }, 6); },
    destacarFaixaTexto(t, linhas) { const e = porTexto(t); const s = e && e.closest('section'); if (!s) return false; const tr = s.querySelectorAll('tbody tr')[linhas - 1];
      return caixa(uniao(e.getBoundingClientRect(), (tr || s).getBoundingClientRect()), 10); },
    apagar() { if (sp.o > 0) anima('spot', [sp.x, sp.y, sp.w, sp.h, sp.o], [sp.x, sp.y, sp.w, sp.h, 0], 350, (v) => { [sp.x, sp.y, sp.w, sp.h, sp.o] = v; pSpot(); }); },
    cursor(x, y) {
      if (curOp < 0.05) { cx = x + 60; cy = y + 50; }
      anima('cur', [cx, cy, curOp], [x, y, 1], 900, (v) => { [cx, cy, curOp] = v; pCur(); }); return [x, y];
    },
    cursorEm(s, dx, dy) { const e = q(s); if (!e) return null; const r = e.getBoundingClientRect(); return this.cursor(r.left + r.width * (dx === undefined ? 0.5 : dx), r.top + r.height * (dy === undefined ? 0.5 : dy)); },
    cursorEmTexto(t) { const e = porTexto(t); return e ? this.cursorEm(e) : null; },
    cursorFora() { anima('cur', [cx, cy, curOp], [cx, cy, 0], 300, (v) => { [cx, cy, curOp] = v; pCur(); }); },
    alvoCursor() { const a = tw.get('cur'); return a ? [a.para[0], a.para[1]] : [cx, cy]; },
    clique() {
      const r = el('vt-rip'), x = this.alvoCursor();
      r.style.left = x[0] + 'px'; r.style.top = x[1] + 'px';
      anima('rip' + T, [0.4, 1], [3.2, 0], 700, (v) => { r.style.transform = `scale(${v[0]})`; r.style.opacity = v[1]; }, 0, () => r.remove());
    },
    capa(nome) {
      card.innerHTML = CAPAS[nome] || '';
      anima('card', cardOp, 1, 600, (v) => { cardOp = v; card.style.opacity = v; });
      // entrada em cascata dos textos da capa (logo, título, linha)
      [...card.querySelectorAll('.vt-capa > *')].forEach((e, i) => {
        e.style.opacity = 0;
        const linha = e.classList.contains('linha');
        anima('capa' + i, [0, 22], [1, 0], 750, (v) => { e.style.opacity = v[0]; e.style.transform = linha ? `scaleX(${v[0]})` : `translateY(${v[1]}px)`; }, 250 + i * 160);
      });
    },
    semCapa() { anima('card', cardOp, 0, 550, (v) => { cardOp = v; card.style.opacity = v; }); },
    // câmera: aproxima um ponto (transform na .app); legenda, cursor e holofote ficam por cima, sem zoom
    zoom(s, maxS) {
      const e = q(s); if (!e) return false;
      const r = e.getBoundingClientRect(), W = innerWidth, H = innerHeight;
      const lx = (r.left - ztx) / zs, ly = (r.top + scrollY - zty) / zs, lw = r.width / zs, lh = r.height / zs;
      const S = Math.max(1, Math.min(maxS || 1.4, (W * 0.84) / lw, (H * 0.6) / lh));
      if (S < 1.06) {   // bloco grande demais para aproximar: só rola até ele (o menu não sai do lugar)
        this.zoom0(); const topo = Math.max(0, (r.top + scrollY - zty) / zs - Math.max(70, H * 0.43 - lh / 2)); this.rolarPara(topo); return 1;
      }
      let tx = W / 2 - S * (lx + lw / 2), ty = H * 0.43 + scrollY - S * (ly + lh / 2);
      tx = Math.min(0, Math.max(W - S * W, tx)); ty = Math.min(scrollY, ty);
      anima('zoom', [zs, ztx, zty], [S, tx, ty], 1100, (v) => { [zs, ztx, zty] = v; pZoom(); });
      return S;
    },
    zoom0() { if (zs === 1 && ztx === 0 && zty === 0 && !tw.has('zoom')) return false; anima('zoom', [zs, ztx, zty], [1, 0, 0], 900, (v) => { [zs, ztx, zty] = v; pZoom(); }); return true; },
    rolarPara(y) {
      y = Math.max(0, Math.min(y, document.documentElement.scrollHeight - innerHeight));
      if (Math.abs(y - scrollY) < 2) return false;
      anima('rolar', scrollY, y, 1100, (v) => window.scrollTo(0, v)); return true;
    },
    rolar(s, margem) { const e = q(s); if (!e) return false; return this.rolarPara(e.getBoundingClientRect().top + scrollY - (margem || 90)); },
    rolarTexto(t, margem) { const e = porTexto(t); return e ? this.rolar(e, margem) : false; },
    topo() { return this.rolarPara(0); },
    // rola um painel que tem rolagem própria (não a página) até o elemento ficar perto do topo dele
    rolarDentro(s, margem) {
      const e = q(s); if (!e) return false;
      let c = e.parentElement;
      while (c && c !== document.body) { const st = getComputedStyle(c); if (/(auto|scroll)/.test(st.overflowY) && c.scrollHeight > c.clientHeight + 4) break; c = c.parentElement; }
      if (!c || c === document.body) return this.rolar(s, margem);
      const alvo = Math.max(0, Math.min(c.scrollTop + e.getBoundingClientRect().top - c.getBoundingClientRect().top - (margem || 12), c.scrollHeight - c.clientHeight));
      if (Math.abs(alvo - c.scrollTop) < 2) return false;
      anima('rolarD', c.scrollTop, alvo, 1000, (v) => { c.scrollTop = v; }); return true;
    },
    // ponto em % da tela SEM zoom (como nos prints do tutorial) → ponto na tela de agora (com o zoom aplicado)
    pontoPct(xp, yp) { return [ztx + zs * (innerWidth * xp / 100), zty + zs * (innerHeight * yp / 100) - scrollY]; },
    cursorPct(xp, yp) { const [x, y] = this.pontoPct(xp, yp); return this.cursor(x, y); },
    // bloco da página que está no ponto (em % da tela sem zoom): sobe dos elementos pequenos até um cartão/painel de tamanho legível
    alvoPct(xp, yp) {
      const [x, y] = this.pontoPct(xp, yp);
      if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) return null;
      const nosso = (e) => typeof e.className === 'string' && /(^|\s)vt-/.test(e.className);
      let e = document.elementsFromPoint(x, y).find((k) => !nosso(k)); if (!e) return null;
      const A = innerWidth * innerHeight;
      while (e.parentElement && e.parentElement !== document.body) {
        const r = e.getBoundingClientRect();
        if (r.width * r.height >= A * 0.012 * zs * zs && r.width >= 110 * zs && r.height >= 38 * zs) break;
        e = e.parentElement;
      }
      const r = e.getBoundingClientRect();
      if (r.width * r.height > A * 0.55 * zs * zs) return null;   // grande demais (quase a tela toda): sem destaque
      const id = 'a' + (++nAlvo); e.setAttribute('data-vt-alvo', id); return `[data-vt-alvo="${id}"]`;
    },
    // marca invisível dentro da raiz do zoom, cobrindo um retângulo da tela SEM zoom: vira alvo de foco e destaque (o gravador tira o zoom antes)
    marcarRet(l, t, w, h) {
      const m = document.createElement('div'), id = 'm' + (++nAlvo); m.setAttribute('data-vt-alvo', id);
      if (getComputedStyle(app).position === 'static') app.style.position = 'relative';
      const rb = app.getBoundingClientRect();
      m.style.cssText = `position:absolute;left:${l - rb.left}px;top:${t - rb.top}px;width:${w}px;height:${h}px;pointer-events:none;visibility:hidden`;
      app.appendChild(m); return `[data-vt-alvo="${id}"]`;
    },
    marcarFaixa(a, b) { const ea = q(a), eb = q(b); if (!ea || !eb) return null; const r = uniao(ea.getBoundingClientRect(), eb.getBoundingClientRect()); return this.marcarRet(r.left, r.top, r.width, r.height); },
    marcarRetPct(xp, yp, wp, hp) { return this.marcarRet(innerWidth * xp / 100, innerHeight * yp / 100, innerWidth * wp / 100, innerHeight * hp / 100); },
    // retângulo em % da tela (para capas feitas de imagem)
    destacarRetPct(xp, yp, wp, hp, pad) { return caixa({ left: innerWidth * xp / 100, top: innerHeight * yp / 100, width: innerWidth * wp / 100, height: innerHeight * hp / 100 }, pad === undefined ? 8 : pad); },
    faixa(prefixo) { const p = [...document.querySelectorAll('svg [data-tip]')].find((x) => x.getAttribute('data-tip').startsWith(prefixo)); if (!p) return null;
      const r = p.getBoundingClientRect(); return [r.left + r.width * 0.55, r.top + r.height * 0.5]; },
  };
})();
