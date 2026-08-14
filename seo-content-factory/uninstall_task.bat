@echo off
chcp 936 >nul
schtasks /delete /tn "SEO每日任务" /f
echo 已删除计划任务「SEO每日任务」
pause