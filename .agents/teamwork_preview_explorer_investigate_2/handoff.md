# Handoff Report — Custom Applications Audit (R2)

## 1. Observation

A detailed audit of the 15+ custom applications under `apps/`, the C++ core engine under `core/`, and the `amitshield/` daemon and UI has revealed the following specific bugs, compiler/syntax issues, compatibility errors, and elevation concerns.

### A. Critical Startup & Import Errors (Crash-on-Launch)

1. **`apps/amitpaint.py`**
   - **Code Location**: Lines 8, 92, 94, 105, 108.
   - **Verbatim Code**:
     ```python
     8: from gi.repository import Gtk, Gdk, Cairo
     ...
     92:         self.surface = widget.get_window().create_similar_surface(
     93:             Cairo.Content.COLOR, widget.get_allocated_width(), widget.get_allocated_height())
     94:         cr = Cairo.Context(self.surface)
     ...
     105:         cr = Cairo.Context(self.surface)
     ...
     108:         cr.set_line_cap(Cairo.LineCap.ROUND)
     ```
   - **Issue**: PyGI/GObject Introspection does not expose Cairo directly via `gi.repository`. Trying to import `Cairo` from `gi.repository` throws an immediate `ImportError: cannot import name 'Cairo' from 'gi.repository'` on startup.

2. **`apps/amittray.py`**
   - **Code Location**: Lines 9, 13–17.
   - **Verbatim Code**:
     ```python
     9: gi.require_version("AppIndicator3", "0.1")
     ...
     13: try:
     14:     from gi.repository import AppIndicator3
     15:     HAS_INDICATOR = True
     16: except Exception:
     17:     HAS_INDICATOR = False
     ```
   - **Issue**: The `gi.require_version` call is executed at module level *before* the try-except block. If the system does not have the `gir1.2-appindicator3-0.1` package installed, the program will crash on line 9 with `ValueError: Namespace AppIndicator3 not available`.

3. **`amitshield/amitshield-ui.py` (GTK4 Compatibility)**
   - **Code Location**: Lines 8–10, 35.
   - **Verbatim Code**:
     ```python
     8: gi.require_version("Gtk", "4.0")
     9: gi.require_version("Adw", "1")
     10: from gi.repository import Gtk, Adw, GLib, Pango, Gdk
     ...
     35:         self.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
     ```
   - **Issue**: The dashboard is written in GTK4 + Libadwaita, introducing a dependency mismatch with the rest of the applications (which are GTK3). More critically, in GTK4, the instance method `add_provider` was removed from `Gtk.StyleContext`. Running this code results in an immediate crash: `AttributeError: 'StyleContext' object has no attribute 'add_provider'`.

4. **`amitshield/amitshield.py` (Daemon Permissions)**
   - **Code Location**: Lines 29, 75.
   - **Verbatim Code**:
     ```python
     29: LOG_FILE      = "/var/log/amitshield.log"
     ...
     75:         logging.FileHandler(LOG_FILE),
     ```
   - **Issue**: The daemon creates a file handler targeting `/var/log/amitshield.log` at module import time. If run by a non-root user (e.g. during testing or if imported by another script), it raises an uncaught `PermissionError: [Errno 13] Permission denied: '/var/log/amitshield.log'` and crashes.

---

### B. Elevation & IPC Failures

1. **`core/amitshield_core.cpp` (Unix Socket Permission Bug)**
   - **Code Location**: Lines 455–457.
   - **Verbatim Code**:
     ```cpp
     455:     ::chmod(SOCKET_PATH, 0666);
     456: 
     457:     if (::bind(srv, (struct sockaddr*)&addr, sizeof(addr)) < 0) { ::close(srv); return; }
     ```
   - **Issue**: The C++ daemon attempts to call `chmod` on the socket file `/tmp/amitshield.sock` *before* calling `bind`. Since `bind` is what actually creates the socket file, `chmod` fails with `ENOENT` (No such file or directory). The socket is subsequently created by `bind` with root's default restrictive umask permissions (e.g., `0755` or `0700`). Consequently, any non-root client (such as `amitshield-ui.py` or `amitshield_bridge.py` running in a user session) fails to write to the socket, returning a `Permission Denied` error and preventing IPC.

