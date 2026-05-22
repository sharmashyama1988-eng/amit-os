"""
============================================================
  AMITSHIELD BRIDGE — Python ↔ C++ Bridge
  Amit OS Security Engine v1.0
  Author: Amit

  Two connection modes:
    1. ctypes   → loads libamitshield.so directly (fast)
    2. socket   → connects to running C++ IPC server (safe)
  
  Auto-detects which mode to use.
============================================================
"""

import ctypes
import socket
import json
import os
import time
import logging
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any

log = logging.getLogger("amitshield.bridge")

# ── Paths ────────────────────────────────────────────────────
SOCKET_PATH  = "/tmp/amitshield.sock"
LIB_PATHS    = [
    "./libamitshield.so",
    "/usr/local/lib/libamitshield.so",
    "/usr/lib/libamitshield.so",
]
DAEMON_BIN   = "/usr/local/bin/amitshield-daemon"


# ════════════════════════════════════════════════════════════
#  ctypes WRAPPER — direct .so calls (max performance)
# ════════════════════════════════════════════════════════════
class _CtypesBackend:
    """Wraps the compiled C++ .so via ctypes."""

    def __init__(self, lib_path: str):
        self._lib = ctypes.CDLL(lib_path)
        self._setup_signatures()
        self._engine = self._lib.amitshield_create()
        if not self._engine:
            raise RuntimeError("Failed to create C++ engine instance")
        log.info(f"[Bridge] ctypes backend loaded: {lib_path}")

    def _setup_signatures(self):
        lib = self._lib
        lib.amitshield_create.restype          = ctypes.c_void_p
        lib.amitshield_destroy.argtypes        = [ctypes.c_void_p]
        lib.amitshield_start.argtypes          = [ctypes.c_void_p]
        lib.amitshield_start.restype           = ctypes.c_int
        lib.amitshield_stop.argtypes           = [ctypes.c_void_p]
        lib.amitshield_is_running.argtypes     = [ctypes.c_void_p]
        lib.amitshield_is_running.restype      = ctypes.c_int
        lib.amitshield_get_status.argtypes     = [ctypes.c_void_p]
        lib.amitshield_get_status.restype      = ctypes.c_char_p
        lib.amitshield_get_threats.argtypes    = [ctypes.c_void_p, ctypes.c_int]
        lib.amitshield_get_threats.restype     = ctypes.c_char_p
        lib.amitshield_free_str.argtypes       = [ctypes.c_char_p]
        lib.amitshield_block_ip.argtypes       = [ctypes.c_void_p, ctypes.c_char_p]
        lib.amitshield_block_ip.restype        = ctypes.c_int
        lib.amitshield_firewall_enable.argtypes  = [ctypes.c_void_p]
        lib.amitshield_firewall_enable.restype   = ctypes.c_int
        lib.amitshield_firewall_disable.argtypes = [ctypes.c_void_p]
        lib.amitshield_firewall_disable.restype  = ctypes.c_int

    def start(self) -> bool:
        return bool(self._lib.amitshield_start(self._engine))

    def stop(self):
        self._lib.amitshield_stop(self._engine)

    def is_running(self) -> bool:
        return bool(self._lib.amitshield_is_running(self._engine))

    def get_status(self) -> Dict:
        raw = self._lib.amitshield_get_status(self._engine)
        return json.loads(raw.decode()) if raw else {}

    def get_threats(self, count: int = 50) -> List[Dict]:
        raw = self._lib.amitshield_get_threats(self._engine, count)
        return json.loads(raw.decode()) if raw else []

    def block_ip(self, ip: str) -> bool:
        return bool(self._lib.amitshield_block_ip(self._engine, ip.encode()))

    def firewall_enable(self) -> bool:
        return bool(self._lib.amitshield_firewall_enable(self._engine))

    def firewall_disable(self) -> bool:
        return bool(self._lib.amitshield_firewall_disable(self._engine))

    def __del__(self):
        if hasattr(self, '_engine') and self._engine:
            self._lib.amitshield_destroy(self._engine)


# ════════════════════════════════════════════════════════════
#  SOCKET BACKEND — talks to running C++ daemon via IPC
# ════════════════════════════════════════════════════════════
class _SocketBackend:
    """Connects to the C++ daemon's Unix socket."""

    def __init__(self):
        self._sock_path = SOCKET_PATH
        self._daemon_proc: Optional[subprocess.Popen] = None
        log.info("[Bridge] Socket backend initialised")

    def _send(self, action: str, **kwargs) -> Dict:
        payload = json.dumps({"action": action, **kwargs})
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect(self._sock_path)
                s.sendall(payload.encode())
                data = b""
                while True:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    data += chunk
            return json.loads(data.decode()) if data else {}
        except (ConnectionRefusedError, FileNotFoundError):
            return {"error": "daemon not running"}
        except Exception as e:
            log.error(f"[Bridge] IPC error: {e}")
            return {"error": str(e)}

    def start(self) -> bool:
        if os.path.exists(DAEMON_BIN):
            self._daemon_proc = subprocess.Popen(
                [DAEMON_BIN],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1.0)
            return True
        return False

    def stop(self):
        self._send("stop")
        if self._daemon_proc:
            self._daemon_proc.terminate()

    def is_running(self) -> bool:
        r = self._send("get_status")
        return "error" not in r

    def get_status(self) -> Dict:
        return self._send("get_status")

    def get_threats(self, count: int = 50) -> List[Dict]:
        r = self._send("get_threats", count=count)
        return r if isinstance(r, list) else []

    def block_ip(self, ip: str) -> bool:
        r = self._send("block_ip", ip=ip)
        return r.get("ok", False)

    def firewall_enable(self) -> bool:
        r = self._send("fw_enable")
        return r.get("ok", False)

    def firewall_disable(self) -> bool:
        r = self._send("fw_disable")
        return r.get("ok", False)


