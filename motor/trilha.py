# Trilha e efeitos sonoros sintetizados na própria máquina (sem direito autoral, sem internet), para os vídeos animados (motor/animar.py).
#   musica(duracao, arq)          base suave: acordes longos (Dó, Sol, Lá menor, Fá) + notas dedilhadas tipo marimba, estéreo 48 kHz
#   efeitos(eventos, duracao, arq) sons curtos nos instantes que a página pediu: whoosh, pop, plim, splash, bolha
# A música sai com volume baixo e fixo; quem abaixa a música quando a voz fala é o ffmpeg (sidechaincompress no animar.py).
import wave

import numpy as np

TAXA = 48000
RNG = np.random.default_rng(7)


def _grava(arq, est):
    x = (np.clip(est, -1, 1) * 32767).astype("<i2")
    with wave.open(str(arq), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(TAXA); w.writeframes(x.tobytes())


def _hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _somar(buf, ini, sinal, pan=0.0):
    """Soma um sinal mono no buffer estéreo a partir do segundo `ini`, com pan de -1 (esquerda) a 1 (direita)."""
    i = int(ini * TAXA)
    if i >= len(buf):
        return
    s = sinal[: len(buf) - i]
    buf[i:i + len(s), 0] += s * np.sqrt((1 - pan) / 2) * 1.414
    buf[i:i + len(s), 1] += s * np.sqrt((1 + pan) / 2) * 1.414


# ------------------------------------------------------------------ música
ACORDES = [  # (baixo, notas do acorde) em MIDI: Cmaj7, G, Am7, Fmaj7 (I V vi IV)
    (48, [64, 67, 71]), (43, [62, 67, 71]), (45, [64, 67, 72]), (41, [64, 69, 72]),
]
BPM = 100
RITMO = [1, 0, 1, 1, 0, 1, 0, 1]   # colcheias tocadas (1) e pausas (0) em cada compasso


def musica(duracao, arq, alvo_rms_db=-27.0):
    n = int(duracao * TAXA) + TAXA
    buf = np.zeros((n, 2))
    batida = 60 / BPM
    compasso = 4 * batida
    t = 0.0; k = 0
    while t < duracao + compasso:
        baixo, notas = ACORDES[k % len(ACORDES)]
        dur = compasso + 1.0                                      # o som do acorde invade um pouco o próximo
        tt = np.arange(int(dur * TAXA)) / TAXA
        env = np.minimum(1, tt / 0.6) * np.minimum(1, np.maximum(0, (dur - tt) / 1.0))
        for j, m in enumerate(notas):                              # pad: senoide + um pouco do 2º harmônico, levemente desafinada nos dois lados
            f = _hz(m)
            for lado, desaf in ((-0.5, 0.9988), (0.5, 1.0012)):
                s = (np.sin(2 * np.pi * f * desaf * tt) + 0.12 * np.sin(4 * np.pi * f * desaf * tt)) * env * 0.05
                _somar(buf, t, s, lado * (0.4 + 0.2 * j / 3))
        fb = _hz(baixo)                                            # baixo macio
        envb = np.minimum(1, tt / 0.05) * (0.55 + 0.45 * np.exp(-tt / 0.8)) * np.minimum(1, np.maximum(0, (dur - tt) / 1.0))
        _somar(buf, t, (np.sin(2 * np.pi * fb * tt) + 0.25 * np.sin(4 * np.pi * fb * tt)) * envb * 0.09)
        if t >= 2 * compasso:                                      # dedilhado entra depois de 2 compassos
            arpejo = [m + 12 for m in notas] + [notas[0] + 24]
            for c in range(8):
                if not RITMO[c]:
                    continue
                m = arpejo[(c + k) % len(arpejo)]
                f = _hz(m); dn = 0.9
                tn = np.arange(int(dn * TAXA)) / TAXA
                s = (np.sin(2 * np.pi * f * tn) * np.exp(-tn / 0.28) + 0.35 * np.sin(4 * np.pi * f * tn) * np.exp(-tn / 0.07))
                s *= np.minimum(1, tn / 0.004) * 0.06
                _somar(buf, t + c * batida / 2, s, 0.35 if c % 2 else -0.35)
        t += compasso; k += 1
    buf = buf[: int(duracao * TAXA)]
    rms = np.sqrt(np.mean(buf ** 2)) + 1e-9
    buf *= 10 ** (alvo_rms_db / 20) / rms
    ent, sai = int(1.2 * TAXA), int(2.5 * TAXA)                  # entra e sai suave
    buf[:ent] *= np.linspace(0, 1, ent)[:, None]
    buf[-sai:] *= np.linspace(1, 0, sai)[:, None] ** 1.5
    _grava(arq, buf)


# ------------------------------------------------------------------ batida (propaganda, Reels de venda)
def _ruido_filtrado(dur, corte_baixo=None, corte_alto=None, seed=0):
    r = np.random.default_rng(seed).standard_normal(int(dur * TAXA))
    if corte_alto:
        r = _passa_baixa(r, corte_alto)
    if corte_baixo:
        r = r - _passa_baixa(r, corte_baixo)
    return r


def _serra(f, tn, harm=6):
    return sum(np.sin(2 * np.pi * f * h * tn) / h for h in range(1, harm + 1))


def batida(duracao, arq, bpm=118, alvo_rms_db=-23.0):
    """Batida eletrônica animada: bumbo 4 por compasso, palma no 2 e no 4, chimbal em colcheias, baixo e acordes curtos (Lá menor, Fá, Dó, Sol)."""
    n = int(duracao * TAXA) + TAXA
    buf = np.zeros((n, 2))
    b = 60 / bpm
    tk = np.arange(int(0.4 * TAXA)) / TAXA                                    # bumbo: senoide que cai de tom
    bumbo = np.sin(2 * np.pi * np.cumsum(48 + 120 * np.exp(-tk / 0.03)) / TAXA) * np.exp(-tk / 0.22)
    bumbo[:96] += np.random.default_rng(1).standard_normal(96) * 0.3 * np.linspace(1, 0, 96)
    tp = np.arange(int(0.22 * TAXA)) / TAXA                                   # palma: três estalos de ruído
    base = _ruido_filtrado(0.22, 700, 4000, 2)
    palma = np.zeros_like(tp)
    for k, atraso in enumerate((0, 0.011, 0.022)):
        i = int(atraso * TAXA); palma[i:] += base[: len(palma) - i] * np.exp(-tp[: len(palma) - i] / (0.018 if k < 2 else 0.1))
    chimbal = [_ruido_filtrado(0.06, 6500, None, 10 + s) * np.exp(-np.arange(int(0.06 * TAXA)) / TAXA / 0.018) for s in range(3)]
    acordes = [(57, [69, 72, 76]), (53, [69, 72, 77]), (48, [67, 72, 76]), (55, [67, 71, 74])]   # Am F C G
    t = 0.0; compasso = 0
    while t < duracao + 4 * b:
        raiz, notas = acordes[(compasso // 2) % 4]
        for batida_i in range(4):
            tb = t + batida_i * b
            _somar(buf, tb, bumbo * 0.55)
            if batida_i in (1, 3):
                _somar(buf, tb, palma * 0.22, 0.1)
            for c in range(2):                                                   # chimbal em colcheias (o do contratempo mais forte)
                _somar(buf, tb + c * b / 2, chimbal[(batida_i + c) % 3] * (0.07 if c == 0 else 0.11), 0.3)
            tn = np.arange(int(b / 2 * TAXA)) / TAXA                            # baixo em colcheias, entra depois do bumbo
            for c in range(2):
                fb = _hz(raiz - 24 + (12 if c == 1 and batida_i == 3 else 0))
                env = np.minimum(1, tn / 0.01) * np.exp(-tn / 0.16) * np.minimum(1, (b / 2 - tn) / 0.01)
                _somar(buf, tb + c * b / 2 + 0.01, _serra(fb, tn, 4) * env * 0.16)
            if batida_i in (1, 3):                                               # acorde curto no contratempo
                td = np.arange(int(0.3 * TAXA)) / TAXA
                env = np.minimum(1, td / 0.005) * np.exp(-td / 0.11)
                for j, m in enumerate(notas):
                    _somar(buf, tb + b / 2, _serra(_hz(m), td, 5) * env * 0.035, (-0.4, 0, 0.4)[j])
        t += 4 * b; compasso += 1
    buf = buf[: int(duracao * TAXA)]
    rms = np.sqrt(np.mean(buf ** 2)) + 1e-9
    buf *= 10 ** (alvo_rms_db / 20) / rms
    ent, sai = int(0.15 * TAXA), int(1.8 * TAXA)
    buf[:ent] *= np.linspace(0, 1, ent)[:, None]
    buf[-sai:] *= np.linspace(1, 0, sai)[:, None] ** 1.5
    _grava(arq, buf)


# ------------------------------------------------------------------ lo-fi (explicativo premium, como as referências de 21/11/2026)
def _piano_eletrico(f, dur, vel=1.0):
    """Timbre de piano elétrico: fundamental + harmônicos que somem rápido + tremolo leve."""
    tn = np.arange(int(dur * TAXA)) / TAXA
    s = (np.sin(2 * np.pi * f * tn) + 0.45 * np.sin(4 * np.pi * f * tn) * np.exp(-tn / 0.25)
         + 0.12 * np.sin(6 * np.pi * f * tn) * np.exp(-tn / 0.12) + 0.05 * np.sin(2 * np.pi * 7.1 * f * tn) * np.exp(-tn / 0.03))
    env = np.minimum(1, tn / 0.006) * np.exp(-tn / 1.6) * np.minimum(1, (dur - tn) / 0.25)
    return s * env * (1 + 0.12 * np.sin(2 * np.pi * 4.6 * tn)) * vel


def lofi(duracao, arq, bpm=92, alvo_rms_db=-21.0):
    """Lo-fi suave: bumbo macio no 1 e no 3, estalo no 2 e no 4, chimbal com balanço, piano elétrico em acordes de sétima e baixo."""
    n = int(duracao * TAXA) + 2 * TAXA
    buf = np.zeros((n, 2))
    b = 60 / bpm
    balanco = 0.12 * b                                                        # contratempo atrasado (swing)
    tk = np.arange(int(0.45 * TAXA)) / TAXA
    bumbo = np.sin(2 * np.pi * np.cumsum(52 + 70 * np.exp(-tk / 0.04)) / TAXA) * np.exp(-tk / 0.22)
    te = np.arange(int(0.12 * TAXA)) / TAXA
    estalo = _ruido_filtrado(0.12, 900, 3500, 21) * np.exp(-te / 0.035) * 0.8 + np.sin(2 * np.pi * 820 * te) * np.exp(-te / 0.02) * 0.4
    chimbal = [_ruido_filtrado(0.05, 7000, None, 30 + s) * np.exp(-np.arange(int(0.05 * TAXA)) / TAXA / 0.015) for s in range(3)]
    # Fmaj7, Em7, Dm7, Cmaj7 (voz do meio, longe da região da narração)
    acordes = [(41, [57, 60, 64, 67]), (40, [55, 59, 62, 67]), (38, [57, 60, 62, 65]), (36, [55, 59, 64, 67])]
    t = 0.0; k = 0
    while t < duracao + 4 * b:
        raiz, notas = acordes[k % 4]
        for i, m in enumerate(notas):                                         # acorde no 1 (dedilhado rápido) e de novo no "e" do 3
            _somar(buf, t + i * 0.012, _piano_eletrico(_hz(m), 4 * b + 0.6, 0.075), (-0.25, -0.08, 0.08, 0.25)[i])
            _somar(buf, t + 2.5 * b + balanco + i * 0.01, _piano_eletrico(_hz(m + 12 if i == 3 else m), 1.6 * b, 0.035), (-0.3, 0.3)[i % 2])
        for bi in range(4):
            tb = t + bi * b
            if bi in (0, 2):
                _somar(buf, tb, bumbo * 0.5)
            if bi in (1, 3):
                _somar(buf, tb, estalo * 0.16, 0.12)
            _somar(buf, tb, chimbal[bi % 3] * 0.035, 0.35)
            _somar(buf, tb + b / 2 + balanco, chimbal[(bi + 1) % 3] * 0.05, 0.35)
        tn = np.arange(int(1.4 * b * TAXA)) / TAXA                            # baixo: no 1 e no "e" do 2
        for ini in (0, 1.5 * b + balanco):
            env = np.minimum(1, tn / 0.01) * np.exp(-tn / 0.5) * np.minimum(1, (1.4 * b - tn) / 0.05)
            _somar(buf, t + ini, (np.sin(2 * np.pi * _hz(raiz) * tn) + 0.2 * np.sin(4 * np.pi * _hz(raiz) * tn)) * env * 0.22)
        t += 4 * b; k += 1
    buf = buf[: int(duracao * TAXA)]
    rms = np.sqrt(np.mean(buf ** 2)) + 1e-9
    buf *= 10 ** (alvo_rms_db / 20) / rms
    ent, sai = int(0.4 * TAXA), int(2.2 * TAXA)
    buf[:ent] *= np.linspace(0, 1, ent)[:, None]
    buf[-sai:] *= np.linspace(1, 0, sai)[:, None] ** 1.5
    _grava(arq, buf)


# ------------------------------------------------------------------ efeitos
def _passa_baixa(x, fc):
    """Filtro de um polo com corte variável (fc pode ser um vetor do mesmo tamanho de x). Só para sons curtos."""
    fc = np.broadcast_to(fc, x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / TAXA)
    y = np.empty_like(x); v = 0.0
    for i in range(len(x)):
        v += a[i] * (x[i] - v); y[i] = v
    return y


def _whoosh(dur=0.6):
    n = int(dur * TAXA); u = np.linspace(0, 1, n)
    ruido = RNG.standard_normal(n)
    corte = 250 + 3200 * np.sin(np.pi * u) ** 2
    s = _passa_baixa(ruido, corte) - _passa_baixa(ruido, 120)
    return s * np.sin(np.pi * u) ** 2 * 0.22


def _pop():
    tn = np.arange(int(0.16 * TAXA)) / TAXA
    f = 300 + 600 * np.exp(-tn / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / TAXA) * np.exp(-tn / 0.05) * np.minimum(1, tn / 0.002) * 0.3


def _bolha():
    tn = np.arange(int(0.2 * TAXA)) / TAXA
    f = 280 + 520 * (1 - np.exp(-tn / 0.06))
    return np.sin(2 * np.pi * np.cumsum(f) / TAXA) * np.exp(-tn / 0.07) * np.minimum(1, tn / 0.003) * 0.3


def _plim(midi=84):
    f = _hz(midi); tn = np.arange(int(0.9 * TAXA)) / TAXA
    s = np.sin(2 * np.pi * f * tn) + 0.3 * np.sin(4 * np.pi * f * tn) * np.exp(-tn / 0.15) + 0.1 * np.sin(6 * np.pi * f * tn) * np.exp(-tn / 0.08)
    return s * np.exp(-tn / 0.35) * np.minimum(1, tn / 0.003) * 0.16


def _splash():
    n = int(0.45 * TAXA); tn = np.arange(n) / TAXA
    ruido = _passa_baixa(RNG.standard_normal(n), 2600) * np.exp(-tn / 0.12) * 0.5
    return ruido + np.concatenate([_bolha(), np.zeros(n - int(0.2 * TAXA))]) * 0.7


def _kaching():                                   # caixa registradora: sino metálico + moedas
    tn = np.arange(int(0.9 * TAXA)) / TAXA
    sino = sum(a * np.sin(2 * np.pi * f * tn) * np.exp(-tn / d) for f, a, d in ((2093, 1, 0.45), (2637, 0.7, 0.35), (3520, 0.45, 0.25), (4186, 0.3, 0.2)))
    moedas = _ruido_filtrado(0.9, 3000, None, 5) * np.exp(-tn / 0.05) * 0.4
    s = (sino * 0.25 + moedas) * np.minimum(1, tn / 0.002)
    s2 = np.zeros_like(s); i = int(0.07 * TAXA); s2[i:] = s[:-i] * 0.8                # "ka" ... "ching"
    return (s * 0.5 + s2) * 0.32


def _carimbo():                                   # pancada surda (carimbo, martelo, placa)
    tn = np.arange(int(0.35 * TAXA)) / TAXA
    corpo = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tn / 0.025)) / TAXA) * np.exp(-tn / 0.12)
    estalo = _ruido_filtrado(0.35, None, 1800, 6) * np.exp(-tn / 0.02)
    return (corpo + estalo * 0.6) * 0.5


