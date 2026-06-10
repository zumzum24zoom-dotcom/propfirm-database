@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo  PFD Tools Server
echo  http://localhost:8080
echo ========================================
echo.
echo サーバー起動中...
start python -m http.server 8080
timeout /t 2 /nobreak > nul
echo 起動完了。このウィンドウを閉じないでください。
echo （閉じるとサーバーが停止します）
echo.
pause
