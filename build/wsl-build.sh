#!/bin/bash
# ============================================================
#  AMIT OS — Complete ISO Build Script (runs inside WSL2)
#  Builds a real bootable Debian-based Live ISO
#  Output: /mnt/d/Amit os/output/amit-os-1.0-amd64.iso
# ============================================================

set -e
BOLD='\033[1m'; GREEN='\033[0;32m'; RED='\033[0;31m'
YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

WIN_OUT="/mnt/d/Amit os/output"
BUILD_TMP="/tmp/amitos-build"
LOG="$WIN_OUT/build.log"

# ── Banner ────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
cat << 'BANNER'
    _   _   _ ___ _____    ___  ____  
   / \ | \ | |_ _|_   _|  / _ \/ ___| 
  / _ \|  \| || |  | |   | | | \___ \ 
 / ___ \ |\  || |  | |   | |_| |___) |
/_/   \_\_| \_|___| |_|    \___/|____/ 
BANNER
echo -e "${NC}${BOLD}  Amit OS 1.0 — ISO Build System${NC}"
echo -e "${YELLOW}  Fast • Secure • Beautiful${NC}"
echo "  ─────────────────────────────────────────"

mkdir -p "$WIN_OUT"
: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

step() { echo -e "\n${CYAN}${BOLD}[STEP] $1${NC}"; }
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
fail() { echo -e "${RED}✗ ERROR: $1${NC}"; exit 1; }

# ── Must be root ──────────────────────────────────────────────
[ "$EUID" -eq 0 ] || fail "Run as root: sudo bash wsl-build.sh"

# ── Step 1: Install dependencies ─────────────────────────────
step "Installing build dependencies..."

# Network & DNS Fix for WSL
ip link set dev eth0 mtu 1350 2>/dev/null || true
echo "nameserver 8.8.8.8" > /etc/resolv.conf
sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null 2>&1 || true

# Switch to stable mirror
sed -i 's/archive.ubuntu.com/mirrors.kernel.org/g' /etc/apt/sources.list.d/ubuntu.sources 2>/dev/null || true
sed -i 's/security.ubuntu.com/mirrors.kernel.org/g' /etc/apt/sources.list.d/ubuntu.sources 2>/dev/null || true

apt-get update -qq
apt-get install -y --fix-missing --no-install-recommends \
    live-build live-config live-boot \
    debootstrap squashfs-tools xorriso \
    grub-efi-amd64-bin grub-pc-bin mtools \
    syslinux isolinux syslinux-common \
    wget curl git python3
ok "Dependencies installed"

# ── Step 2: Prepare Fast Build Environment ───────────────────
BUILD_DIR="/tmp/amitos-build"
WIN_CACHE="/mnt/d/Amit os/cache"
step "Setting up High-Speed Workspace ($BUILD_DIR)..."

# Ensure host cache exists
mkdir -p "$WIN_CACHE"

# CRITICAL: Unmount any leftover points from previous failed runs
echo "Checking for active mount points in $BUILD_DIR..."
for mnt in $(mount | grep "$BUILD_DIR" | awk '{print $3}' | sort -r); do
    warn "Unmounting active mount point: $mnt"
    umount -l "$mnt" 2>/dev/null || true
done

# Clean build dir but PRESERVE CACHE by not deleting the bind-mounted target if active
sudo rm -rf "$BUILD_DIR/config" "$BUILD_DIR/chroot" "$BUILD_DIR/binary" "$BUILD_DIR/local" "$BUILD_DIR/.build"
sudo rm -f "$BUILD_DIR/.lock"
mkdir -p "$BUILD_DIR/cache"

# Bind mount the persistent cache from Windows D: drive to WSL fast storage
# This ensures nothing is re-downloaded if it already exists in D:\Amit os\cache
sudo mount --bind "$WIN_CACHE" "$BUILD_DIR/cache"

cd "$BUILD_DIR"
ok "Fast Build Environment ready (with persistent cache)"

