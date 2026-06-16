# AmitOS-Dark — KDE Plasma Theme

A sleek, modern **dark Plasma theme** crafted for the AmitOS desktop experience.  
Built for clarity, performance, and premium aesthetics.

---

## 📁 Theme Structure

```
AmitOS-Dark/
├── colors/                         # KDE color scheme files
├── contents/
│   ├── defaults                    # Default wallpaper, colorScheme, lookAndFeel mappings
│   ├── layouts/
│   │   └── org.kde.plasma.desktop-layout.js   # Default panel layout
│   └── plasmoids/                  # Custom Plasma widgets (if any)
├── metadata.desktop                # Legacy KDE metadata (for older Plasma)
├── metadata.json                   # Modern KDE metadata (Plasma 5.27+)
└── README.md
```

---

## 🚀 Installation

### Method 1 — KDE System Settings (Recommended)

1. Open **System Settings → Appearance → Global Theme**
2. Click **Get New Global Themes…**
3. Or click **Install from File…** and select this folder/archive

### Method 2 — Manual Installation

```bash
# Copy theme to your local Plasma themes directory
cp -r AmitOS-Dark ~/.local/share/plasma/desktoptheme/

# Apply via plasmapkg2
plasmapkg2 --install ~/.local/share/plasma/desktoptheme/AmitOS-Dark
```

### Method 3 — From the AmitOS repository root

```bash
# Clone the repo (if not already done)
git clone https://github.com/sharmashyama1988-eng/amit-os.git
cd amit-os

# Install the theme
plasmapkg2 --install themes/AmitOS-Dark
```

---

## 🎨 Applying the Theme

After installation, apply via:

```bash
# Apply Look & Feel
lookandfeeltool --apply org.kde.breezedark.desktop

# Or through KDE System Settings
# System Settings → Appearance → Global Theme → AmitOS Dark
```

---

## 🔄 Updating

```bash
plasmapkg2 --upgrade themes/AmitOS-Dark
```

---

## 🗑️ Uninstalling

```bash
plasmapkg2 --remove AmitOS-Dark
```

---

## ⚙️ Default Panel Layout

The included layout script (`contents/layouts/org.kde.plasma.desktop-layout.js`) creates:

| Widget | Position |
|---|---|
| 🚀 Kickoff App Launcher | Left |
| 📋 Task Manager | Center |
| ⬛ Flexible Spacer | — |
| 🔔 System Tray (Network, Volume, Battery, Bluetooth) | Right |
| 🕐 Digital Clock (24h + Date) | Right |
| 🖥️ Show Desktop | Far Right |

---

## 📋 Requirements

- KDE Plasma **5.20** or newer (Plasma 6 compatible)
- Qt **5.15** or newer
- `plasmapkg2` utility (part of `plasma-framework`)

---

## 📄 License

GPL-2.0-or-later — see the root `LICENSE` file for details.

---

## 🤝 Contributing

Pull requests are welcome!  
Please open an issue first to discuss any major changes.

> Part of the **AmitOS** project — [github.com/sharmashyama1988-eng/amit-os](https://github.com/sharmashyama1988-eng/amit-os)