def _vidro():                                     # vidro quebrando: estalos agudos espalhados
    n = int(0.7 * TAXA); tn = np.arange(n) / TAXA; s = np.zeros(n)
    r = np.random.default_rng(8)
    base = _ruido_filtrado(0.7, 2500, None, 9)
    s += base * np.exp(-tn / 0.08) * 0.6
    for _ in range(14):
        t0 = r.uniform(0, 0.35); f = r.uniform(2500, 6500); i = int(t0 * TAXA); m = n - i
        s[i:] += np.sin(2 * np.pi * f * tn[:m]) * np.exp(-tn[:m] / r.uniform(0.02, 0.08)) * r.uniform(0.15, 0.35)
    return s * 0.35


def _subida(dur=1.2):                             # sobe antes da chamada final
    n = int(dur * TAXA); u = np.linspace(0, 1, n)
    ruido = _passa_baixa(RNG.standard_normal(n), 300 + 6000 * u ** 2)
    tom = np.sin(2 * np.pi * np.cumsum(200 + 700 * u ** 2) / TAXA) * 0.3
    return (ruido * 0.6 + tom) * u ** 2 * 0.3


def _tique():                                     # toque de interface (cartão/linha aparecendo)
    tn = np.arange(int(0.06 * TAXA)) / TAXA
    return (np.sin(2 * np.pi * 1850 * tn) * np.exp(-tn / 0.012) + _ruido_filtrado(0.06, 3000, None, 41) * np.exp(-tn / 0.004) * 0.5) * 0.22


