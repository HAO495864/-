@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 小鲸鱼打工日记
echo.
echo   🐋  正在启动本地小服务器...
echo.
where py >nul 2>nul
if %errorlevel%==0 (
    py server.py
) else (
    python server.py
)
echo.
echo  服务已停止。按任意键关闭窗口。
pause >nul
