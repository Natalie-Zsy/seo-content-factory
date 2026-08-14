@echo off
chcp 936 >nul
cd /d "%~dp0"
where python >nul 2>nul || (
    echo [错误] 未检测到 Python，请先安装并勾选 Add to PATH
    pause
    exit /b 1
)
echo 正在启动网页工具，稍后浏览器会自动打开 http://localhost:8501
python -m streamlit run app.py
pause