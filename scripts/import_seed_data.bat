@echo off
:: import_seed_data.bat
:: Wrapper para correr el script de PowerShell sin problemas de execution policy.
:: Correr desde la raiz del proyecto: scripts\import_seed_data.bat
:: O hacer doble click directamente.

echo Iniciando importacion de datos EPU...
powershell -ExecutionPolicy Bypass -File "%~dp0import_seed_data.ps1"
pause