def _notificacao():                               # notificação de celular: dois tons
    tn = np.arange(int(0.7 * TAXA)) / TAXA
    s = np.zeros_like(tn)
    for ini, f in ((0.0, 1318.5), (0.11, 1760.0)):
        i = int(ini * TAXA); m = len(tn) - i
        s[i:] += (np.sin(2 * np.pi * f * tn[:m]) + 0.25 * np.sin(4 * np.pi * f * tn[:m]) * np.exp(-tn[:m] / 0.08)) * np.exp(-tn[:m] / 0.22)
    return s * np.minimum(1, tn / 0.003) * 0.17


def _risco():                                     # caneta riscando
    n = int(0.28 * TAXA); u = np.linspace(0, 1, n)
    r = _ruido_filtrado(0.28, 1500, 6000, 52)
    return r * np.sin(np.pi * u) ** 0.6 * (0.7 + 0.3 * np.sin(2 * np.pi * 38 * u * 0.28)) * 0.22


def _roleta(dur=0.9):                             # números rolando: tiques cada vez mais espaçados
    n = int(dur * TAXA); s = np.zeros(n); t = 0.0; passo = 0.035
    tq = _tique()
    while t < dur - 0.06:
        i = int(t * TAXA); m = min(len(tq), n - i); s[i:i + m] += tq[:m] * 0.8
        t += passo; passo *= 1.09
    return s


