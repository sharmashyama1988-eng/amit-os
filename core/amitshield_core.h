// ============================================================
//  AMITSHIELD CORE — C++ Security Engine Header
//  Amit OS Security Engine v1.0
//  Author: Amit
// ============================================================

#pragma once
#ifndef AMITSHIELD_CORE_H
#define AMITSHIELD_CORE_H

#include <string>
#include <vector>
#include <map>
#include <set>
#include <atomic>
#include <mutex>
#include <thread>
#include <functional>
#include <chrono>
#include <cstdint>

namespace AmitShield {

// ── Version ─────────────────────────────────────────────────
constexpr const char* VERSION     = "1.0.0";
constexpr const char* SOCKET_PATH = "/tmp/amitshield.sock";
constexpr int         MAX_THREATS = 1000;

// ── Alert severity levels ────────────────────────────────────
enum class AlertLevel {
    INFO    = 0,
    WARNING = 1,
    DANGER  = 2,
    CRITICAL= 3
};

// ── Threat record ────────────────────────────────────────────
struct Threat {
    uint64_t    id;
    std::string type;         // "process", "network", "file"
    std::string description;
    std::string source;
    AlertLevel  level;
    bool        blocked;
    int64_t     timestamp;    // Unix epoch ms
};

// ── Process info ─────────────────────────────────────────────
struct ProcessInfo {
    int         pid;
    int         ppid;
    std::string name;
    std::string user;
    std::string cmdline;
    double      cpu_percent;
    uint64_t    mem_rss_kb;
};

// ── Network connection ───────────────────────────────────────
struct NetConn {
    std::string local_ip;
    int         local_port;
    std::string remote_ip;
    int         remote_port;
    std::string state;        // "ESTABLISHED", "LISTEN", etc.
    int         pid;
};

// ── Security Status snapshot ─────────────────────────────────
struct SecurityStatus {
    std::string version;
    std::string status;           // "active", "idle", "alert"
    uint64_t    uptime_seconds;
    uint32_t    threats_detected;
    uint32_t    threats_blocked;
    uint32_t    scans_completed;
    bool        firewall_active;
    bool        apparmor_active;
    double      cpu_usage;
    uint64_t    mem_used_mb;
    uint64_t    mem_total_mb;
};

// ── Callback types ───────────────────────────────────────────
using ThreatCallback  = std::function<void(const Threat&)>;
using StatusCallback  = std::function<void(const SecurityStatus&)>;

// ════════════════════════════════════════════════════════════
//  PROCESS MONITOR MODULE
// ════════════════════════════════════════════════════════════
class ProcessMonitor {
public:
    ProcessMonitor();
    ~ProcessMonitor();

    std::vector<ProcessInfo> scan();
    bool is_suspicious(const ProcessInfo& proc) const;
    bool kill_process(int pid);
    bool suspend_process(int pid);
    double get_cpu_usage();
    uint64_t get_mem_info(uint64_t& total_kb);

private:
    std::set<int>                 known_pids_;
    std::vector<std::string>      suspicious_patterns_;
    std::vector<std::string>      protected_names_;

    std::string read_file(const std::string& path) const;
    ProcessInfo parse_proc(int pid) const;
    std::string get_cmdline(int pid) const;
    std::string get_procname(int pid) const;
    std::string get_proc_user(int pid) const;
};

// ════════════════════════════════════════════════════════════
//  NETWORK GUARDIAN MODULE
// ════════════════════════════════════════════════════════════
class NetworkGuardian {
public:
    NetworkGuardian();
    ~NetworkGuardian();

    std::vector<NetConn> scan_connections();
    bool is_suspicious_port(int port) const;
    bool block_ip(const std::string& ip);
    bool unblock_ip(const std::string& ip);
    bool apply_firewall_rules();
    std::vector<std::string> get_blocked_ips() const;

private:
    std::set<int>         dangerous_ports_;
    std::set<std::string> blocked_ips_;
    mutable std::mutex    mutex_;

    std::vector<NetConn> parse_tcp_connections() const;
    std::vector<NetConn> parse_udp_connections() const;
    bool run_ufw_cmd(const std::vector<std::string>& args);
};

// ════════════════════════════════════════════════════════════
//  FIREWALL MODULE
// ════════════════════════════════════════════════════════════
class Firewall {
public:
    Firewall();
    ~Firewall();

    bool enable();
    bool disable();
    bool is_active() const;
    bool add_rule(const std::string& rule);
    bool allow_port(int port, const std::string& proto = "tcp");
    bool deny_port(int port, const std::string& proto = "tcp");
    bool allow_ip(const std::string& ip);
    bool deny_ip(const std::string& ip);
    bool reset_to_defaults();
    std::string get_status() const;

private:
    bool        active_;
    mutable std::mutex mutex_;
    bool run_command(const std::string& cmd) const;
};

// ════════════════════════════════════════════════════════════
//  MAIN AMITSHIELD ENGINE
// ════════════════════════════════════════════════════════════
class Engine {
public:
    Engine();
    ~Engine();

    // Lifecycle
    bool  start();
    void  stop();
    bool  is_running() const { return running_.load(); }

    // Callbacks
    void set_threat_callback(ThreatCallback cb)  { threat_cb_ = cb; }
    void set_status_callback(StatusCallback cb)  { status_cb_ = cb; }

    // Modules
    ProcessMonitor& processes()  { return proc_monitor_; }
    NetworkGuardian& network()   { return net_guardian_; }
    Firewall& firewall()         { return firewall_; }

    // Status & reports
    SecurityStatus  get_status() const;
    std::vector<Threat> get_recent_threats(int count = 50) const;

    // Config
    void set_scan_interval(int seconds) { scan_interval_sec_ = seconds; }
    int  get_scan_interval() const      { return scan_interval_sec_; }

    // IPC server (Python bridge connects here)
    bool start_ipc_server();
    void stop_ipc_server();

private:
    std::atomic<bool>    running_        { false };
    std::atomic<bool>    ipc_running_    { false };
    int                  scan_interval_sec_ { 30 };

    ProcessMonitor       proc_monitor_;
    NetworkGuardian      net_guardian_;
    Firewall             firewall_;

    ThreatCallback       threat_cb_;
    StatusCallback       status_cb_;

    std::vector<Threat>  threats_;
    mutable std::mutex   threats_mutex_;
    uint64_t             threat_id_counter_ { 0 };

    std::thread          scan_thread_;
    std::thread          ipc_thread_;

    std::chrono::steady_clock::time_point start_time_;
    uint32_t             scans_completed_ { 0 };

    // Internal
    void scan_loop();
    void ipc_loop();
    void handle_ipc_client(int client_fd);
    void add_threat(Threat t);
    void fire_alert(const Threat& t);
    std::string status_to_json() const;
    std::string threats_to_json(int count) const;
    std::string handle_command(const std::string& cmd_json);
};

} // namespace AmitShield

// ── C-compatible export API (for Python ctypes bridge) ──────
extern "C" {
    void* amitshield_create();
    void  amitshield_destroy(void* engine);
    int   amitshield_start(void* engine);
    void  amitshield_stop(void* engine);
    int   amitshield_is_running(void* engine);
    // Returns JSON string (caller must free with amitshield_free_str)
    const char* amitshield_get_status(void* engine);
    const char* amitshield_get_threats(void* engine, int count);
    void  amitshield_free_str(char* str);
    int   amitshield_block_ip(void* engine, const char* ip);
    int   amitshield_firewall_enable(void* engine);
    int   amitshield_firewall_disable(void* engine);
}

#endif // AMITSHIELD_CORE_H
