#!/bin/bash
# ============================================================
#  AmitShield C++ Core — Build & Install Script
#  Run this on Linux (or WSL2) to compile the C++ engine
# ============================================================

set -e
BOLD='\033[1m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════╗"
echo "  ║  AmitShield — C++ Build Script  ║"
echo "  ╚══════════════════════════════════╝"
echo -e "${NC}"

# Check deps
echo -e "${GREEN}[1/4]${NC} Checking build tools..."
command -v g++   &>/dev/null || { sudo apt-get install -y g++;   }
command -v cmake &>/dev/null || { sudo apt-get install -y cmake; }

# Build
echo -e "${GREEN}[2/4]${NC} Compiling C++ engine..."
mkdir -p ../build-cpp && cd ../build-cpp
cmake ../core -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
make -j$(nproc)

# Install
echo -e "${GREEN}[3/4]${NC} Installing..."
sudo make install
sudo ldconfig

# Quick compile fallback (single-file, no cmake)
echo -e "${GREEN}[4/4]${NC} Also building single-file .so for bridge..."
g++ -O3 -std=c++17 -shared -fPIC -pthread \
    -o ../bridge/libamitshield.so \
    ../core/amitshield_core.cpp \
    -lpthread
echo -e "  .so copied to bridge/ folder ✓"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗"
echo -e "║  ✓ AmitShield Build Complete!        ║"
echo -e "║  Library : /usr/local/lib/           ║"
echo -e "║  Daemon  : /usr/local/bin/           ║"
echo -e "╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Test bridge: python3 bridge/amitshield_bridge.py"
echo "  Start daemon: sudo amitshield-daemon"
