# Vozes do Gerador de Vídeos: transforma cada fala do roteiro num WAV (mono, 44,1 kHz), com o motor escolhido.
#   edge        vozes neurais da Microsoft pelo leitor do Edge (biblioteca edge-tts). Grátis, sem chave. Melhores em pt-BR:
#               pt-BR-AntonioNeural (masc.), pt-BR-FranciscaNeural e pt-BR-ThalitaMultilingualNeural (fem.). Serviço não oficial.
#   elevenlabs  ElevenLabs (chave em %USERPROFILE%\.secrets\elevenlabs\.env, linha ELEVENLABS_API_KEY=...). Na conta gratuita só as
#               vozes padrão funcionam pela API; vozes da biblioteca (as brasileiras) pedem plano pago.
#   windows     vozes do próprio Windows (Microsoft Maria/Daniel). Sem internet, mas robóticas: só para rascunho.
# O que vai para fora (edge e elevenlabs) é só o texto das falas. Nunca ponha dado de cliente no texto da fala.
#
# Linha de comando:
#   py motor/vozes.py listar edge                       vozes do Edge em pt-BR e as multilíngues
#   py motor/vozes.py listar elevenlabs                 vozes da sua conta ElevenLabs
#   py motor/vozes.py biblioteca                        vozes masculinas e femininas do português do Brasil na biblioteca do ElevenLabs (só lista)
#   py motor/vozes.py amostra edge pt-BR-FranciscaNeural "Texto de teste" saida.mp3
#   py motor/vozes.py amostras "Texto de teste" pasta   uma amostra de cada voz do CATALOGO (abaixo), para comparar
#   py motor/vozes.py desenhar "descrição da voz" "texto" pasta   3 prévias de voz sob medida (ElevenLabs; a chave precisa da permissão voice_generation)
#
# Respiro (20/11/2026, feedback do Gabriel: "acelera muito, parece que não tem vírgula e não respira, fica na cara que é IA"):
#   no Edge, cada fala é gerada FRASE POR FRASE (quebra em . ! ? e no marcador |), o silêncio das pontas é aparado e as frases são
#   coladas com uma pausa fixa (voz["respiro"] em ms; padrão 320; 0 = fala inteira de uma vez, como antes).
#   Junto do <id>.wav sai <id>.palavras.json com o tempo de cada palavra (legenda animada do vídeo animado, motor/animar.py).
import array, asyncio, json, re, subprocess, sys, urllib.error, urllib.request, wave
from pathlib import Path

MOTOR = Path(__file__).resolve().parent
if (MOTOR / "pylib").exists():                 # cópia local do edge-tts (Python 3.14); em outra máquina: py -m pip install -r requirements.txt
    sys.path.insert(0, str(MOTOR / "pylib"))
CHAVE_ELEVEN = Path.home() / ".secrets" / "elevenlabs" / ".env"
# vozes aprovadas pelo Gabriel em 19/11/2026 (arquivo da amostra, motor, voz, ajustes); ver vozes/CATALOGO.md
CATALOGO = [
    ("Masculina 1 - Antonio (nativo do Brasil)", "edge", "pt-BR-AntonioNeural", {"ritmo": "-3%", "tom": "-2Hz"}),
    ("Masculina 2 - William (multilingue)", "edge", "en-AU-WilliamMultilingualNeural", {}),
    ("Masculina 3 - Brian (multilingue)", "edge", "en-US-BrianMultilingualNeural", {}),
    ("Feminina 1 - Francisca (nativa do Brasil)", "edge", "pt-BR-FranciscaNeural", {}),
    ("Feminina 2 - Thalita (nativa do Brasil)", "edge", "pt-BR-ThalitaMultilingualNeural", {}),
    ("Feminina 3 - Ava (multilingue)", "edge", "en-US-AvaMultilingualNeural", {}),
    ("Feminina 4 - Emma (multilingue)", "edge", "en-US-EmmaMultilingualNeural", {}),
    ("Feminina 5 - Matilda (ElevenLabs)", "elevenlabs", "XrExE9yKIg1WjnnlVkGX", {}),
    ("Feminina 6 - Sarah (ElevenLabs)", "elevenlabs", "EXAVITQu4vr4xnSDxMaL", {}),
]


def duracao(wav: Path) -> float:
    with wave.open(str(wav)) as w:
        return w.getnframes() / w.getframerate()


def para_wav(origem: Path, destino: Path):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(origem), "-ac", "1", "-ar", "44100", "-sample_fmt", "s16", str(destino)], check=True)