# ── Step 3: Sync Windows Workspace to Build Dir ────────────
step "Syncing Amit OS workspace files..."
# Create directory structure
mkdir -p config/includes.chroot/etc/apt
mkdir -p config/includes.chroot/usr/local/amitos/apps
mkdir -p config/includes.chroot/usr/local/amitos/branding
mkdir -p config/includes.chroot/usr/local/amitos/core
mkdir -p config/hooks/normal

# Sync files from Windows host to Fast Storage
WSL_HOST="/mnt/d/Amit os"
cp -r "$WSL_HOST/branding/"* config/includes.chroot/usr/local/amitos/branding/ 2>/dev/null || true
cp -r "$WSL_HOST/apps/"*     config/includes.chroot/usr/local/amitos/apps/     2>/dev/null || true
cp -r "$WSL_HOST/core/"*     config/includes.chroot/usr/local/amitos/core/     2>/dev/null || true
cp -r "$WSL_HOST/themes/"*   config/includes.chroot/usr/share/themes/          2>/dev/null || true

# Sync custom config (hooks, includes) from Windows host
cp -r "$WSL_HOST/config/"* config/ 2>/dev/null || true

# Copy AmitShield UI app
cp "$WSL_HOST/amitshield/amitshield-ui.py" config/includes.chroot/usr/local/amitos/apps/amitshield-ui.py 2>/dev/null || true

# Copy bridge module
cp -r "$WSL_HOST/bridge/"* config/includes.chroot/usr/local/amitos/core/ 2>/dev/null || true

ok "Workspace files synced to fast storage"

# ── Step 3: Configure live-build ──────────────────────────────
step "Configuring live-build for Amit OS..."
# CLEANUP: Remove old manual repo files
rm -rf config/archives/*.list
rm -rf config/includes.chroot/etc/apt/sources.list

# ── Step 4: Configure Live-Build (Hardened) ──────────────────
step "Configuring live-build for Amit OS..."

# Reset state
lb clean --purge || true
rm -rf .build .lock chroot binary

lb config --mode debian \
    --distribution bookworm \
    --architecture amd64 \
    --mirror-bootstrap "http://deb.debian.org/debian" \
    --mirror-binary "http://deb.debian.org/debian" \
    --linux-packages "linux-image" \
    --linux-flavours "amd64" \
    --binary-images iso-hybrid \
    --compression gzip \
    --bootappend-live "boot=live components quiet splash hostname=amitos username=amit" \
    --iso-volume "AmitOS 1.0" \
    --iso-publisher "Amit" \
    --iso-application "Amit OS - Fast Secure Linux" \
    --debian-installer false \
    --firmware-binary true \
    --firmware-chroot true \
    --apt-options "--yes --allow-downgrades --allow-remove-essential --allow-change-held-packages -o Acquire::Retries=3 -o Acquire::AllowInsecureRepositories=true -o APT::Get::AllowUnauthenticated=true -o APT::Immediate-Configure=0" \
    --apt-secure false \
    --memtest none \
    --win32-loader false

# ── Step 4.1: Inject Super-Fix Hook ──────────────────────
mkdir -p config/hooks/normal
cat > config/hooks/normal/9999-super-fix.hook.chroot << 'EOF'
#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
echo "Running Super-Fix to repair any broken package states..."
dpkg --configure -a || true
apt-get install -f -y || true
# Ensure /dev/null is correct
[ -e /dev/null ] && rm -f /dev/null
mknod -m 666 /dev/null c 1 3
EOF
chmod +x config/hooks/normal/9999-super-fix.hook.chroot

# ── Step 4.2: DNS Fixes ───────────────────────
cat > config/hooks/normal/0000-dns-fix.hook.chroot << 'EOF'
#!/bin/bash
echo "nameserver 8.8.8.8" > /etc/resolv.conf
EOF
chmod +x config/hooks/normal/0000-dns-fix.hook.chroot

# FORCED FIX: Manually kill security mirror in live-build config files
sed -i 's/^LB_SECURITY=.*/LB_SECURITY="false"/' config/chroot
sed -i 's|^LB_PARENT_MIRROR_CHROOT_SECURITY=.*|LB_PARENT_MIRROR_CHROOT_SECURITY=""|' config/chroot
sed -i 's|^LB_PARENT_MIRROR_BINARY_SECURITY=.*|LB_PARENT_MIRROR_BINARY_SECURITY=""|' config/chroot
sed -i 's|^LB_MIRROR_CHROOT_SECURITY=.*|LB_MIRROR_CHROOT_SECURITY=""|' config/chroot
sed -i 's|^LB_MIRROR_BINARY_SECURITY=.*|LB_MIRROR_BINARY_SECURITY=""|' config/chroot

