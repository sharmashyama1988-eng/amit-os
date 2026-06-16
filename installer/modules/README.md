# AmitOS Installer — Calamares Modules

This directory contains custom Calamares installer module configurations and scripts for **AmitOS**.

---

## Directory Structure

```
installer/
└── modules/
    ├── amitos-post-install.sh   # Post-installation shell script
    ├── finished.conf            # Calamares 'finished' module config
    ├── welcomeq.conf            # Calamares 'welcomeq' module config
    └── README.md                # This file
```

---

## Files

### `amitos-post-install.sh`

A Bash script executed by the Calamares **shellprocess** module inside the target system's chroot environment after packages are installed.

**What it does (in order):**

| Step | Action |
|------|--------|
| 1 | Enables `amitshield.service` via `systemctl enable` |
| 2 | Sets the default Plymouth boot-splash theme to `amitos` (falls back to `spinner`) |
| 3 | Enables UFW firewall with `deny incoming` / `allow outgoing` / SSH allowed |
| 4 | Creates standard XDG user directories (`Desktop`, `Documents`, `Downloads`, etc.) for the first non-root user |
| 5 | Sets the system hostname to `amitos` and updates `/etc/hosts` |

**Usage in `settings.conf`:**

```yaml
- shellprocess:
    script:
      - "/usr/lib/calamares/modules/amitos-post-install.sh"
```

> [!IMPORTANT]
> The script must be installed into the live ISO at `/usr/lib/calamares/modules/` (or your configured module path) so it is accessible during the install.

---

### `welcomeq.conf`

Configuration for the Calamares **welcomeq** Qt-based welcome screen module.

**Key settings:**

| Key | Value | Purpose |
|-----|-------|---------|
| `showSupportUrl` | `true` | Shows "Get Support" button |
| `showKnownIssuesUrl` | `true` | Shows "Known Issues" button |
| `showReleaseNotesUrl` | `true` | Shows "Release Notes" button |
| `requiredStorage` | `10` GiB | Minimum free disk space check |
| `requiredRam` | `2.0` GiB | Minimum RAM check |

Update the `supportUrl`, `knownIssuesUrl`, and `releaseNotesUrl` values to point to your live documentation URLs before building the ISO.

---

### `finished.conf`

Configuration for the Calamares **finished** module — the last page shown after installation completes.

**Key settings:**

| Key | Value | Purpose |
|-----|-------|---------|
| `restartNowEnabled` | `true` | Shows the "Restart now" checkbox |
| `restartNowChecked` | `true` | Checkbox is ticked by default |
| `restartNowCommand` | `systemctl reboot` | Command to reboot the machine |

---

## Calamares Integration

### 1. Copy modules to the live ISO

Place this `modules/` directory content into your ISO build's Calamares modules path, typically:

```
/etc/calamares/modules/
```

or

```
/usr/lib/calamares/modules/
```

### 2. Reference in `settings.conf`

Ensure your `settings.conf` sequence references these modules:

```yaml
sequence:
  - show:
      - welcomeq
  - exec:
      - shellprocess        # runs amitos-post-install.sh
  - show:
      - finished
```

### 3. Make the post-install script executable

```bash
chmod +x /usr/lib/calamares/modules/amitos-post-install.sh
```

---

## Customisation

| What to change | Where |
|----------------|-------|
| Hostname | `amitos-post-install.sh` — Step 5 |
| Plymouth theme name | `amitos-post-install.sh` — Step 2 |
| Firewall rules | `amitos-post-install.sh` — Step 3 |
| Support / notes URLs | `welcomeq.conf` |
| Restart command | `finished.conf` |

---

## License

These files are part of the AmitOS project and are distributed under the **MIT License** unless otherwise noted.
