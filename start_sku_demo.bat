@echo off
echo ========================================
echo SKU功能演示环境启动脚本
echo ========================================
echo.

REM 检查Docker是否运行
echo [1/4] 检查Docker服务状态...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker未安装或未运行
    echo 请先安装并启动Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker服务正常

REM 启动后端服务
echo.
echo [2/4] 启动后端服务...
cd backend
docker compose up -d
if errorlevel 1 (
    echo ❌ 后端服务启动失败
    pause
    exit /b 1
)
echo ✅ 后端服务启动成功

REM 等待后端服务启动
echo.
echo [3/4] 等待后端服务就绪...
timeout /t 10 /nobreak >nul
echo ✅ 后端服务就绪

REM 检查前端依赖
echo.
echo [4/4] 检查前端环境...
cd ..\frontend
if not exist "node_modules" (
    echo ⚠ 前端依赖未安装，正在安装...
    pnpm install
    if errorlevel 1 (
        echo ❌ 前端依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 前端依赖安装成功
) else (
    echo ✅ 前端依赖已安装
)

REM 启动前端服务
echo.
echo [5/5] 启动前端开发服务器...
start cmd /k "cd /d %cd% && pnpm dev"

echo.
echo ========================================
echo 🎉 SKU演示环境启动完成！
echo ========================================
echo.
echo 访问地址：
echo 前端界面：http://localhost:3000
echo API文档：http://localhost:5000/docs
echo.
echo SKU功能路径：
echo 1. SKU列表：http://localhost:3000/product/sku
echo 2. 创建测试数据后访问详情页
echo.
echo 按任意键打开浏览器访问SKU列表...
pause >nul
start http://localhost:3000/product/sku

echo.
echo 提示：要停止服务，请运行 stop_sku_demo.bat
pause
