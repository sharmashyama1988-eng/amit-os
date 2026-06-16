# AmitOS Plymouth Boot Splash Theme

A polished boot-splash theme for **AmitOS**, built with the Plymouth `script` module.

---

## Theme Files

| File | Purpose |
|------|---------|
| `amitos.plymouth` | Plymouth theme descriptor |
| `amitos.script` | Main animation script |
| `amitos-wallpaper.png` | Full-screen background wallpaper *(provide your own)* |
| `amitos-logo.png` | Centre-screen logo *(provide your own)* |

> **Note:** The two PNG assets are referenced by the script but are not committed to this repository. Place them in the theme installation directory before testing.

---

## Installation

### 1. Copy theme files to the Plymouth themes directory

```bash
sudo mkdir -p /usr/share/plymouth/themes/amitos
sudo cp amitos.plymouth amitos.script \
        amitos-wallpaper.png amitos-logo.png \
        /usr/share/plymouth/themes/amitos/
```

### 2. Set AmitOS as the default Plymouth theme

```bash
sudo plymouth-set-default-theme --rebuild-initrd amitos
```

`--rebuild-initrd` regenerates the initramfs so the theme is embedded and visible as early as possible during boot.

### 3. Verify the theme was registered

```bash
plymouth-set-default-theme --list | grep amitos
```

---

## Testing Without Rebooting

Plymouth provides a built-in test mode that runs the splash inside your current desktop session.

### Quick graphical preview

```bash
sudo plymouthd --no-daemon --debug &
sleep 1
sudo plymouth --show-splash
sleep 5
sudo plymouth --update=testing
sleep 2
sudo plymouth --quit
```

### Simulate full boot progress (0 → 100 %)

```bash
sudo plymouthd --no-daemon &
sudo plymouth --show-splash
for i in $(seq 0 10 100); do
    sudo plymouth --update="Loading… ${i}%"
    sleep 0.4
done
sudo plymouth --quit
```

### Test the password prompt

```bash
sudo plymouthd --no-daemon &
sudo plymouth --show-splash
sudo plymouth --ask-for-password
sudo plymouth --quit
```

---

## Uninstalling

```bash
# Switch back to the distro default theme first
sudo plymouth-set-default-theme --rebuild-initrd default

# Then remove AmitOS theme files
sudo rm -rf /usr/share/plymouth/themes/amitos
```

---

## Customisation

| What to change | Where |
|----------------|-------|
| Accent colour (progress bar / spinner) | `amitos.script` → `new_fill.Fill(r, g, b, a)` |
| Bar size & position | `BAR_WIDTH`, `BAR_HEIGHT`, `BAR_Y` constants |
| Number of scrolling log lines | `LOG_LINES` constant |
| Font sizes | `MSG_FONT_SIZE`, `LOG_FONT` constants |
| Wallpaper / logo | Replace PNG assets in the theme directory |

---

## Requirements

- Plymouth ≥ **0.9.4** (ships with most modern distros)
- Plymouth `script` plugin: `libply-splash-graphics`, `plymouth-plugin-script`
- On Debian/Ubuntu: `sudo apt install plymouth-themes`
- On Fedora/RHEL:  `sudo dnf install plymouth-plugin-script`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Blank screen at boot | Ensure `quiet splash` is in your kernel command line (e.g. in `/etc/default/grub`) |
| Theme not found | Run `sudo update-initramfs -u` (Debian) or `sudo dracut -f` (Fedora) after installing |
| Images not loading | Check file paths — images must be in the same directory as the `.script` file |
| Low resolution splash | Add `GRUB_GFXMODE=1920x1080` to `/etc/default/grub` then `sudo update-grub` |
