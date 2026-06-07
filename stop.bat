@echo off
echo ========================================
echo   猫咪民宿预订管理系统 - 停止服务
echo ========================================
echo.

echo 正在停止所有服务...
docker-compose down

echo.
echo 所有服务已停止
pause
