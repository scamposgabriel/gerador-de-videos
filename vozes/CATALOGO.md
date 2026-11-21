# Catálogo de vozes

Vozes testadas e aprovadas em 19/11/2026. Para ouvir antes de escolher, gere uma amostra de cada uma (comandos no fim).

| Nome | Motor | Nome no CONFIG | Observação |
|---|---|---|---|
| Masculina 1 - Antonio | edge | `pt-BR-AntonioNeural` (ritmo -3%, tom -2Hz) | nativa do Brasil; usada nos tutoriais e no exemplo (ritmo +4%) |
| Masculina 2 - William | edge | `en-AU-WilliamMultilingualNeural` | multilíngue; não aceitou ajuste de tom |
| Masculina 3 - Brian | edge | `en-US-BrianMultilingualNeural` | multilíngue, mais descontraída |
| Feminina 1 - Francisca | edge | `pt-BR-FranciscaNeural` | nativa do Brasil |
| Feminina 2 - Thalita | edge | `pt-BR-ThalitaMultilingualNeural` | nativa do Brasil (multilíngue) |
| Feminina 3 - Ava | edge | `en-US-AvaMultilingualNeural` | multilíngue |
| Feminina 4 - Emma | edge | `en-US-EmmaMultilingualNeural` | multilíngue |
| Feminina 5 - Matilda | elevenlabs | `XrExE9yKIg1WjnnlVkGX` | voz padrão do ElevenLabs falando português (modelo multilingual v2) |
| Feminina 6 - Sarah | elevenlabs | `EXAVITQu4vr4xnSDxMaL` | idem |

Não funcionam pelo Edge: `en-US-AndrewMultilingualNeural`, `fr-FR-VivienneMultilingualNeural` (NoAudioReceived).

## Motores
- **edge** (padrão): grátis, sem chave, boa qualidade. Usa o serviço de leitura do Edge pela biblioteca `edge-tts`, que não é uma
  API oficial da Microsoft: pode mudar sem aviso. Alternativa oficial com as mesmas vozes (e mais vozes brasileiras): Azure AI Speech
  (precisa de chave da conta Azure).
- **elevenlabs**: chave em `%USERPROFILE%\.secrets\elevenlabs\.env` (`ELEVENLABS_API_KEY=`). Na conta gratuita só as vozes padrão
  funcionam pela API (as da biblioteca dão erro 402); vozes brasileiras da biblioteca pedem plano pago.
- **windows**: Microsoft Maria/Daniel do próprio Windows, sem internet; robótica, só para rascunho.

## Gerar amostras
```
py motor/vozes.py listar edge
py motor/vozes.py amostra edge pt-BR-FranciscaNeural "Texto de teste em português." vozes/amostras/teste.mp3
py motor/vozes.py amostras "Texto de teste em português." vozes/amostras      (uma amostra de cada voz do catálogo)
```
