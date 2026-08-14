@echo off
chcp 936 >nul
cd /d "%~dp0"
echo 正在手动执行一次每日任务（会真实调用 API，并写一篇草稿到 WordPress）...
echo.
call run_daily.bat
echo.
echo ---------- 最近日志 ----------
powershell -NoProfile -Command "if (Test-Path 'data\daily_log.txt') { Get-Content 'data\daily_log.txt' -Tail 20 } else { Write-Output '（还没有日志文件）' }"
echo.
pause