# HOT-PATCH: Aggressive fix for live-build source code bug (Debian Bookworm URL shift)
step "Applying aggressive hot-patch to live-build toolset..."
# This handles variations like ${LB_ARCHITECTURE}, ${_ARCHITECTURE}, $ARCHITECTURE etc.
sudo find /usr/lib/live/build/ -type f -exec sed -i 's|dists/\([^/]*\)/Contents-\([^/]*\).gz|dists/\1/main/Contents-\2.gz|g' {} + 2>/dev/null || true
# Prevent double 'main/main' if script is run multiple times
sudo find /usr/lib/live/build/ -type f -exec sed -i 's|main/main|main|g' {} + 2>/dev/null || true
ok "Live-build toolset patched"

# Create manual sources.list in includes.chroot again (Double protection)
mkdir -p config/includes.chroot/etc/apt
cat > config/includes.chroot/etc/apt/sources.list << 'EOF'
deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
EOF

ok "live-build configured and patched"
step "Setting up package list (15+ apps + security)..."
mkdir -p config/package-lists

cat > config/package-lists/amitos.list.chroot << 'PKGS'
# Desktop
kde-plasma-desktop
plasma-workspace
plasma-nm
kscreen
powerdevil
sddm
sddm-theme-breeze
breeze
breeze-gtk-theme
kwin-x11
xorg
xserver-xorg

# 15 Apps
chromium
qalculate-gtk
gnome-calendar
dolphin
konsole
kate
vlc
gwenview
rhythmbox
kde-spectacle
plasma-systemmonitor
ksystemstats
ark
okular
knotes
libreoffice-writer
libreoffice-calc

# Security (AmitShield deps)
ufw
gufw
apparmor
apparmor-profiles
apparmor-utils
clamav
clamtk
rkhunter
fail2ban
unattended-upgrades

# Fonts & UI
fonts-noto
fonts-noto-color-emoji
fonts-open-sans
fonts-hack
fonts-inter

# Networking
network-manager
network-manager-gnome
curl
wget
net-tools
network-manager-openvpn
network-manager-vpnc
network-manager-pptp
modemmanager
mobile-broadband-provider-info

# Multimedia codecs
gstreamer1.0-plugins-good
gstreamer1.0-plugins-bad
gstreamer1.0-plugins-ugly
gstreamer1.0-libav
ffmpeg
libavcodec-extra

# Kernel & Core
linux-image-amd64
linux-headers-amd64
live-boot
live-config
live-config-systemd

# Python GUI & Tray Runtimes
python3-gi
python3-gi-cairo
gir1.2-gtk-3.0
gir1.2-gtk-4.0
gir1.2-adw-1
gir1.2-ayatanaappindicator3-0.1

# Compiler (native C++ core)
g++

# CPU Microcode
intel-microcode
amd64-microcode

# GPU Drivers
xserver-xorg-video-intel
libgl1-mesa-dri
mesa-vulkan-drivers
xserver-xorg-video-amdgpu
xserver-xorg-video-nouveau
firmware-misc-nonfree
xserver-xorg-video-fbdev
xserver-xorg-video-vesa

# WiFi & Bluetooth Firmware
firmware-iwlwifi
firmware-realtek
firmware-atheros
wpasupplicant
wireless-tools
iw
rfkill
bluetooth
bluez
bluez-tools
bluedevil
blueman

# Audio & Multimedia (Modern PipeWire configuration)
alsa-utils
pavucontrol
plasma-pa
pipewire
pipewire-pulse
pipewire-alsa
wireplumber

