import os
import psutil

class SystemMonitor:
    """
    System Monitor Backend that gathers real-time system metrics and process information.
    """
    def __init__(self):
        self._proc_cache = {}
        # Cache the logical CPU cores count for CPU normalization
        self.logical_cores = psutil.cpu_count() or 1
        # Initialize system-wide CPU percent measurement (so subsequent calls are accurate)
        psutil.cpu_percent(interval=None)

    def get_system_metrics(self) -> dict:
        """
        Gathers real-time CPU, RAM, Disk, and Network stats.
        Returns:
            dict: {
                'cpu': float,
                'ram': float,
                'disk': float,
                'network': {
                    'bytes_sent': int,
                    'bytes_recv': int
                }
            }
        """
        # Overall CPU usage percentage
        cpu = psutil.cpu_percent(interval=None)
        if cpu is None:
            cpu = 0.0

        # Overall RAM usage percentage
        try:
            ram = psutil.virtual_memory().percent
        except Exception:
            ram = 0.0

        # Overall Disk usage percentage
        try:
            disk = psutil.disk_usage('/').percent
        except Exception:
            try:
                disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
            except Exception:
                disk = 0.0

        # Network bytes sent/received
        try:
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent if net_io else 0
            bytes_recv = net_io.bytes_recv if net_io else 0
        except Exception:
            bytes_sent = 0
            bytes_recv = 0

        return {
            'cpu': round(float(cpu), 2),
            'ram': round(float(ram), 2),
            'disk': round(float(disk), 2),
            'network': {
                'bytes_sent': int(bytes_sent),
                'bytes_recv': int(bytes_recv)
            }
        }

    def get_processes(self) -> list[dict]:
        """
        Returns a list of dictionaries containing active process details.
        Keys: PID, Name, User, CPU%, MEM%
        """
        processes_data = []
        current_pids = set()

        try:
            pids = psutil.pids()
        except Exception:
            pids = []

        for pid in pids:
            current_pids.add(pid)

            # Caching and validation of psutil.Process instance
            if pid not in self._proc_cache:
                try:
                    p = psutil.Process(pid)
                    # Initialize CPU tracking for the process
                    p.cpu_percent(interval=None)
                    self._proc_cache[pid] = p
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    p = None
            else:
                p = self._proc_cache[pid]
                try:
                    # If process is not running or has been recycled, recreate Process instance
                    if not p.is_running():
                        p = psutil.Process(pid)
                        p.cpu_percent(interval=None)
                        self._proc_cache[pid] = p
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    p = None

            # 1. Harvest Process Name
            name = "Unknown"
            if p is not None:
                try:
                    name = p.name()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    if pid == 0:
                        name = "System Idle Process"
                    elif pid == 4:
                        name = "System"
                    else:
                        name = "Access Denied"
                except Exception:
                    name = "Unknown"
            else:
                if pid == 0:
                    name = "System Idle Process"
                elif pid == 4:
                    name = "System"
                else:
                    name = "Access Denied"

            # 2. Harvest Username & filter domains
            username = "N/A"
            if p is not None:
                try:
                    user_raw = p.username()
                    if user_raw:
                        # Clean Windows-specific domain prefix if present (e.g., NT AUTHORITY\SYSTEM)
                        if '\\' in user_raw:
                            username = user_raw.split('\\')[-1]
                        else:
                            username = user_raw
                    else:
                        username = "N/A"
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    if pid in (0, 4):
                        username = "SYSTEM"
                    else:
                        username = "Access Denied"
                except Exception:
                    username = "Unknown"
            else:
                if pid in (0, 4):
                    username = "SYSTEM"
                else:
                    username = "Access Denied"

            # 3. Harvest Process CPU% (divided by logical cores)
            cpu_pct = 0.0
            if p is not None:
                try:
                    raw_cpu = p.cpu_percent(interval=None)
                    # Normalize to 0-100% total system CPU capacity
                    cpu_pct = raw_cpu / self.logical_cores
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cpu_pct = 0.0
                except Exception:
                    cpu_pct = 0.0

            # 4. Harvest Process MEM%
            mem_pct = 0.0
            if p is not None:
                try:
                    mem_pct = p.memory_percent()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    mem_pct = 0.0
                except Exception:
                    mem_pct = 0.0

            processes_data.append({
                'PID': int(pid),
                'Name': str(name),
                'User': str(username),
                'CPU%': round(float(cpu_pct), 2),
                'MEM%': round(float(mem_pct), 2)
            })

        # Purge dead PIDs from cache to avoid memory leaks
        dead_pids = [pid for pid in self._proc_cache if pid not in current_pids]
        for pid in dead_pids:
            try:
                del self._proc_cache[pid]
            except KeyError:
                pass

        return processes_data

    def kill_process(self, pid: int) -> bool:
        """
        Terminates the process with the given PID.
        Returns:
            bool: True if termination succeeded or process is already dead, False on failure.
        """
        # Explicit safety blocks to protect critical PIDs
        if pid == 0 or pid == 4 or pid == os.getpid():
            return False

        try:
            p = psutil.Process(pid)
            p.kill()
            # Wait briefly to confirm termination
            p.wait(timeout=1.0)
            
            # Remove from cache if present
            if pid in self._proc_cache:
                try:
                    del self._proc_cache[pid]
                except KeyError:
                    pass
            return True
        except psutil.NoSuchProcess:
            # Already dead
            if pid in self._proc_cache:
                try:
                    del self._proc_cache[pid]
                except KeyError:
                    pass
            return True
        except (psutil.AccessDenied, psutil.TimeoutExpired):
            return False
        except Exception:
            return False
