@echo off
echo ========================================
echo SKU功能演示环境停止脚本
echo ========================================
echo.

REM 停止前端服务
echo [1/3] 停止前端服务...
taskkill /F /IM node.exe >nul 2>&1
echo ✅ 前端服务已停止

REM 停止后端服务
echo.
echo [2/3] 停止后端服务...
cd backend
docker compose down
if errorlevel 1 (
    echo ⚠ 后端服务停止时出现警告
) else (
    echo ✅ 后端服务已停止
)

REM 清理临时文件
echo.
echo [3/3] 清理临时文件...
cd ..
del test_sku_api.py >nul 2>&1
echo ✅ 临时文件已清理

echo.
echo ========================================
echo 🛑 SKU演示环境已完全停止
echo ========================================
echo.
echo 所有服务已停止，可以安全关闭。
pause
