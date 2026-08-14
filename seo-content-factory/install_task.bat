@echo off
chcp 936 >nul
cd /d "%~dp0"
setlocal enabledelayedexpansion
echo ============================================
echo    SEO 内容分发工厂 - 一键安装
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo 请先安装 Python，安装时务必勾选 Add python.exe to PATH：
    echo    https://www.python.org/downloads/
    echo 安装完成后重新双击本文件。
    pause
    exit /b 1
)

echo [诊断] Python 信息：
python --version
python -m pip --version
echo.
echo [诊断] 代理环境变量（有值的话说明 pip 可能走了代理）：
echo    HTTP_PROXY  = %HTTP_PROXY%
echo    HTTPS_PROXY = %HTTPS_PROXY%
echo.
echo [诊断] 测试 HTTPS 连通性（curl 正常返回 200 说明网络本身没问题）...
curl -s -o nul -w "    HTTP状态码: %%{http_code}`n" --connect-timeout 10 https://pypi.tuna.tsinghua.edu.cn/simple/ 2>nul
if errorlevel 1 echo    curl 连接失败
echo.

echo [1/4] 安装依赖库（自动尝试 4 种镜像配置，请耐心等待）...
set SUCCESS=0

echo   尝试 1/4：清华 HTTPS...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --timeout 30
if !errorlevel!==0 set SUCCESS=1

if !SUCCESS!==0 (
    echo.
    echo   尝试 2/4：阿里云 HTTPS...
    python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --timeout 30
    if !errorlevel!==0 set SUCCESS=1
)

if !SUCCESS!==0 (
    echo.
    echo   尝试 3/4：清华 HTTP...
    python -m pip install -r requirements.txt -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --timeout 30
    if !errorlevel!==0 set SUCCESS=1
)

if !SUCCESS!==0 (
    echo.
    echo   尝试 4/4：阿里云 HTTP...
    python -m pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --timeout 30
    if !errorlevel!==0 set SUCCESS=1
)

if !SUCCESS!==0 (
    echo.
    echo [错误] 依赖安装失败。常见原因与解决办法：
    echo   1. 电脑开着代理/VPN（Clash、v2rayN、加速器 等）
    echo      → 先关闭它（或切到「规则模式/直连」），再重新双击本文件
    echo   2. 安全软件拦截（360 / 火绒 / 电脑管家）
    echo      → 暂时退出后重试
    echo   3. Python 版本太旧
    echo      → 到 https://www.python.org/downloads/ 安装新版
    echo.
    echo 如果以上都试了还不行，把本窗口完整内容截图发给我。
    pause
    exit /b 1
)

echo.
echo [2/4] 检查配置文件...
if not exist .env (
    copy .env.example .env >nul
    echo    已生成 .env 文件，稍后会自动打开，请填写真实密钥！
) else (
    echo    .env 已存在，跳过。
)
if not exist config\daily_plan.json (
    copy config\daily_plan.example.json config\daily_plan.json >nul
    echo    已生成 config\daily_plan.json（每日关键词计划）。
) else (
    echo    config\daily_plan.json 已存在，跳过。
)

echo.
echo [3/4] 创建 Windows 计划任务「SEO每日任务」（每天 10:00 自动生成文章到 WP 草稿箱）...
schtasks /create /tn "SEO每日任务" /tr "\"%~dp0run_daily.bat\"" /sc daily /st 10:00 /f

echo.
echo [4/4] 安装完成！
echo.
echo 接下来请做：
echo   1. 在弹出的 .env 记事本里，把每个 = 后面填成真实密钥并保存
echo   2. 双击 test_daily.bat 手动测试一次，成功后会写一篇草稿到 WordPress
echo   3. 想改运行时间：控制面板 - 管理工具 - 任务计划程序 - 找到 SEO每日任务
echo   4. 卸载：双击 uninstall_task.bat
echo.
start notepad .env
pause