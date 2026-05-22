# 🖥️ Amit OS — Your Linux, Your Rules

> **Fast. Secure. Beautiful. Built for Amit.**

AmitOS is a custom Linux distribution based on **Debian 12 (Bookworm)**, designed to deliver a premium **Windows-like experience** with the power, speed, and security of Linux.

---

## 🌟 Key Features

| Feature | Details |
|---|---|
| **Base** | Debian 12 Bookworm (Stable) |
| **Desktop** | KDE Plasma 5 (Windows-like layout) |
| **Kernel** | Linux 6.x (Latest Stable) |
| **Architecture** | x86_64 (64-bit) |
| **ISO Size** | ~2.5 GB (Live + Installer) |
| **RAM Required** | Minimum 2 GB (4 GB recommended) |
| **Security Engine** | AmitShield v1.0 |

---

## 🛡️ AmitShield — Security Engine

AmitShield is the built-in security engine of Amit OS. It provides:

- 🔥 **Real-time Firewall** (UFW + custom rules)
- 🔍 **Process Monitor** (detects malicious processes)
- 🔐 **AppArmor** (mandatory access control)
- 📡 **Network Guardian** (blocks suspicious traffic)
- 🧹 **Auto-cleaner** (removes temp files & junk)
- 📊 **Security Dashboard** (GUI monitor)
- ⚠️ **Intrusion Detection** (alerts on threats)
- 🔄 **Auto Security Updates**

---

## 📦 Pre-installed Apps (15+)

| # | App Name | Description |
|---|---|---|
| 1 | **AmitBrowser** | Chromium-based web browser |
| 2 | **AmitCalc** | Scientific calculator |
| 3 | **AmitCalendar** | Calendar & events manager |
| 4 | **AmitFiles** | File manager (Dolphin) |
| 5 | **AmitTerminal** | Terminal emulator |
| 6 | **AmitText** | Text & code editor |
| 7 | **AmitMedia** | Video player (VLC) |
| 8 | **AmitPhotos** | Image viewer |
| 9 | **AmitMusic** | Music player |
| 10 | **AmitCapture** | Screenshot tool |
| 11 | **AmitMonitor** | System resource monitor |
| 12 | **AmitArchive** | Zip/archive manager |
| 13 | **AmitPDF** | PDF viewer |
| 14 | **AmitNotes** | Sticky notes |
| 15 | **AmitShield UI** | Security dashboard |
| 16 | **AmitSettings** | System control panel |
| 17 | **AmitStore** | App store |

---

## 🚀 Building the ISO

### Prerequisites (run in WSL2 or native Linux/Debian):

```bash
sudo apt-get install -y live-build debootstrap squashfs-tools xorriso
```

### Build Steps:

```bash
# 1. Clone or copy AmitOS folder to your Linux system
# 2. Run the build script
cd AmitOS
chmod +x build/build.sh
sudo ./build/build.sh

# Output: output/amit-os-1.0-amd64.iso
```

---

## 📁 Project Structure

```
AmitOS/
├── build/              # Build scripts
├── config/             # live-build configuration
│   ├── package-lists/  # App packages to install
│   ├── hooks/          # Pre/post install scripts
│   └── includes.chroot/# Custom files in rootfs
├── amitshield/         # Security Engine source
├── apps/               # Custom app scripts
├── themes/             # AmitOS visual theme
├── installer/          # Calamares installer config
├── branding/           # Logo, wallpaper, boot splash
└── docs/               # Documentation
```

---

## 👨‍💻 Developer

**Amit** — Creator & Architect of Amit OS

---

## 📜 License

MIT License — Open Source, Free Forever.
