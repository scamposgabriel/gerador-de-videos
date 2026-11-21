# Gera um WAV por fala com a voz neural do Windows (OneCore, pt-BR). Entrada: arquivo JSON [{id, texto}], pasta de saída e voz.
# Usa só o que já vem no Windows (Windows.Media.SpeechSynthesis); nada vai para a internet.
param([string]$Entrada, [string]$Pasta, [string]$Voz = 'Daniel', [string]$Taxa = '1.0')
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Esperar($op, [Type]$tipo) { $t = $asTask.MakeGenericMethod($tipo).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
$s = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$v = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.Language -eq 'pt-BR' -and $_.DisplayName -like "*$Voz*" } | Select-Object -First 1
if (-not $v) { throw "voz $Voz não encontrada" }
$s.Voice = $v
$s.Options.SpeakingRate = [double]$Taxa
New-Item -ItemType Directory -Force $Pasta | Out-Null
$itens = Get-Content -Raw -Encoding UTF8 $Entrada | ConvertFrom-Json
foreach ($it in $itens) {
  $stream = Esperar ($s.SynthesizeTextToStreamAsync($it.texto)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
  $tam = [uint32]$stream.Size
  $leitor = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
  $null = Esperar ($leitor.LoadAsync($tam)) ([uint32])
  $bytes = New-Object byte[] $tam
  $leitor.ReadBytes($bytes)
  [System.IO.File]::WriteAllBytes((Join-Path $Pasta ($it.id + '.wav')), $bytes)
  $leitor.Dispose(); $stream.Dispose()
}
"ok: $($itens.Count) falas com a voz $($v.DisplayName)"
