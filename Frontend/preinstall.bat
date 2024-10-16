@echo off
echo 正在执行预安装脚本...

:: 创建一个新目录
mkdir C:\MindPilotTemp

:: 在新目录中创建一个文本文件
echo 安装时间: %date% %time% > C:\MindPilotTemp\install_log.txt

:: 显示一条消息
echo 预安装步骤完成!

:: 暂停,以便用户可以看到消息(可选)
pause