# ════════════════════════════════════════════════════════════
#  PYTHON FALLBACK — pure Python engine (no C++ needed)
# ════════════════════════════════════════════════════════════
class _PythonFallback:
    """Full Python implementation — used when C++ lib missing."""

    def __init__(self):
        import re, pwd
        self._running    = False
        self._threats    = []
        self._blocked    = 0
        self._scans      = 0
        self._start_time = time.time()
        self._thread     = None
        self._re         = re
        self._suspicious = [
            r"xmrig", r"minerd", r"cpuminer",
            r"nc -e", r"/dev/tcp/",
            r"wget.*\|.*bash", r"curl.*\|.*bash"
        ]
        log.warning("[Bridge] Using Python fallback engine (compile C++ for best performance)")

    def start(self) -> bool:
        self._running = True
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _scan_loop(self):
        import glob
        while self._running:
            try:
                self._scans += 1
                for pid_path in glob.glob("/proc/[0-9]*/cmdline"):
                    try:
                        with open(pid_path, "r", errors="replace") as f:
                            cmd = f.read().replace("\x00", " ")
                        for pat in self._suspicious:
                            if self._re.search(pat, cmd, self._re.IGNORECASE):
                                pid = int(pid_path.split("/")[2])
                                self._threats.append({
                                    "type": "process",
                                    "description": f"Suspicious: PID {pid}",
                                    "blocked": False,
                                    "timestamp": int(time.time() * 1000)
                                })
                                os.kill(pid, 19)  # SIGSTOP
                                self._threats[-1]["blocked"] = True
                                self._blocked += 1
            except Exception:
                pass
            time.sleep(30)

    def get_status(self) -> Dict:
        uptime = int(time.time() - self._start_time)
        return {
            "version":          "1.0.0-py",
            "status":           "active" if self._running else "stopped",
            "uptime":           uptime,
            "threats_detected": len(self._threats),
            "threats_blocked":  self._blocked,
            "scans_completed":  self._scans,
            "firewall":         "active",
            "cpu_usage":        0.0,
            "mem_used_mb":      0,
            "mem_total_mb":     0,
        }

    def get_threats(self, count: int = 50) -> List[Dict]:
        return self._threats[-count:]

    def block_ip(self, ip: str) -> bool:
        return os.system(f"ufw deny from {ip} to any") == 0

    def firewall_enable(self)  -> bool:
        return os.system("ufw --force enable")  == 0

    def firewall_disable(self) -> bool:
        return os.system("ufw disable") == 0


# ════════════════════════════════════════════════════════════
#  AMITSHIELD BRIDGE — Public API (auto-selects backend)
# ════════════════════════════════════════════════════════════
class AmitShieldBridge:
    """
    Unified Python API for AmitShield C++ Engine.

    Priority:
      1. ctypes   → libamitshield.so found
      2. socket   → C++ daemon running on Unix socket
      3. Python   → pure Python fallback

    Usage:
        bridge = AmitShieldBridge()
        bridge.start()
        status = bridge.get_status()
        threats = bridge.get_threats()
        bridge.block_ip("1.2.3.4")
    """

    def __init__(self):
        self._backend = None
        self._mode    = None
        self._select_backend()

    def _select_backend(self):
        # 1. Try ctypes (.so)
        for path in LIB_PATHS:
            if os.path.exists(path):
                try:
                    self._backend = _CtypesBackend(path)
                    self._mode    = "ctypes"
                    log.info("[Bridge] ✓ ctypes backend (C++ .so)")
                    return
                except Exception as e:
                    log.warning(f"[Bridge] ctypes failed: {e}")

        # 2. Try socket (C++ daemon already running)
        if os.path.exists(SOCKET_PATH):
            try:
                self._backend = _SocketBackend()
                self._mode    = "socket"
                log.info("[Bridge] ✓ socket backend (C++ daemon IPC)")
                return
            except Exception as e:
                log.warning(f"[Bridge] socket failed: {e}")

        # 3. Pure Python fallback
        self._backend = _PythonFallback()
        self._mode    = "python"
        log.warning("[Bridge] ✓ Python fallback (compile core for better performance)")

    # ── Public API ───────────────────────────────────────────
    @property
    def mode(self) -> str:
        return self._mode

    def start(self) -> bool:
        return self._backend.start()

    def stop(self):
        self._backend.stop()

    def is_running(self) -> bool:
        return self._backend.is_running()

    def get_status(self) -> Dict[str, Any]:
        return self._backend.get_status()

    def get_threats(self, count: int = 50) -> List[Dict]:
        return self._backend.get_threats(count)

    def block_ip(self, ip: str) -> bool:
        return self._backend.block_ip(ip)

    def firewall_enable(self) -> bool:
        return self._backend.firewall_enable()

    def firewall_disable(self) -> bool:
        return self._backend.firewall_disable()

    def __repr__(self):
        return f"<AmitShieldBridge mode={self._mode} running={self.is_running()}>"


# ── Singleton instance ───────────────────────────────────────
_bridge_instance: Optional[AmitShieldBridge] = None

def get_bridge() -> AmitShieldBridge:
    """Get or create the global bridge singleton."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AmitShieldBridge()
    return _bridge_instance


# ── CLI test ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    b = AmitShieldBridge()
    print(f"\n╔══ AmitShield Bridge ══╗")
    print(f"  Mode   : {b.mode}")
    b.start()
    time.sleep(1)
    status = b.get_status()
    for k, v in status.items():
        print(f"  {k:20s}: {v}")
    print(f"╚════════════════════════╝\n")