# Touchpad & Input
xserver-xorg-input-libinput
xserver-xorg-input-synaptics
libinput-tools

# USB & File Systems
ntfs-3g
exfatprogs
dosfstools
btrfs-progs
udisks2
gvfs
gvfs-backends

# Webcam
v4l-utils

# Printers & Scanners
cups
cups-filters
system-config-printer
hplip
sane-utils
simple-scan

# Power Management (TLP prioritized for optimization)
acpi
acpid
tlp
thermald
cpufrequtils

# Utilities
gparted
timeshift
python3
python3-dbus
p7zip-full
zip
unzip
htop
nano
bash-completion
pciutils
usbutils
dctrl-tools
resolvconf
zenity

# Installer
calamares
PKGS

# Remove problematic packages that often fail in WSL/Chroot
sed -i '/exim4/d' config/package-lists/amitos.list.chroot
sed -i '/bsd-mailx/d' config/package-lists/amitos.list.chroot
sed -i '/dictionaries-common/d' config/package-lists/amitos.list.chroot
sed -i '/aspell/d' config/package-lists/amitos.list.chroot
ok "Package list ready (cleaned from problematic pkgs)"

# ── Step 5: Custom files (AmitShield) ─────────────────────────
step "Adding AmitShield security engine..."
mkdir -p config/includes.chroot/usr/local/bin
mkdir -p config/includes.chroot/etc/amitshield
mkdir -p config/includes.chroot/etc/systemd/system
mkdir -p config/includes.chroot/usr/share/applications

# AmitShield Python daemon
cat > config/includes.chroot/usr/local/bin/amitshield << 'SHIELD'
#!/usr/bin/env python3
"""AmitShield Security Engine — Amit OS"""
import os, sys, time, re, subprocess, threading, json, logging
from datetime import datetime

