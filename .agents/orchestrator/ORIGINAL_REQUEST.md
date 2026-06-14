# Original User Request

## Initial Request — 2026-06-14T13:49:13Z

Scan, repair, and build Amit OS, a Debian-based custom Linux distribution. The objective is to identify and resolve all system bugs, package conflicts, security vulnerabilities, GUI application crashes, and bootloader configuration failures to ensure a successful release.

Working directory: d:/Amit os
Integrity mode: development

## Requirements

### R1. Bootloader and ISO Build Fix
Resolve the syslinux/isolinux bootloader compilation errors during the live-build process (specifically, `/usr/lib/live/build/lb_binary_syslinux: cannot open binary/isolinux/bootlogo: No such file`). Ensure the bootlogo dummy cpio or relevant files are located in `config/bootloaders/isolinux/` or `config/binary_local-includes/isolinux/` so they are copied correctly during the live-build process.

### R2. Custom Applications Audit
Ensure all 15+ custom applications under `apps/` and the `amitshield/` daemon and UI run correctly without crashing. Check for missing imports, syntax errors, PyGI/GTK3 compatibility, and proper elevation handling.

### R3. Hook and Package Validation
Validate all live-build hook scripts (`config/hooks/normal/*.chroot`) and package lists to remove any conflicting or broken packages that could interrupt the debootstrap or apt stages.

## Acceptance Criteria

### Build Success
- [ ] The `lb build` (or `wsl-build.sh`) process completes successfully without exit errors.
- [ ] A bootable hybrid ISO (`amit-os-1.0-amd64.iso`) is successfully generated in the output folder.

### Application Integrity
- [ ] All custom python files compile correctly without any syntax errors or missing library imports.
- [ ] The AmitShield service starts and runs successfully as a systemd daemon.
