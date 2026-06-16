#!/usr/bin/env bash
# =============================================================================
# AmitOS Post-Installation Script
# Calamares shellprocess module hook
# Runs inside the target system chroot after package installation
# =============================================================================

set -euo pipefail

LOG_FILE="/var/log/amitos-post-install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================================="
echo " AmitOS Post-Installation Script"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================="

# ---------------------------------------------------------------------------
# 1. Enable AmitShield service
# ---------------------------------------------------------------------------
echo "[1/5] Enabling AmitShield security service..."
if systemctl list-unit-files | grep -q "amitshield.service"; then
    systemctl enable amitshield.service
    echo "      ✔ amitshield.service enabled."
else
    echo "      ⚠ amitshield.service not found — skipping."
fi

# ---------------------------------------------------------------------------
# 2. Set default Plymouth boot splash theme
# ---------------------------------------------------------------------------
echo "[2/5] Setting default Plymouth theme to 'amitos'..."
if command -v plymouth-set-default-theme &>/dev/null; then
    if plymouth-set-default-theme --list | grep -q "amitos"; then
        plymouth-set-default-theme -R amitos
        echo "      ✔ Plymouth theme set to 'amitos' and initramfs rebuilt."
    else
        echo "      ⚠ Plymouth theme 'amitos' not found — applying 'spinner' fallback."
        plymouth-set-default-theme -R spinner
    fi
else
    echo "      ⚠ plymouth-set-default-theme not available — skipping."
fi

# ---------------------------------------------------------------------------
# 3. Enable UFW firewall with sensible defaults
# ---------------------------------------------------------------------------
echo "[3/5] Enabling UFW firewall..."
if command -v ufw &>/dev/null; then
    # Deny all incoming, allow all outgoing (safe defaults)
    ufw default deny incoming
    ufw default allow outgoing

    # Allow SSH so the user is not locked out
    ufw allow ssh

    # Enable non-interactively
    ufw --force enable
    systemctl enable ufw.service
    echo "      ✔ UFW enabled (deny incoming / allow outgoing / SSH allowed)."
else
    echo "      ⚠ ufw not found — skipping firewall setup."
fi

# ---------------------------------------------------------------------------
# 4. Create default user XDG directories
# ---------------------------------------------------------------------------
echo "[4/5] Creating default user directories..."
# Determine the first non-root, non-system user created during install
TARGET_USER=$(awk -F: '$3 >= 1000 && $1 != "nobody" {print $1; exit}' /etc/passwd 2>/dev/null || true)

if [[ -n "$TARGET_USER" ]]; then
    TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
    echo "      Target user : $TARGET_USER"
    echo "      Home dir    : $TARGET_HOME"

    XDG_DIRS=(
        Desktop
        Documents
        Downloads
        Music
        Pictures
        Public
        Templates
        Videos
    )

    for dir in "${XDG_DIRS[@]}"; do
        mkdir -p "$TARGET_HOME/$dir"
    done

    chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME"
    echo "      ✔ XDG directories created and ownership set."

    # Run xdg-user-dirs-update as the target user if available
    if command -v xdg-user-dirs-update &>/dev/null; then
        su -c "xdg-user-dirs-update" "$TARGET_USER" || true
        echo "      ✔ xdg-user-dirs-update ran successfully."
    fi
else
    echo "      ⚠ No non-root user found — skipping directory creation."
fi

# ---------------------------------------------------------------------------
# 5. Set system hostname to 'amitos'
# ---------------------------------------------------------------------------
echo "[5/5] Setting hostname to 'amitos'..."
if command -v hostnamectl &>/dev/null; then
    hostnamectl set-hostname amitos
    echo "      ✔ Hostname set to 'amitos' via hostnamectl."
else
    echo "amitos" > /etc/hostname
    echo "      ✔ Hostname set to 'amitos' via /etc/hostname."
fi

# Update /etc/hosts to reference the new hostname
if grep -q "127.0.1.1" /etc/hosts; then
    sed -i "s/^127\.0\.1\.1.*/127.0.1.1\tamitos/" /etc/hosts
else
    echo -e "127.0.1.1\tamitos" >> /etc/hosts
fi
echo "      ✔ /etc/hosts updated."

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo " AmitOS post-installation complete!"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================="

exit 0
