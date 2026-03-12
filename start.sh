#!/bin/bash
set -e

echo "🔄 Päivitetään järjestelmä..."
 apt update && apt upgrade -y

echo "📦 Asennetaan peruspaketit..."
 apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  build-essential \
  curl \
  wget \
  git \
  ca-certificates

echo "🔊 Asennetaan ääni- ja mediakirjastot (FFmpeg)..."
 apt install -y \
  ffmpeg \
  libopus0 \
  libopus-dev \
  libnacl-dev

echo "🌐 Asennetaan HTML / XML parser -riippuvuudet..."
 apt install -y \
  libxml2 \
  libxml2-dev \
  libxslt1-dev \
  zlib1g-dev

echo "🔐 Asennetaan SSL / crypto -kirjastot..."
 apt install -y \
  libffi-dev \
  libssl-dev

echo "🐍 Luodaan Python-virtuaaliympäristö..."
python3 -m venv venv

echo "✅ Aktivoidaan virtuaaliympäristö..."
source venv/bin/activate

echo "⬆️ Päivitetään pip..."
pip install --upgrade pip setuptools wheel

echo "📥 Asennetaan Python-riippuvuudet (requirements.txt)..."
pip install -r requirements.txt

echo ""
echo "🚀 Käynnistetään Discord-botti (bot.py)..."
echo "────────────────────────────────────"
python3 run.py
