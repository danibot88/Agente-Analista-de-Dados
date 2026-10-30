@echo off
cd /d "%~dp0"
set "APP_PY=%~dp0.venv\Scripts\python.exe"

if not exist "%APP_PY%" (
  echo Criando o ambiente Python...
  python -m venv .venv
  if errorlevel 1 goto error
)

"%APP_PY%" -m pip --version >nul 2>&1
if errorlevel 1 (
  "%APP_PY%" -m ensurepip --upgrade
  if errorlevel 1 goto error
)

"%APP_PY%" -c "import streamlit, pandas, duckdb, openpyxl, ollama" >nul 2>&1
if errorlevel 1 (
  echo Instalando as bibliotecas. Isso pode demorar alguns minutos...
  "%APP_PY%" -m pip install -r "%~dp0requirements_local.txt"
  if errorlevel 1 goto error
)

echo Abrindo o aplicativo. Mantenha esta janela aberta.
"%APP_PY%" -m streamlit run "%~dp0app_local.py" --server.address localhost
if errorlevel 1 goto error
exit /b

:error
echo O aplicativo nao iniciou. Confira a mensagem acima.
pause
