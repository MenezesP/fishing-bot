@echo off
color 0B
title Iniciador do Bot Poke Memories

echo ==============================================
echo    Verificando privilegios de Administrador...
echo ==============================================

:: Tenta executar um comando que só administradores podem (net session)
net session >nul 2>&1

:: Se o errorLevel for 0, significa que somos Administrador
if %errorLevel% == 0 (
    echo [OK] Privilegios de Administrador confirmados!
    goto :iniciar_bot
) else (
    echo [AVISO] Solicitando permissoes de Administrador...
    :: Reinicia o proprio arquivo .bat pedindo privilegios como administrador usando PowerShell
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:iniciar_bot
:: Muda o diretorio atual para a pasta onde este ficheiro .bat esta localizado
cd /d "%~dp0"

echo.
echo Ativando o ambiente virtual (venv)...
:: Verifica se o script de ativacao do venv existe e executa-o
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    echo [OK] Ambiente virtual ativado com sucesso!
) else (
    echo [AVISO] Pasta 'venv' nao encontrada ou sem activate.bat.
    echo Tentando executar com a instalacao global do Python...
)

echo.
echo Iniciando o Python...
echo.

:: Executa o bot
python bot_pesca.py

:: Se o bot fechar ou der erro, pausa a tela para poderes ler o que aconteceu
echo.
pause