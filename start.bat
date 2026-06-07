@echo off
echo ========================================
echo   猫咪民宿预订管理系统 - 一键启动
echo ========================================
echo.

echo [1/4] 检查Docker环境...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Docker，请先安装Docker Desktop
    pause
    exit /b 1
)
echo Docker环境检查通过
echo.

echo [2/4] 停止旧容器（如果存在）...
docker-compose down >nul 2>&1
echo.

echo [3/4] 构建并启动所有服务...
docker-compose up -d --build
if %errorlevel% neq 0 (
    echo 错误: 服务启动失败，请查看日志
    docker-compose logs
    pause
    exit /b 1
)
echo.

echo [4/4] 等待服务就绪...
timeout /t 10 /nobreak >nul
echo.

echo ========================================
echo   服务启动成功！
echo ========================================
echo.
echo 前端地址: http://localhost
echo 后端API: http://localhost/api/v1
echo API文档: http://localhost/docs
echo 数据库端口: 5432
echo Redis端口: 6379
echo.
echo 查看日志: docker-compose logs -f
echo 停止服务: docker-compose down
echo.
pause
