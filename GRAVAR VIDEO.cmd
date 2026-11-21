@echo off
rem Grava um video tutorial do Gerador de Videos. Uso: dois cliques e digite o nome da pasta do video (dentro de "videos").
rem Ou na linha de comando:  "GRAVAR VIDEO.cmd" <pasta-do-video> [--so 04-06]
rem Video animado (Reels): py motor\animar.py videos\<pasta>
cd /d "%~dp0"
set PASTA=%1
if "%PASTA%"=="" (
  echo Videos disponiveis:
  dir /b videos
  set /p PASTA=Nome da pasta do video:
)
py motor\gravar.py "videos\%PASTA%" %2 %3
echo.
pause