2. **`amitshield/amitshield.service` (Systemd Startup Failure)**
   - **Code Location**: Line 10.
   - **Verbatim Code**:
     ```ini
     10: ExecStartPre=/usr/local/bin/amitshield-preflight.sh
     ```
   - **Issue**: The service file requires a preflight script (`amitshield-preflight.sh`) which is completely missing from the repository. Under Systemd, any failure in `ExecStartPre` blocks service launch, preventing the security daemon from starting.

3. **`apps/amitcleaner.py` (Privilege Silent Failure)**
   - **Code Location**: Lines 68–73, 83.
   - **Verbatim Code**:
     ```python
     68:         paths = [
     69:             os.path.expanduser("~/.cache"),
     70:             "/var/cache/apt/archives",
     71:             "/tmp",
     72:             os.path.expanduser("~/.local/share/Trash")
     73:         ]
     ...
     83:                 except: pass
     ```
   - **Issue**: It attempts to clean system-owned folders like `/var/cache/apt/archives` and `/tmp` (which contains files owned by other users) but runs without root elevation, causing permission failures that are caught and ignored silently.

4. **`amitshield/amitshield-ui.py` (Log View Access Denied)**
   - **Code Location**: Lines 301–305.
   - **Verbatim Code**:
     ```python
     301:     def _view_log(self, btn):
     302:         try:
     303:             subprocess.Popen(["xdg-open", "/var/log/amitshield.log"])
     ```
   - **Issue**: Attempting to view the log file using the default editor via `xdg-open` fails for regular users since the file is owned by root with restrictive permissions.

---

### C. Performance & UI Thread-Blocking Issues

1. **`apps/amitmonitor.py` (Process list latency)**
   - **Code Location**: Lines 98–123, 272.
   - **Issue**: Every 1.5 seconds, the script lists `/proc` and reads three files per process (`/proc/{pid}/stat`, `/proc/{pid}/statm`, and `/proc/{pid}/comm`) synchronously on the main thread. This performs hundreds of disk/sysfs operations per cycle, blocking the GTK main loop and causing severe GUI stuttering.

2. **`apps/amitsearch.py` (Typing Lag)**
   - **Code Location**: Lines 71–98.
   - **Issue**: On every single character typed in the search bar, it reads every desktop file in `/usr/share/applications` and `~/.local/share/applications` synchronously on the main thread, blocking user input.

---

### D. UI & State Sync Bugs

1. **`apps/amitnotes.py` (Sidebar Selection Sync)**
   - **Code Location**: Lines 226–237, 261–277.
   - **Issue**: Rebuilding the listbox in `_save_current()` during selection changes triggers recursive event processing that ends up setting the selection to the *old* note while the editor updates to the *new* note.

2. **`apps/amitstore.py` (Installation State Tracking)**
   - **Code Location**: Lines 248–268.
   - **Issue**: The worker thread executes the PolicyKit elevation command:
     `subprocess.run(["pkexec", "apt-get", action, "-y", pkg], ...)`
     but calls the success handler `_post_action` regardless of the subprocess's return code. If the user cancels the PolicyKit prompt or if the command fails, the UI still marks the application as installed or removed.

---

## 2. Logic Chain

1. **`amitpaint.py` ImportError**:
   - *Observation*: Line 8 attempts to import `Cairo` from `gi.repository`.
   - *Reasoning*: Cairo is not packaged inside the GObject Introspection repository for Python GI. Instead, Python bindings for Cairo are provided by the `pycairo` package under the namespace `cairo`.
   - *Conclusion*: Running the script throws an immediate `ImportError`.

2. **`amittray.py` ValueError**:
   - *Observation*: Line 9 calls `gi.require_version("AppIndicator3", "0.1")`.
   - *Reasoning*: The `require_version` call throws `ValueError` if the library version is not registered. Because this is outside the try-except wrapper (lines 13–17), the program crashes immediately on system platforms lacking AppIndicator3 introspection metadata.

3. **`amitshield-ui.py` AttributeError**:
   - *Observation*: Line 35 calls `self.get_style_context().add_provider(...)` on a `Gtk.Box` under GTK4.
   - *Reasoning*: In GTK4, the `add_provider` method was removed from `Gtk.StyleContext`. Style providers must now be added globally on the display level.
   - *Conclusion*: Invoking the script results in an `AttributeError`.

4. **`amitshield_core.cpp` IPC Permission Denied**:
   - *Observation*: Line 455 performs `chmod(SOCKET_PATH, 0666)` and Line 457 runs `bind(srv, ...)`.
   - *Reasoning*: `chmod` requires the file to exist on the filesystem. Since the Unix socket is created by the `bind` system call, calling `chmod` beforehand has no effect. The file is created with root permissions, blocking user-level UI connections.
   - *Conclusion*: IPC connection from `amitshield-ui.py` fails with permission errors.