# ---------------------------------------------------------------- Edge
async def _edge(texto, voz, arq, ritmo=None, tom=None, palavras=None):
    """Grava o mp3; se vier a lista `palavras`, acrescenta nela {"t": início em s, "d": duração em s, "w": palavra}."""
    import edge_tts
    extra = {k: v for k, v in (("rate", ritmo), ("pitch", tom)) if v}
    if palavras is None:
        await edge_tts.Communicate(texto, voz, **extra).save(str(arq))
        return
    com = edge_tts.Communicate(texto, voz, boundary="WordBoundary", **extra)
    with open(arq, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                palavras.append({"t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7, "w": ch["text"]})


def frases(texto: str) -> list:
    """Quebra a fala em frases (depois de . ! ? …) e no marcador | (pausa sem pontuação)."""
    return [p.strip() for p in re.split(r"(?<=[.!?…])\s+|\s*\|\s*", texto.strip()) if p.strip()]


def _ler_wav(arq: Path):
    with wave.open(str(arq)) as w:
        return w.getframerate(), array.array("h", w.readframes(w.getnframes()))


def _aparar(am, taxa, limiar=350, folga_ini=0.02, folga_fim=0.07):
    """Tira o silêncio das pontas de um trecho (int16 mono). Devolve (amostras, segundos tirados do começo)."""
    i, j = 0, len(am) - 1
    while i < j and abs(am[i]) < limiar:
        i += 1
    while j > i and abs(am[j]) < limiar:
        j -= 1
    i = max(0, i - int(folga_ini * taxa)); j = min(len(am) - 1, j + int(folga_fim * taxa))
    return am[i:j + 1], i / taxa


def _edge_com_respiro(fala: dict, voz: dict, pasta: Path, pausa_ms: int):
    """Gera a fala frase por frase, apara as pontas e cola com pausa fixa. Grava <id>.wav e <id>.palavras.json."""
    taxa, total, palavras, pos = 44100, array.array("h"), [], 0.0
    pedacos = frases(fala["fala"])
    for k, frase in enumerate(pedacos):
        mp3, wv, pal = pasta / f"_{fala['id']}_{k}.mp3", pasta / f"_{fala['id']}_{k}.wav", []
        asyncio.run(_edge(frase, voz["nome"], mp3, voz.get("ritmo"), voz.get("tom"), pal))
        para_wav(mp3, wv)
        taxa, am = _ler_wav(wv)
        am, cortado = _aparar(am, taxa)
        if k:                                          # o respiro entre uma frase e a outra
            total.extend([0] * int(pausa_ms / 1000 * taxa)); pos += pausa_ms / 1000
        for p in pal:
            palavras.append({"t": round(pos + max(0.0, p["t"] - cortado), 3), "d": round(p["d"], 3), "w": p["w"]})
        total.extend(am); pos += len(am) / taxa
        mp3.unlink(missing_ok=True); wv.unlink(missing_ok=True)
    total.extend([0] * int(0.05 * taxa))
    with wave.open(str(pasta / f"{fala['id']}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(total.tobytes())
    (pasta / f"{fala['id']}.palavras.json").write_text(json.dumps(palavras, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- ElevenLabs
def _chave_eleven() -> str:
    if not CHAVE_ELEVEN.exists():
        raise SystemExit(f"Falta a chave do ElevenLabs: crie {CHAVE_ELEVEN} com a linha ELEVENLABS_API_KEY=sua_chave")
    for linha in CHAVE_ELEVEN.read_text(encoding="utf-8-sig").splitlines():
        if linha.strip().startswith("ELEVENLABS_API_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{CHAVE_ELEVEN} não tem a linha ELEVENLABS_API_KEY=...")


def _api_eleven(metodo, caminho, corpo=None):
    req = urllib.request.Request("https://api.elevenlabs.io" + caminho, method=metodo, data=json.dumps(corpo).encode("utf-8") if corpo is not None else None,
                                 headers={"xi-api-key": _chave_eleven(), "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs respondeu {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")


def _eleven(texto, voz, arq, antes=None, depois=None, modelo="eleven_multilingual_v2"):
    corpo = {"text": texto, "model_id": modelo,
             "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True, "speed": 1.0}}
    if antes:
        corpo["previous_text"] = antes
    if depois:
        corpo["next_text"] = depois
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128", method="POST",
                                 data=json.dumps(corpo).encode("utf-8"),
                                 headers={"xi-api-key": _chave_eleven(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            arq.write_bytes(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs respondeu {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")


# ---------------------------------------------------------------- Windows
def _windows(falas, pasta, voz="Maria", taxa="1.05"):
    js = pasta / "_falas.json"
    js.write_text(json.dumps([{"id": f["id"], "texto": f["fala"]} for f in falas], ensure_ascii=False), encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(MOTOR / "tts_windows.ps1"), "-Entrada", str(js),
                    "-Pasta", str(pasta / "_win"), "-Voz", voz, "-Taxa", str(taxa)], check=True)
    for f in falas:
        para_wav(pasta / "_win" / f"{f['id']}.wav", pasta / f"{f['id']}.wav")


# ---------------------------------------------------------------- gerar as falas de um roteiro
def gerar(voz: dict, falas: list, pasta: Path, refazer=False) -> Path:
    """voz = {"motor": "edge"|"elevenlabs"|"windows", "nome": ..., "ritmo": "-3%", "tom": "-2Hz"}. Devolve a pasta com <id>.wav."""
    pasta.mkdir(parents=True, exist_ok=True)
    faltam = [f for f in falas if refazer or not (pasta / f"{f['id']}.wav").exists()]
    if not faltam:
        return pasta
    if voz["motor"] == "windows":
        _windows(faltam, pasta, voz.get("nome", "Maria"), voz.get("taxa", "1.05"))
        return pasta
    pausa = int(voz.get("respiro", 320))
    for f in faltam:
        i = falas.index(f)
        mp3 = pasta / f"{f['id']}.mp3"
        if voz["motor"] == "edge" and pausa > 0:
            _edge_com_respiro(f, voz, pasta, pausa)
            print(f"  voz: fala {f['id']} ok ({len(frases(f['fala']))} frases)", flush=True)
            continue
        if voz["motor"] == "edge":
            asyncio.run(_edge(f["fala"], voz["nome"], mp3, voz.get("ritmo"), voz.get("tom")))
        elif voz["motor"] == "elevenlabs":
            _eleven(f["fala"], voz["nome"], mp3, falas[i - 1]["fala"] if i else None, falas[i + 1]["fala"] if i + 1 < len(falas) else None,
                    voz.get("modelo", "eleven_multilingual_v2"))
        else:
            raise SystemExit(f"motor de voz desconhecido: {voz['motor']}")
        para_wav(mp3, pasta / f"{f['id']}.wav")
        print(f"  voz: fala {f['id']} ok", flush=True)
    return pasta


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "listar" and sys.argv[2:3] == ["edge"]:
        import edge_tts

        async def listar():
            for v in await edge_tts.list_voices():
                if v["Locale"].startswith("pt-") or "Multilingual" in v["ShortName"]:
                    print(f"{v['ShortName']:40} {v['Gender']:7} {v['Locale']}")
        asyncio.run(listar())
    elif cmd == "listar" and sys.argv[2:3] == ["elevenlabs"]:
        for v in _api_eleven("GET", "/v1/voices").get("voices", []):
            lb = v.get("labels") or {}
            print(f"{v['voice_id']} | {v['name']} | {v.get('category', '')} | sotaque {lb.get('accent', '-')} | {lb.get('gender', '')}")
    elif cmd == "biblioteca":
        import urllib.parse
        for genero in ("male", "female"):
            q = urllib.parse.urlencode({"language": "pt", "accent": "brazilian", "gender": genero, "page_size": 15, "sort": "usage_character_count_1y"})
            for v in _api_eleven("GET", f"/v1/shared-voices?{q}").get("voices", []):
                print(f"{genero:6} {v.get('voice_id')} | {v.get('name')} | {v.get('age', '')} | {v.get('use_case', '')} | {(v.get('description') or '')[:90]}")
    elif cmd == "amostra":
        motor, nome, texto, saida = sys.argv[2:6]
        if motor == "edge":
            asyncio.run(_edge(texto, nome, Path(saida)))
        elif motor == "elevenlabs":
            _eleven(texto, nome, Path(saida))
        print("amostra:", saida)
    elif cmd == "amostras":
        texto, pasta = sys.argv[2], Path(sys.argv[3]); pasta.mkdir(parents=True, exist_ok=True)
        for arq, motor, nome, aj in CATALOGO:
            destino = pasta / f"{arq}.mp3"
            try:
                if motor == "edge":
                    asyncio.run(_edge(texto, nome, destino, aj.get("ritmo"), aj.get("tom")))
                else:
                    _eleven(texto, nome, destino)
                print("ok", arq)
            except (Exception, SystemExit) as e:
                destino.unlink(missing_ok=True); print("falhou", arq, str(e)[:120])
    elif cmd == "desenhar":
        import base64
        descricao, texto, pasta = sys.argv[2], sys.argv[3], Path(sys.argv[4]); pasta.mkdir(parents=True, exist_ok=True)
        r = _api_eleven("POST", "/v1/text-to-voice/design", {"voice_description": descricao, "text": texto, "model_id": "eleven_multilingual_ttv_v2"})
        for i, pv in enumerate(r.get("previews", []), 1):
            (pasta / f"previa_{i}.mp3").write_bytes(base64.b64decode(pv["audio_base_64"]))
            print(f"prévia {i}: {pv['generated_voice_id']}")
    else:
        print("uso: py motor/vozes.py listar edge|elevenlabs | biblioteca | amostra <motor> <voz> \"texto\" <saida.mp3> | amostras \"texto\" <pasta> | desenhar \"descrição\" \"texto\" <pasta>")
