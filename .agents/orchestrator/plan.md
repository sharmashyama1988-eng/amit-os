# Implementation Plan: Amit OS Repair and Build

## Objective
Scan, repair, and generate a bootable Debian-based live ISO for Amit OS by fixing bootloader, custom apps, hooks, and package configuration.

## Milestones

### Milestone 1: Investigation and Exploration
- **Goal**: Identify all syntax, library import, PyGI/GTK3 compatibility, and elevation bugs in the 15+ python apps under `apps/` and `amitshield/`. Analyze hook script errors and syslinux/isolinux bootlogo config.
- **Verification**: Exploration report containing findings, file paths, and recommended fixes.

### Milestone 2: Bootloader configuration (R1)
- **Goal**: Copy `dummy.cpio` as `bootlogo` to syslinux/isolinux config directories (`config/bootloaders/isolinux/bootlogo`, `config/includes.binary/isolinux/bootlogo`, and `config/binary_local-includes/isolinux/bootlogo`) and update `build/wsl-build.sh` if needed to ensure proper copy during build.
- **Verification**: Verify files exist in expected locations before/during build.

### Milestone 3: Custom Applications Audit & Fix (R2)
- **Goal**: Fix all 15+ custom applications under `apps/` and the `amitshield/` daemon and UI to run correctly. Resolve missing imports, syntax errors, PyGI/GTK3 compatibility issues, and elevation handling.
- **Verification**: Compilation check (`python3 -m py_compile`) passes for all python files, and syntax validation.

### Milestone 4: Hook and Package Validation (R3)
- **Goal**: Validate live-build hooks (`config/hooks/normal/*.chroot`) and package lists to remove broken or conflicting packages.
- **Verification**: Clean syntax and path verification.

### Milestone 5: E2E Build and ISO Generation
- **Goal**: Run the full ISO build process inside WSL2 to verify successful compilation and ISO generation (`amit-os-1.0-amd64.iso` in the output folder).
- **Verification**: The `wsl-build.sh` script executes successfully and output ISO is generated.

### Milestone 6: Adversarial Coverage Hardening
- **Goal**: Run adversarial test verification to identify any gaps or hidden bugs.
- **Verification**: Complete validation by Forensic Auditor.
