## 2026-06-14T13:58:00Z
You are the Worker Implementer. Your working directory is d:\Amit os\.agents\teamwork_preview_worker_implement_1.
Your task is to implement the fixes for requirements R1, R2, and R3 based on the investigations of Explorer 1, 2, and 3.

Here are the specific fixes to apply:

1. **R1: Bootloader & ISO Build Fix**
   Modify `build/wsl-build.sh` (specifically Step 8) to:
   - Copy `$WSL_HOST/dummy.cpio` as `bootlogo` to the syslinux/isolinux config directories:
     - `config/bootloaders/isolinux/bootlogo`
     - `config/includes.binary/isolinux/bootlogo`
     - `config/binary_local-includes/isolinux/bootlogo`
   - Copy `config/bootloaders/isolinux/bootlogo` to `binary/isolinux/bootlogo` before running `lb build`.
   - Refer to `d:\Amit os\.agents\teamwork_preview_explorer_investigate_1\wsl-build.patch` for exact syntax.

2. **R2: Custom Applications Audit & Fix**
   - `apps/amitpaint.py`: Change lines 8-9 (or the Cairo imports) to use native `import cairo as Cairo` instead of importing from `gi.repository`.
   - `apps/amittray.py`: Wrap `gi.require_version("AppIndicator3", "0.1")` and the subsequent import within the existing `try/except` block.
   - `amitshield/amitshield-ui.py`: Fix GTK4 compatibility. Modify lines 34-35 (or the `add_provider` calls on StyleContext) to use `Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)` and `self.add_css_class("threat-card")` instead of `self.get_style_context().add_provider(...)` and `add_class`.
   - `core/amitshield_core.cpp`: Move the `chmod(SOCKET_PATH, 0666)` call to execute *after* the `bind` call (around lines 454-457).

3. **R3: Hook and Package Validation**
   - In `build/wsl-build.sh`, `build/build.sh`, and `build/prepare-offline.sh`, add `--archive-areas "main contrib non-free non-free-firmware"` to the `lb config` call.
   - In `config/hooks/normal/0400-branding.hook.chroot`:
     - Replace the `kdeglobals` writing block with a unified version that includes `ColorScheme=BreezeDark` and `Theme=breeze-dark` (as detailed in Explorer 3's handoff).
     - Ensure the destination directory `/usr/share/wallpapers/Next/contents/images/` exists (`mkdir -p`) before creating the wallpaper symlink on line 76.
     - Remove the `kdeglobals` writing block from `config/hooks/normal/0100-amitos-setup.hook.chroot` to avoid theme overwrite conflicts.
   - In `config/hooks/normal/0200-amit-apps.hook.chroot`:
     - Add `make_desktop "amittray" "AmitTray" "System Tray Utilities" "preferences-desktop-notification" "Utility"` to the desktop entries generation so that `amittray.desktop` is correctly created and autostarts.
   - In `config/package-lists/amitos.list.chroot`:
     - Ensure `g++` is present in the package list under the compilers section.
   - In `config/hooks/normal/9999-super-fix.hook.chroot`:
     - Ensure `/dev/null` is only recreated if it doesn't already exist:
       ```bash
       if [ ! -e /dev/null ]; then
           mknod -m 666 /dev/null c 1 3 || true
       fi
       ```
       (do not delete it).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

After applying all fixes, please run syntax and compilation checks (`python3 -m py_compile`) on all python scripts under `apps/` and `amitshield/` to verify correctness. Verify that `g++` is in the package list. Document all modified files and the validation commands you ran.
Write your handoff report to handoff.md in your working directory and notify the parent.
