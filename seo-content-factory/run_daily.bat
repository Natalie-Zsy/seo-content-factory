@echo off
chcp 936 >nul
cd /d "%~dp0"
where python >nul 2>nul || (
    echo [错误] 未检测到 Python
    exit /b 1
)
if not exist .env (
    echo [错误] 未找到 .env 配置文件，请先双击 install_task.bat 完成安装
    exit /b 1
)
echo [%date% %time%] 开始执行每日任务...
python scripts/daily_article.py >> data\daily_log.txt 2>&1
set EXITCODE=%ERRORLEVEL%
echo [%date% %time%] 执行结束，退出码 %EXITCODE%，日志：data\daily_log.txt
exit /b %EXITCODE%