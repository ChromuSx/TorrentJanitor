#!/bin/bash

# TorrentJanitor Quick Setup Script
# This script helps you quickly set up TorrentJanitor

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ASCII Art Banner
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════╗"
echo "║        🧹 TorrentJanitor Setup 🧹              ║"
echo "║    Keep it clean, keep it lean!               ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Check Python version
print_message "Checking Python version..."
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_message "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Docker is installed (optional)
if command -v docker &>/dev/null; then
    print_message "Docker is installed"
    USE_DOCKER=true
else
    print_warning "Docker is not installed. Proceeding with Python-only setup."
    USE_DOCKER=false
fi

# Create virtual environment
print_message "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
print_message "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy configuration
if [ ! -f config.json ]; then
    print_message "Creating configuration file..."
    cp config.example.json config.json
    print_warning "Please edit config.json with your qBittorrent credentials"
fi

# Copy environment file
if [ ! -f .env ]; then
    print_message "Creating environment file..."
    cp .env.example .env
    print_warning "Please edit .env with your settings"
fi

# Create necessary directories
print_message "Creating data directories..."
mkdir -p data logs

# Docker setup (if available)
if [ "$USE_DOCKER" = true ]; then
    print_message "Building Docker image..."
    docker build -t torrentjanitor:latest .
    print_message "Docker image built successfully!"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your qBittorrent credentials"
echo "2. Edit .env if using environment variables"
echo ""
echo "To run TorrentJanitor:"
echo ""
echo "  With Python:"
echo "    source venv/bin/activate"
echo "    python torrentjanitor.py --dry-run --once  # Test mode"
echo "    python torrentjanitor.py                   # Normal mode"
echo ""
if [ "$USE_DOCKER" = true ]; then
    echo "  With Docker:"
    echo "    docker run -v \$(pwd)/config:/config torrentjanitor:latest --dry-run --once"
    echo "    docker-compose up -d  # Using docker-compose"
fi
echo ""
echo "For help: python torrentjanitor.py --help"
echo ""
echo -e "${GREEN}Happy cleaning! 🧹${NC}"