---

## 3. Caveats

- We did not compile the C++ code locally since compile checks require a Linux/Debian host environment, whereas we are operating on a Windows system. The C++ findings were identified through static analysis of the source code (`amitshield_core.cpp`, `daemon_main.cpp`, `CMakeLists.txt`).
- We assume that the target OS platform runs standard KDE Plasma 5 as specified in the `README.md`.

---

## 4. Conclusion

The audit shows that **multiple core custom apps and services fail to run in their current state** due to syntax/import errors, GTK4 API mismatches, systemd configuration errors, and C++ socket permission sequencing bugs. 

To resolve these, the following changes must be implemented:
- **`amitpaint.py`**: Fix Cairo imports to use native `import cairo` instead of `gi.repository`.
- **`amittray.py`**: Wrap the `require_version` call inside the existing try-except block.
- **`amitshield-ui.py`**: Modify CSS provider registration to use `add_provider_for_display`.
- **`amitshield_core.cpp`**: Move the `chmod` call to execute *after* the `bind` call.
- **`amitshield.service`**: Either create `amitshield-preflight.sh` or remove `ExecStartPre` from the service file.
- **`amitmonitor.py` & `amitsearch.py`**: Move disk I/O operations (scanning `/proc` and reading desktop files) to background threads.
- **`amitstore.py`**: Verify `res.returncode == 0` before updating UI installation state.

---

## 5. Proposed Code Changes (Before ➔ After)

### Fix 1: `apps/amitpaint.py` (Cairo Import)
**Before (Lines 8–9):**
```python
from gi.repository import Gtk, Gdk, Cairo
import math
```
**After:**
```python
from gi.repository import Gtk, Gdk
import cairo as Cairo
import math
```

---

### Fix 2: `apps/amittray.py` (AppIndicator3 Crash)
**Before (Lines 7–17):**
```python
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, Gdk, GLib
import subprocess, os, re, threading, time

try:
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except Exception:
    HAS_INDICATOR = False
```
**After:**
```python
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import subprocess, os, re, threading, time

try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except Exception:
    HAS_INDICATOR = False
```

---

### Fix 3: `amitshield/amitshield-ui.py` (StyleContext crash)
**Before (Lines 34–35):**
```python
        self.get_style_context().add_class("threat-card")
        self.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
```
**After:**
```python
        self.add_css_class("threat-card")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
```

---

### Fix 4: `core/amitshield_core.cpp` (IPC Socket permissions)
**Before (Lines 454–457):**
```cpp
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path)-1);
    ::chmod(SOCKET_PATH, 0666);

    if (::bind(srv, (struct sockaddr*)&addr, sizeof(addr)) < 0) { ::close(srv); return; }
```
**After:**
```cpp
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path)-1);

    if (::bind(srv, (struct sockaddr*)&addr, sizeof(addr)) < 0) { ::close(srv); return; }
    ::chmod(SOCKET_PATH, 0666);
```

---

### Fix 5: `amitshield/amitshield.service` (Missing preflight)
**Before (Lines 10–11):**
```ini
ExecStartPre=/usr/local/bin/amitshield-preflight.sh
ExecStart=/usr/bin/python3 /usr/local/bin/amitshield.py
```
**After (if preflight script is not needed):**
```ini
ExecStart=/usr/bin/python3 /usr/local/bin/amitshield.py
```

---

## 6. Verification Method

To verify these issues independently:
1. **Import Checks**:
   Run python check command on the modified scripts:
   ```bash
   python3 -m py_compile apps/amitpaint.py
   python3 -m py_compile apps/amittray.py
   python3 -m py_compile amitshield/amitshield-ui.py
   ```
   *Pass Condition*: The commands return exit code `0` without error.
2. **Socket Permission Check**:
   On a Linux/WSL2 host:
   Compile and run the daemon as root:
   ```bash
   sudo ./core/amitshield-daemon
   ```
   Check the permissions of `/tmp/amitshield.sock`:
   ```bash
   ls -la /tmp/amitshield.sock
   ```
   *Invalidation Condition*: If the permissions are `srwxr-xr-x` (or similar), non-root users will get a `Permission Denied` error when trying to write to the socket.
   *Valid Condition*: The permissions should be `srwxrwxrwx` (writable by all).