def _chiado(dur=4.0):                            # carne chiando na brasa: chiado agudo + estalos
    n = int(dur * TAXA); tn = np.arange(n) / TAXA
    r = np.random.default_rng(71)
    s = _ruido_filtrado(dur, 2200, 9000, 72) * (0.55 + 0.25 * np.sin(2 * np.pi * 0.7 * tn) + 0.2 * np.sin(2 * np.pi * 1.9 * tn + 1))
    for _ in range(int(dur * 38)):                                            # estalos curtos espalhados
        i = int(r.uniform(0, dur - 0.02) * TAXA); m = int(r.uniform(0.002, 0.012) * TAXA)
        s[i:i + m] += r.standard_normal(m) * np.exp(-np.arange(m) / (m / 4)) * r.uniform(0.6, 2.2)
    env = np.minimum(1, tn / 0.35) * np.minimum(1, (dur - tn) / 0.6)
    return s * env * 0.09


def _chama():                                     # labareda subindo (whoosh grave)
    n = int(0.8 * TAXA); u = np.linspace(0, 1, n)
    s = _passa_baixa(RNG.standard_normal(n), 150 + 1400 * np.sin(np.pi * u) ** 2) * np.sin(np.pi * u) ** 1.5
    return s * 0.35


SONS = {"whoosh": _whoosh, "pop": _pop, "bolha": _bolha, "plim": _plim, "splash": _splash, "kaching": _kaching, "carimbo": _carimbo,
        "vidro": _vidro, "subida": _subida, "tique": _tique, "notificacao": _notificacao, "risco": _risco, "roleta": _roleta,
        "chiado": _chiado, "chama": _chama}


def efeitos(eventos, duracao, arq):
    """eventos = [{"t": s, "som": "whoosh"|"pop"|"bolha"|"plim"|"splash", "vol": 1, "nota": 84, "dur": 0.6, "pan": 0}]"""
    buf = np.zeros((int(duracao * TAXA) + TAXA, 2))
    for e in eventos:
        som = e.get("som")
        if som not in SONS:
            continue
        if som == "plim":
            s = _plim(e.get("nota", 84))
        elif som == "whoosh":
            s = _whoosh(e.get("dur", 0.6))
        elif som == "subida":
            s = _subida(e.get("dur", 1.2))
        elif som == "roleta":
            s = _roleta(e.get("dur", 0.9))
        elif som == "chiado":
            s = _chiado(e.get("dur", 4.0))
        else:
            s = SONS[som]()
        _somar(buf, max(0.0, e["t"]), s * e.get("vol", 1.0), e.get("pan", 0.0))
    _grava(arq, buf[: int(duracao * TAXA)])
