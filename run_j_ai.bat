@echo off
setlocal EnableExtensions
cd /d %~dp0

if "%JAI_MODEL_PATH%"=="" set "JAI_MODEL_PATH=D:\Models Library\gemma-2-2b-it-Q4_K_M.gguf"

echo [J.AI] Creating venv if missing...
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat

echo [J.AI] Upgrading pip...
python -m pip install --upgrade pip

echo [J.AI] Installing dependencies...
pip install -r requirements.txt

echo [J.AI] Enforcing non-AVX2 llama build...
pip uninstall -y llama-cpp-python >nul 2>&1
pip install llama-cpp-python==0.2.75 --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

echo [J.AI] Starting local server on http://127.0.0.1:8000
python main.py
endlocal
