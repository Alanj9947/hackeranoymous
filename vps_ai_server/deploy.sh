#!/bin/bash
# deploy.sh – Deploy VPS AI Server on Ubuntu
set -euo pipefail

echo "=== VPS AI Server Deployment ==="

# 1. System updates
echo "→ Updating system..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Python 3.11+ if needed
if ! command -v python3.11 &> /dev/null; then
    echo "→ Installing Python 3.11..."
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update -y
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
fi

# 3. Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "→ Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# 4. Start Ollama service
echo "→ Starting Ollama..."
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 5

# 5. Pull model
echo "→ Pulling AI model (this may take a while)..."
ollama pull llama3.1:8b

# 6. Set up application directory
APP_DIR="/opt/vps-ai-server"
echo "→ Setting up $APP_DIR..."
sudo mkdir -p "$APP_DIR"
sudo cp -r ./* "$APP_DIR/"
sudo chown -R "$USER:$USER" "$APP_DIR"

# 7. Python virtual environment
echo "→ Creating virtual environment..."
cd "$APP_DIR"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 8. Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "→ Created .env file – PLEASE EDIT the API_KEY!"
fi

# 9. Create systemd service
echo "→ Creating systemd service..."
sudo tee /etc/systemd/system/vps-ai-server.service > /dev/null <<EOF
[Unit]
Description=VPS AI Server
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/bin
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8100 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vps-ai-server
sudo systemctl start vps-ai-server

# 10. Setup firewall
echo "→ Configuring firewall..."
sudo ufw allow 8100/tcp 2>/dev/null || true

echo ""
echo "=== Deployment Complete ==="
echo "Server running at: http://$(hostname -I | awk '{print $1}'):8100"
echo "Health check: curl http://localhost:8100/health"
echo ""
echo "⚠ Remember to:"
echo "  1. Edit /opt/vps-ai-server/.env and set a strong API_KEY"
echo "  2. Set up HTTPS with a reverse proxy (nginx + certbot)"
echo "  3. Restart: sudo systemctl restart vps-ai-server"
