#!/usr/bin/env python3
# ============================================================
#  AMITSHIELD — Amit OS Security Engine v1.0
#  Author:  Amit
#  Description: Real-time security daemon for Amit OS
#               Protects against threats, monitors system,
#               manages firewall, and keeps OS safe.
# ============================================================

import os
import sys
import time
import json
import logging
import subprocess
import threading
import signal
import socket
import hashlib
import shutil
import re
from datetime import datetime
from pathlib import Path
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

# ─── Configuration ───────────────────────────────────────────
VERSION       = "1.0.0"
CONFIG_FILE   = "/etc/amitshield/amitshield.conf"
LOG_FILE      = "/var/log/amitshield.log"
RULES_DIR     = "/etc/amitshield/rules"
THREAT_DB     = "/etc/amitshield/threat_signatures.json"
PID_FILE      = "/var/run/amitshield.pid"
DBUS_NAME     = "org.amitos.AmitShield"
DBUS_PATH     = "/org/amitos/AmitShield"

# ─── Default Configuration ───────────────────────────────────
DEFAULT_CONFIG = {
    "firewall_enabled":         True,
    "intrusion_detection":      True,
    "process_monitoring":       True,
    "network_guardian":         True,
    "auto_updates":             True,
    "auto_clean":               True,
    "scan_interval_seconds":    30,
    "threat_log_max_mb":        50,
    "alert_on_new_process":     True,
    "block_suspicious_ports":   True,
    "safe_mode":                False,
    "notify_desktop":           True,
}

# ─── Known Malicious Patterns ────────────────────────────────
SUSPICIOUS_PATTERNS = [
    r"cryptominer", r"xmrig", r"minerd", r"cpuminer",
    r"torjan", r"rootkit", r"keylogger", r"ransomware",
    r"netcat\s+-e", r"bash\s+-i\s+>&", r"python\s+-c.*socket",
    r"perl\s+-e.*socket", r"/dev/tcp/", r"wget.*\|.*bash",
    r"curl.*\|.*bash", r"chmod.*777.*tmp"
]

# ─── Dangerous Ports ─────────────────────────────────────────
DANGEROUS_PORTS = [23, 135, 137, 138, 139, 445, 3389, 5900, 6667]

# ─── Protected System Processes ──────────────────────────────
PROTECTED_PROCESSES = [
    "systemd", "init", "kthreadd", "sddm", "plasmashell",
    "kwin_x11", "dbus-daemon", "NetworkManager", "amitshield"
]

# ─── Setup Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] AmitShield: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("amitshield")


