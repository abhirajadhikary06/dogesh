#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Dogesh Assistant – Setup Script
# Usage:  chmod +x setup.sh && ./setup.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║          Dogesh Assistant  –  Setup                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. System audio deps (Linux) ─────────────────────────────────────────────
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "[1/4] Installing system audio libraries (may need sudo)…"
    sudo apt-get update -qq
    sudo apt-get install -y portaudio19-dev libespeak1 espeak ffmpeg > /dev/null 2>&1 || true
    echo "      ✓ System deps OK"
fi

# ── 2. Python virtual environment ────────────────────────────────────────────
echo "[2/4] Creating Python virtual environment…"
python3 -m venv .venv
source .venv/bin/activate
echo "      ✓ .venv created"

# ── 3. Python packages ────────────────────────────────────────────────────────
echo "[3/4] Installing Python packages (this may take a minute)…"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "      ✓ Packages installed"

# ── 4. Env file ───────────────────────────────────────────────────────────────
echo "[4/4] Setting up environment…"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "      ✓ .env created from .env.example"
else
    echo "      ✓ .env already exists"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Setup complete!  Run:  flet run main.py            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