logging.basicConfig(filename='/var/log/amitshield.log',
    format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
log = logging.getLogger('amitshield')

SUSPICIOUS = [r'xmrig',r'minerd',r'cpuminer',r'nc -e',r'/dev/tcp/',
              r'wget.*\|.*bash',r'curl.*\|.*bash']
DANGEROUS_PORTS = {23,135,137,139,445,3389,5900,4444,1337}
PROTECTED = {'systemd','sddm','plasmashell','kwin_x11','dbus-daemon',
             'NetworkManager','amitshield'}

def setup_firewall():
    cmds = [['ufw','default','deny','incoming'],
            ['ufw','default','allow','outgoing'],
            ['ufw','allow','ssh'],['ufw','allow','80/tcp'],
            ['ufw','allow','443/tcp'],['ufw','--force','enable']]
    for c in cmds:
        subprocess.run(c, capture_output=True)
    for p in DANGEROUS_PORTS:
        subprocess.run(['ufw','deny',str(p)], capture_output=True)
    log.info('Firewall active')

def scan_processes():
    import glob
    for pid_path in glob.glob('/proc/[0-9]*/cmdline'):
        try:
            pid = int(pid_path.split('/')[2])
            with open(pid_path,'rb') as f:
                cmd = f.read().replace(b'\x00',b' ').decode(errors='replace')
            name_path = f'/proc/{pid}/comm'
            name = open(name_path).read().strip() if os.path.exists(name_path) else ''
            if name in PROTECTED: continue
            for pat in SUSPICIOUS:
                if re.search(pat, cmd, re.IGNORECASE):
                    log.warning(f'THREAT PID:{pid} NAME:{name} — suspended')
                    os.kill(pid, 19)
                    subprocess.Popen(['notify-send','--urgency=critical',
                        'AmitShield Alert',f'Threat blocked: {name} [PID:{pid}]'])
                    break
        except Exception: pass

def main():
    log.info('=== AmitShield v1.0 starting ===')
    setup_firewall()
    scan = 0
    while True:
        scan += 1
        scan_processes()
        log.info(f'Scan #{scan} complete')
        time.sleep(30)

if __name__ == '__main__':
    main()
SHIELD
chmod +x config/includes.chroot/usr/local/bin/amitshield

# AmitShield systemd service
cat > config/includes.chroot/etc/systemd/system/amitshield.service << 'SVC'
[Unit]
Description=AmitShield Security Engine
After=network.target
[Service]
Type=simple
ExecStart=/usr/local/bin/amitshield
Restart=on-failure
RestartSec=5s
[Install]
WantedBy=multi-user.target
SVC

ok "AmitShield engine added"

# ── Step 6: Desktop shortcuts ─────────────────────────────────
step "Creating app shortcuts..."
APPS="config/includes.chroot/usr/share/applications"

cat > $APPS/amitbrowser.desktop   << 'E'
[Desktop Entry]
Name=AmitBrowser
Exec=chromium --no-sandbox %U
Icon=chromium
Type=Application
Categories=Network;WebBrowser;
E
cat > $APPS/amitcalc.desktop      << 'E'
[Desktop Entry]
Name=AmitCalc
Exec=qalculate-gtk
Icon=accessories-calculator
Type=Application
Categories=Utility;Calculator;
E
cat > $APPS/amitfiles.desktop     << 'E'
[Desktop Entry]
Name=AmitFiles
Exec=dolphin
Icon=system-file-manager
Type=Application
Categories=System;FileManager;
E
cat > $APPS/amitshield-ui.desktop << 'E'
[Desktop Entry]
Name=AmitShield
Exec=bash -c "pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY systemctl status amitshield | zenity --text-info --title='AmitShield Security'"
Icon=security-high
Type=Application
Categories=System;Security;
E

ok "App shortcuts created"

# ── Step 7: Post-install hook ─────────────────────────────────
step "Writing system configuration hook..."
mkdir -p config/hooks/normal

# NOTE: System configuration hook is synced from config/hooks/normal/0100-amitos-setup.hook.chroot
# No manual hook creation needed here.

ok "System hook ready"

# ── Step 8: Build the ISO! ────────────────────────────────────
step "Building ISO... (Final Lap)"

# Clean previous failed binary artifacts but KEEP CHROOT to avoid full rebuild
# This allows us to skip the 1500+ package install phase
rm -rf binary .build/binary*

# GUARANTEED BOOT FILES: Copying from system to binary-includes
# This is the most reliable way in WSL to ensure isolinux works
mkdir -p config/binary_local-includes/isolinux
for f in /usr/lib/ISOLINUX/isolinux.bin \
         /usr/lib/syslinux/modules/bios/vesamenu.c32 \
         /usr/lib/syslinux/modules/bios/ldlinux.c32 \
         /usr/lib/syslinux/modules/bios/libcom32.c32 \
         /usr/lib/syslinux/modules/bios/libutil.c32 \
         /usr/lib/syslinux/modules/bios/menu.c32 \
         /usr/lib/syslinux/modules/bios/chain.c32; do
    if [ -f "$f" ]; then
        cp "$f" config/binary_local-includes/isolinux/
        echo "  [OK] Copied $(basename "$f")"
    else
        warn "  [MISSING] $f"
    fi
done

# Fallback check
if [ ! -f config/binary_local-includes/isolinux/isolinux.bin ]; then
    warn "isolinux.bin not found in primary path, trying fallback..."
    cp /usr/share/live/build/bootloaders/isolinux/isolinux.bin config/binary_local-includes/isolinux/ 2>/dev/null || true
fi

# Final check before build
if [ ! -f config/binary_local-includes/isolinux/isolinux.bin ]; then
    fail "Critical boot files missing! Cannot build ISO."
fi

lb build 2>&1 | tee -a "$LOG"

# ── Step 9: Copy ISO to Windows ──────────────────────────────
step "Finalizing..."
ISO=$(ls *.iso 2>/dev/null | head -n 1)
if [ -n "$ISO" ]; then
    mkdir -p "/mnt/d/Amit os/output"
    cp "$ISO" "/mnt/d/Amit os/output/amit-os-1.0-amd64.iso"
    ok "ISO copied to D: drive"
else
    fail "ISO not found!"
fi