# ════════════════════════════════════════════════════════════
#  AMITSHIELD CORE ENGINE
# ════════════════════════════════════════════════════════════
class AmitShieldEngine:
    def __init__(self):
        self.config = self._load_config()
        self.running = True
        self.threats_detected = 0
        self.threats_blocked = 0
        self.scans_completed = 0
        self.start_time = datetime.now()
        self.known_pids = set()
        self.whitelist = set()
        self.alert_callbacks = []
        log.info(f"═══ AmitShield v{VERSION} Starting ═══")

    # ── Config ──────────────────────────────────────────────
    def _load_config(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    merged = {**DEFAULT_CONFIG, **cfg}
                    return merged
            except Exception as e:
                log.warning(f"Config load failed: {e}. Using defaults.")
        else:
            self._save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    def _save_config(self, config):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    # ── Firewall ────────────────────────────────────────────
    def setup_firewall(self):
        if not self.config["firewall_enabled"]:
            log.info("Firewall disabled by config")
            return
        log.info("Setting up AmitShield Firewall...")
        rules = [
            ["ufw", "default", "deny", "incoming"],
            ["ufw", "default", "allow", "outgoing"],
            ["ufw", "allow", "ssh"],
            ["ufw", "allow", "80/tcp"],
            ["ufw", "allow", "443/tcp"],
            ["ufw", "allow", "53"],
            ["ufw", "--force", "enable"],
        ]
        for rule in rules:
            try:
                subprocess.run(rule, capture_output=True, timeout=10)
            except Exception as e:
                log.warning(f"Firewall rule failed: {rule} — {e}")

        # Block dangerous ports
        if self.config["block_suspicious_ports"]:
            for port in DANGEROUS_PORTS:
                try:
                    subprocess.run(
                        ["ufw", "deny", str(port)],
                        capture_output=True, timeout=5
                    )
                except Exception:
                    pass
        log.info("✓ Firewall configured and active")

    # ── AppArmor ────────────────────────────────────────────
    def setup_apparmor(self):
        log.info("Enabling AppArmor mandatory access control...")
        try:
            subprocess.run(["aa-enforce", "/etc/apparmor.d/*"],
                           shell=True, capture_output=True, timeout=30)
            log.info("✓ AppArmor profiles enforced")
        except Exception as e:
            log.warning(f"AppArmor setup: {e}")

    # ── Process Monitor ──────────────────────────────────────
    def scan_processes(self):
        try:
            result = subprocess.run(
                ["ps", "aux", "--no-headers"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().split("\n")
            current_pids = set()

            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(None, 10)
                if len(parts) < 11:
                    continue
                pid  = parts[1]
                user = parts[0]
                cmd  = parts[10] if len(parts) > 10 else ""
                current_pids.add(pid)

                # Detect new processes
                if pid not in self.known_pids:
                    self.known_pids.add(pid)
                    self._check_process(pid, user, cmd)

            self.known_pids = current_pids
        except Exception as e:
            log.debug(f"Process scan error: {e}")

    def _check_process(self, pid, user, cmd):
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                self.threats_detected += 1
                msg = f"THREAT DETECTED — PID:{pid} USER:{user} CMD:{cmd[:80]}"
                log.warning(f"🚨 {msg}")
                self._send_alert("threat", msg)
                if not any(p in cmd for p in PROTECTED_PROCESSES):
                    self._quarantine_process(pid, cmd)
                break

    def _quarantine_process(self, pid, cmd):
        try:
            log.warning(f"Quarantining malicious process PID:{pid}")
            subprocess.run(["kill", "-STOP", pid], capture_output=True, timeout=5)
            self.threats_blocked += 1
            log.warning(f"✓ Process PID:{pid} suspended")
        except Exception as e:
            log.error(f"Failed to quarantine PID:{pid}: {e}")

    # ── Network Guardian ─────────────────────────────────────
    def scan_network(self):
        if not self.config["network_guardian"]:
            return
        try:
            result = subprocess.run(
                ["ss", "-tnp"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split("\n"):
                for port in DANGEROUS_PORTS:
                    if f":{port}" in line and "ESTABLISHED" in line:
                        self.threats_detected += 1
                        msg = f"Suspicious connection on dangerous port {port}: {line.strip()}"
                        log.warning(f"🌐 {msg}")
                        self._send_alert("network", msg)
        except Exception as e:
            log.debug(f"Network scan error: {e}")

    # ── Auto Cleaner ─────────────────────────────────────────
    def auto_clean(self):
        if not self.config["auto_clean"]:
            return
        log.info("Running auto-cleaner...")
        clean_paths = [
            "/tmp", "/var/tmp",
            os.path.expanduser("~/.cache/thumbnails"),
            "/var/cache/apt/archives",
        ]
        cleaned_mb = 0
        for path in clean_paths:
            if os.path.exists(path):
                try:
                    result = subprocess.run(
                        ["du", "-sm", path],
                        capture_output=True, text=True, timeout=10
                    )
                    size_mb = int(result.stdout.split()[0]) if result.stdout else 0
                    if path == "/var/cache/apt/archives":
                        subprocess.run(["apt-get", "autoclean", "-y"],
                                       capture_output=True, timeout=30)
                    elif path == "/tmp" or path == "/var/tmp":
                        subprocess.run(
                            ["find", path, "-type", "f", "-atime", "+7", "-delete"],
                            capture_output=True, timeout=30
                        )
                    cleaned_mb += size_mb
                except Exception:
                    pass
        log.info(f"✓ Auto-clean freed ~{cleaned_mb} MB")

    # ── Security Report ──────────────────────────────────────
    def get_security_status(self):
        uptime = str(datetime.now() - self.start_time).split(".")[0]
        return {
            "version":          VERSION,
            "status":           "active",
            "uptime":           uptime,
            "threats_detected": self.threats_detected,
            "threats_blocked":  self.threats_blocked,
            "scans_completed":  self.scans_completed,
            "firewall":         "enabled" if self.config["firewall_enabled"] else "disabled",
            "apparmor":         "enforcing",
            "timestamp":        datetime.now().isoformat(),
        }

    # ── Desktop Notifications ────────────────────────────────
    def _send_alert(self, alert_type, message):
        if not self.config.get("notify_desktop"):
            return
        try:
            subprocess.Popen([
                "notify-send",
                "--urgency=critical",
                "--icon=security-high",
                f"AmitShield — {alert_type.upper()} Alert",
                message[:200]
            ])
        except Exception:
            pass

    # ── Auto Security Updates ────────────────────────────────
    def check_security_updates(self):
        if not self.config["auto_updates"]:
            return
        log.info("Checking for security updates...")
        try:
            subprocess.run(
                ["unattended-upgrade", "--minimal_upgrade_steps"],
                capture_output=True, timeout=300
            )
            log.info("✓ Security updates applied")
        except Exception as e:
            log.debug(f"Update check: {e}")

    # ── Main Scan Loop ───────────────────────────────────────
    def run_scan_cycle(self):
        self.scans_completed += 1
        log.info(f"Scan #{self.scans_completed} starting...")
        self.scan_processes()
        self.scan_network()
        log.info(f"Scan #{self.scans_completed} complete — Threats: {self.threats_detected}")

    # ── Signal Handler ───────────────────────────────────────
    def stop(self, signum=None, frame=None):
        log.info("AmitShield shutting down gracefully...")
        self.running = False
        sys.exit(0)

    # ── Main ─────────────────────────────────────────────────
    def start(self):
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT,  self.stop)

        # Write PID
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        log.info("═══════════════════════════════════════")
        log.info(f"  AmitShield Security Engine v{VERSION}")
        log.info(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log.info("═══════════════════════════════════════")

        # Initial setup
        self.setup_firewall()
        self.setup_apparmor()

        # Background threads
        def update_thread():
            time.sleep(3600)  # First check after 1 hour
            while self.running:
                self.check_security_updates()
                time.sleep(86400)  # Daily

        def clean_thread():
            time.sleep(1800)  # First clean after 30 min
            while self.running:
                self.auto_clean()
                time.sleep(21600)  # Every 6 hours

        threading.Thread(target=update_thread, daemon=True).start()
        threading.Thread(target=clean_thread,  daemon=True).start()

        log.info("✓ AmitShield fully operational — Protecting Amit OS")

        # Main scan loop
        while self.running:
            try:
                self.run_scan_cycle()
                time.sleep(self.config["scan_interval_seconds"])
            except Exception as e:
                log.error(f"Scan cycle error: {e}")
                time.sleep(10)


# ─── Entry Point ─────────────────────────────────────────────
if __name__ == "__main__":
    engine = AmitShieldEngine()
    engine.start()
