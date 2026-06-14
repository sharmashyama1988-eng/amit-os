# Project: Amit OS Build and Repair

## Architecture
- **Host System**: Windows with WSL2 (Ubuntu environment).
- **Build System**: Debian Live-Build (`lb build` via `build/wsl-build.sh`).
- **Custom Apps**: 15+ Python apps (under `apps/`) using PyGI/GTK3, plus `amitshield/` daemon and UI.
- **Hook Scripts**: Post-installation hooks under `config/hooks/normal/` configured to install apps, drivers, branding, and compile native C++ libraries.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Investigation | Scan and report syntax/import/bootloader bugs | none | DONE |
| 2 | R1 Bootloader Fix | Relocate bootlogo dummy cpio to config/bootloaders/isolinux | M1 | IN_PROGRESS |
| 3 | R2 App Fixes | Repair 15+ apps & AmitShield daemon & UI compatibility | M1 | IN_PROGRESS |
| 4 | R3 Hook Validation | Validate hooks and cleanup package lists | M1 | IN_PROGRESS |
| 5 | Build ISO | Run `wsl-build.sh` and output iso | M2, M3, M4 | PLANNED |
| 6 | Audit/Hardening | Forensic audit and E2E verification | M5 | PLANNED |

## Interface Contracts
- **AmitShield Daemon ↔ UI**: Communication via `/var/log/amitshield.log` (read by UI) and systemd status.
- **Live-Build ↔ Configuration**: Input files must be located in `config/` directory.
