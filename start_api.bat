@echo off
chcp 65001 > /dev/null
echo ===================================
echo API Server Starting...
echo ===================================

set DASHSCOPE_API_KEY=sk-8fd736225586468eb7f4de705be7e76c
set PYTHONPATH=%cd%\src

echo [OK] API Key configured
echo [OK] PYTHONPATH: %PYTHONPATH%
echo.
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

cd src\api
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
