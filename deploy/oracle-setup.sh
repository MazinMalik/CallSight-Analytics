#!/bin/bash
# ==============================================================================
# Oracle Cloud Free Tier Ubuntu (ARM64 / x86_64) Automated Setup Script
# Telecaller Call Recording, IndicConformer Transcription & Qwen 4B System
# ==============================================================================

set -e

echo "=== Starting Telecaller Automation System Deployment Setup ==="

# 1. Update system packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git python3 python3-pip python3-venv ffmpeg nginx curl build-essential

# 2. Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Enable and start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

echo "Pulling Qwen 4B LLM model (qwen3:4b / qwen:4b)..."
ollama pull qwen3:4b || ollama pull qwen:4b || true

# 3. Setup Backend Repository
APP_DIR="/opt/telecaller-dashboard"
sudo mkdir -p $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

if [ -d "$APP_DIR/backend" ]; then
    echo "Updating existing code at $APP_DIR..."
else
    echo "Copying backend workspace files into $APP_DIR..."
fi

# Create Python virtualenv
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate

pip install --upgrade pip
if [ -f "$APP_DIR/backend/requirements.txt" ]; then
    pip install -r $APP_DIR/backend/requirements.txt
fi

# Create storage directories
mkdir -p $APP_DIR/backend/data $APP_DIR/backend/uploads $APP_DIR/backend/exports

# 4. Install Systemd Service for Uvicorn Backend
echo "Configuring Systemd service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/telecaller-backend.service
[Unit]
Description=Telecaller Audio Automation FastAPI Backend Service
After=network.target ollama.service

[Service]
User=$USER
WorkingDirectory=$APP_DIR/backend
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5
Environment=PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=APP_ENV=production
Environment=DATABASE_URL=sqlite:///./data/telecaller.db
Environment=OLLAMA_BASE_URL=http://localhost:11434
Environment=OLLAMA_MODEL=qwen3:4b

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable telecaller-backend
sudo systemctl restart telecaller-backend

# 5. Configure Nginx Reverse Proxy
echo "Configuring Nginx..."
sudo bash -c "cat <<EOF > /etc/nginx/sites-available/telecaller
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # CORS Headers for Vercel Frontend
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PATCH, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;

        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
}
EOF"

sudo ln -sf /etc/nginx/sites-available/telecaller /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "=== Setup Completed Successfully! ==="
echo "Backend API is running on http://$(curl -s ifconfig.me)/api/health"
