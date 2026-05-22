#!/bin/bash
# ============================================================
#  AMIT OS — Main ISO Build Script
#  Version: 1.0
#  Author:  Amit
#  Description: Builds the complete Amit OS Live ISO
# ============================================================

set -e  # Exit on any error
set -o pipefail

# ─── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Config ──────────────────────────────────────────────────
OS_NAME="AmitOS"
OS_VERSION="1.0"
ARCH="amd64"
DEBIAN_SUITE="bookworm"
MIRROR="http://deb.debian.org/debian"
OUTPUT_DIR="$(pwd)/../output"
BUILD_DIR="$(pwd)/../build-tmp"
LOG_FILE="$OUTPUT_DIR/build.log"

# ─── Banner ──────────────────────────────────────────────────
print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "  █████╗ ███╗   ███╗██╗████████╗ ██████╗ ███████╗"
    echo " ██╔══██╗████╗ ████║██║╚══██╔══╝██╔═══██╗██╔════╝"
    echo " ███████║██╔████╔██║██║   ██║   ██║   ██║███████╗"
    echo " ██╔══██║██║╚██╔╝██║██║   ██║   ██║   ██║╚════██║"
    echo " ██║  ██║██║ ╚═╝ ██║██║   ██║   ╚██████╔╝███████║"
    echo " ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝   ╚═╝    ╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "${BOLD}  Amit OS v${OS_VERSION} — ISO Build System${NC}"
    echo -e "${YELLOW}  Fast. Secure. Beautiful.${NC}"
    echo "  ─────────────────────────────────────────────"
    echo ""
}

# ─── Logging ─────────────────────────────────────────────────
log()     { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"; }
warn()    { echo -e "${YELLOW}[⚠]${NC} $1" | tee -a "$LOG_FILE"; }
error()   { echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"; exit 1; }
info()    { echo -e "${BLUE}[i]${NC} $1" | tee -a "$LOG_FILE"; }
step()    { echo -e "\n${CYAN}${BOLD}━━━ $1 ━━━${NC}\n" | tee -a "$LOG_FILE"; }

# ─── Check root ──────────────────────────────────────────────
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Please run as root: sudo ./build.sh"
    fi
    log "Running as root — OK"
}

# ─── Check dependencies ──────────────────────────────────────
check_deps() {
    step "Checking Build Dependencies"
    DEPS=(live-build debootstrap squashfs-tools xorriso grub-efi-amd64-bin grub-pc-bin mtools)
    MISSING=()
    for dep in "${DEPS[@]}"; do
        if ! dpkg -l "$dep" &>/dev/null; then
            MISSING+=("$dep")
        fi
    done
    if [ ${#MISSING[@]} -gt 0 ]; then
        warn "Installing missing dependencies: ${MISSING[*]}"
        apt-get update -qq
        apt-get install -y "${MISSING[@]}"
    fi
    log "All dependencies satisfied"
}

# ─── Setup live-build config ─────────────────────────────────
setup_lb_config() {
    step "Configuring live-build"
    mkdir -p "$BUILD_DIR"
    cp -r ../config/* "$BUILD_DIR/" 2>/dev/null || true

    cd "$BUILD_DIR"

    lb config \
        --mode debian \
        --distribution "$DEBIAN_SUITE" \
        --architecture "$ARCH" \
        --mirror-bootstrap "$MIRROR" \
        --mirror-binary "$MIRROR" \
        --binary-images iso-hybrid \
        --bootappend-live "boot=live components quiet splash" \
        --debian-installer live \
        --debian-installer-gui true \
        --memtest none \
        --iso-volume "AmitOS 1.0" \
        --iso-publisher "Amit" \
        --iso-application "Amit OS" \
        --firmware-binary true \
        --firmware-chroot true \
        --apt-secure true \
        --security true \
        --updates true

    log "live-build configured"
}

# ─── Copy custom files ───────────────────────────────────────
copy_custom_files() {
    step "Copying Custom AmitOS Files"

    CHROOT="$BUILD_DIR/config/includes.chroot"
    mkdir -p "$CHROOT/usr/local/bin"
    mkdir -p "$CHROOT/etc/amitshield"
    mkdir -p "$CHROOT/usr/share/amitos/themes"
    mkdir -p "$CHROOT/usr/share/amitos/wallpapers"
    mkdir -p "$CHROOT/usr/share/applications"
    mkdir -p "$CHROOT/etc/skel/.config"

    # Copy AmitShield
    cp -r ../../amitshield/* "$CHROOT/usr/local/bin/" 2>/dev/null || warn "AmitShield not found, skipping"

    # Copy apps
    cp -r ../../apps/* "$CHROOT/usr/local/bin/" 2>/dev/null || warn "Custom apps not found, skipping"

    # Copy themes
    cp -r ../../themes/* "$CHROOT/usr/share/amitos/themes/" 2>/dev/null || warn "Themes not found, skipping"

    log "Custom files copied"
}

# ─── Build the ISO ───────────────────────────────────────────
build_iso() {
    step "Building Amit OS ISO (this takes 15-30 minutes...)"
    cd "$BUILD_DIR"
    lb build 2>&1 | tee -a "$LOG_FILE"
    log "ISO build complete"
}

# ─── Move output ─────────────────────────────────────────────
move_output() {
    step "Finalizing Output"
    mkdir -p "$OUTPUT_DIR"
    ISO_FILE=$(find "$BUILD_DIR" -name "*.iso" | head -1)
    if [ -z "$ISO_FILE" ]; then
        error "ISO file not found after build!"
    fi
    cp "$ISO_FILE" "$OUTPUT_DIR/amit-os-${OS_VERSION}-${ARCH}.iso"
    SIZE=$(du -sh "$OUTPUT_DIR/amit-os-${OS_VERSION}-${ARCH}.iso" | cut -f1)
    log "ISO created: $OUTPUT_DIR/amit-os-${OS_VERSION}-${ARCH}.iso ($SIZE)"
}

# ─── Print summary ───────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║     🎉 AMIT OS BUILD SUCCESSFUL! 🎉      ║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}ISO Location:${NC} $OUTPUT_DIR/amit-os-${OS_VERSION}-${ARCH}.iso"
    echo -e "  ${BOLD}Build Log:${NC}   $LOG_FILE"
    echo ""
    echo -e "  ${YELLOW}Test with:${NC}"
    echo -e "  qemu-system-x86_64 -m 4G -cdrom $OUTPUT_DIR/amit-os-${OS_VERSION}-${ARCH}.iso -boot d"
    echo ""
}

# ─── MAIN ────────────────────────────────────────────────────
main() {
    print_banner
    mkdir -p "$OUTPUT_DIR"
    : > "$LOG_FILE"

    check_root
    check_deps
    setup_lb_config
    copy_custom_files
    build_iso
    move_output
    print_summary
}

main "$@"
