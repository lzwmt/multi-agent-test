#!/bin/bash
# AionUi 服务器部署脚本

set -e

echo "=== 安装 AionUi WebUI ==="

# 1. 安装依赖
echo "[1/4] 安装依赖..."
sudo apt-get update
sudo apt-get install -y xvfb libxkbcommon-x11-0

# 2. 下载 AionUi
echo "[2/4] 下载 AionUi..."
cd /tmp
wget -O AionUi-linux-amd64.deb https://github.com/iOfficeAI/AionUi/releases/download/v1.8.23/AionUi-1.8.23-linux-amd64.deb

# 3. 安装
echo "[3/4] 安装 AionUi..."
sudo dpkg -i AionUi-linux-amd64.deb || sudo apt-get install -f -y

# 4. 创建启动脚本
echo "[4/4] 创建启动脚本..."
sudo mkdir -p /opt/AionUi

cat << 'EOF' | sudo tee /opt/AionUi/start-aionui.sh > /dev/null
#!/bin/bash
# AionUi WebUI 启动脚本

PIDFILE="/var/run/aionui.pid"
LOGFILE="/var/log/aionui.log"
WORKDIR="/root"  # 工作目录

start() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
        echo "AionUi 已在运行 (PID: $(cat $PIDFILE))"
        return 1
    fi
    echo "正在启动 AionUi WebUI..."
    cd "$WORKDIR"

    nohup xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" \
        /usr/bin/AionUi --webui --remote --no-sandbox \
        > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 3
    if kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
        echo "AionUi 启动成功 (PID: $(cat $PIDFILE))"
        echo "WebUI: http://$(hostname -I | awk '{print $1}'):25808"
    else
        echo "AionUi 启动失败，请查看日志: $LOGFILE"
        rm -f "$PIDFILE"
        return 1
    fi
}

stop() {
    if [ ! -f "$PIDFILE" ]; then
        echo "AionUi 未在运行"
        return 1
    fi
    PID=$(cat "$PIDFILE")
    echo "正在停止 AionUi (PID: $PID)..."
    kill "$PID" 2>/dev/null
    sleep 2
    kill -9 "$PID" 2>/dev/null
    pkill -f "AionUi --webui" 2>/dev/null
    rm -f "$PIDFILE"
    echo "AionUi 已停止。"
}

restart() { stop; sleep 1; start; }

status() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
        echo "AionUi 运行中 (PID: $(cat $PIDFILE))"
        ss -tlnp | grep 25808 || true
    else
        echo "AionUi 未在运行。"
        rm -f "$PIDFILE" 2>/dev/null
    fi
}

case "${1:-start}" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    *) echo "用法: $0 {start|stop|restart|status}" ;;
esac
EOF

sudo chmod +x /opt/AionUi/start-aionui.sh
sudo ln -sf /opt/AionUi/start-aionui.sh /usr/local/bin/aionui

echo ""
echo "=== 安装完成 ==="
echo "启动命令: sudo aionui start"
echo "停止命令: sudo aionui stop"
echo "查看状态: sudo aionui status"
echo "日志文件: /var/log/aionui.log"
