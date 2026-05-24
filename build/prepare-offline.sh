#!/bin/bash
# ============================================================
#  AMIT OS — Pre-Download / Offline Preparation Script
#  Populates the build cache so no internet is needed during build.
# ============================================================

set -e
BOLD='\033[1m'; GREEN='\033[0;32m'; RED='\033[0;31m'
YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

WIN_CACHE="/mnt/d/Amit os/cache"
BUILD_DIR="/tmp/amitos-offline-prep"

echo -e "${CYAN}${BOLD}Preparing Offline Cache for Amit OS...${NC}"

# Install dependencies first
step() { echo -e "\n${CYAN}${BOLD}[STEP] $1${NC}"; }

step "Fixing WSL Network (MTU & Mirrors)..."
# MTU Fix (Crucial for WSL2 networking issues)
ip link set dev eth0 mtu 1350 2>/dev/null || true

# DNS Fix
echo "nameserver 8.8.8.8" > /etc/resolv.conf
# Disable IPv6
sysctl -w net.ipv6.conf.all.disable_ipv6=1 >/dev/null 2>&1 || true

# Switch to a more reliable mirror (mirrors.kernel.org)
sed -i 's/archive.ubuntu.com/mirrors.kernel.org/g' /etc/apt/sources.list.d/ubuntu.sources 2>/dev/null || true
sed -i 's/security.ubuntu.com/mirrors.kernel.org/g' /etc/apt/sources.list.d/ubuntu.sources 2>/dev/null || true

apt-get update -qq || apt-get update --fix-missing -qq

step "Installing build dependencies in Ubuntu..."
apt-get install -y --fix-missing --no-install-recommends \
    live-build live-config live-boot \
    debootstrap squashfs-tools xorriso \
    grub-efi-amd64-bin grub-pc-bin mtools \
    syslinux syslinux-common isolinux \
    wget curl git python3

# Ensure cache dir exists on Windows
mkdir -p "$WIN_CACHE"

# Setup temp build dir
sudo rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Symlink cache to Windows drive
mkdir -p cache
sudo mount --bind "$WIN_CACHE" cache

# Run lb config (must match wsl-build.sh exactly)
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
    --apt-options "--yes --allow-downgrades --allow-remove-essential --allow-change-held-packages -o Acquire::Retries=3" \
    --memtest none \
    --win32-loader false

# Add the package list
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

echo -e "${YELLOW}Starting download phase... This will take time.${NC}"

# In live-build 3.0, we run the stages to populate the cache.
# It will download everything into the 'cache/' directory which is bind-mounted to D:\Amit os\cache

# 1. Populate bootstrap cache
lb bootstrap

# 2. Populate chroot cache (this downloads all packages in your .list)
lb chroot

echo -e "${GREEN}✓ All packages downloaded and cached in D:\\Amit os\\cache${NC}"

# Cleanup
sudo umount cache
sudo rm -rf "$BUILD_DIR"
