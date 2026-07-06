@echo off
title Vagas Sniper Bot - Local Runner
mode con: cols=90 lines=30
color 0A

echo =======================================================================
echo              VAGAS SNIPER BOT - INICIADOR LOCAL (WINDOWS)              
echo =======================================================================
echo.
echo [+] Iniciando os motores com o seu IP residencial...
echo [+] Verificando ambiente Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nao encontrado no PATH! Por favor, instale o Python.
    pause
    exit /b
)

echo [+] Rodando o bot e o servidor local...
echo.
echo =======================================================================
echo LOGS DO SISTEMA:
echo =======================================================================
python render_bot.py
echo.
echo =======================================================================
echo [!] O processo foi encerrado.
pause
