// ============================================================
//  AMITSHIELD CORE — C++ Security Engine
//  Amit OS v1.0  |  Author: Amit
//  Compile: g++ -O2 -std=c++17 -shared -fPIC -o libamitshield.so amitshield_core.cpp -lpthread
// ============================================================

#include "amitshield_core.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <regex>
#include <cstring>
#include <csignal>
#include <dirent.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <sys/sysinfo.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pwd.h>
#include <chrono>

namespace AmitShield {

// ════════════════════════════════════════════════════════════
//  PROCESS MONITOR
// ════════════════════════════════════════════════════════════
ProcessMonitor::ProcessMonitor() {
    suspicious_patterns_ = {
        "xmrig","minerd","cpuminer","cryptominer",
        "nc -e","bash -i","python -c.*socket",
        "/dev/tcp/","wget.*|.*bash","curl.*|.*bash"
    };
    protected_names_ = {
        "systemd","init","kthreadd","sddm","plasmashell",
        "kwin_x11","dbus-daemon","NetworkManager","amitshield"
    };
}
ProcessMonitor::~ProcessMonitor() {}

std::string ProcessMonitor::read_file(const std::string& path) const {
    std::ifstream f(path);
    if (!f.is_open()) return "";
    std::string content((std::istreambuf_iterator<char>(f)),
                         std::istreambuf_iterator<char>());
    return content;
}

std::string ProcessMonitor::get_cmdline(int pid) const {
    std::string path = "/proc/" + std::to_string(pid) + "/cmdline";
    std::string raw  = read_file(path);
    // Replace null bytes with spaces
    std::replace(raw.begin(), raw.end(), '\0', ' ');
    return raw;
}

std::string ProcessMonitor::get_procname(int pid) const {
    std::string path = "/proc/" + std::to_string(pid) + "/comm";
    std::string name = read_file(path);
    if (!name.empty() && name.back() == '\n')
        name.pop_back();
    return name;
}

std::string ProcessMonitor::get_proc_user(int pid) const {
    std::string status_path = "/proc/" + std::to_string(pid) + "/status";
    std::ifstream f(status_path);
    std::string line;
    while (std::getline(f, line)) {
        if (line.rfind("Uid:", 0) == 0) {
            std::istringstream ss(line.substr(4));
            int uid; ss >> uid;
            struct passwd* pw = getpwuid(uid);
            if (pw) return std::string(pw->pw_name);
            return std::to_string(uid);
        }
    }
    return "unknown";
}

ProcessInfo ProcessMonitor::parse_proc(int pid) const {
    ProcessInfo info{};
    info.pid     = pid;
    info.name    = get_procname(pid);
    info.cmdline = get_cmdline(pid);
    info.user    = get_proc_user(pid);

    // Read RSS memory from /proc/pid/status
    std::string status = read_file("/proc/" + std::to_string(pid) + "/status");
    std::istringstream ss(status);
    std::string line;
    while (std::getline(ss, line)) {
        if (line.rfind("VmRSS:", 0) == 0) {
            std::istringstream ls(line.substr(6));
            ls >> info.mem_rss_kb;
            break;
        }
    }
    return info;
}

std::vector<ProcessInfo> ProcessMonitor::scan() {
    std::vector<ProcessInfo> procs;
    DIR* dir = opendir("/proc");
    if (!dir) return procs;

    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        if (entry->d_type != DT_DIR) continue;
        int pid = 0;
        try { pid = std::stoi(entry->d_name); }
        catch (...) { continue; }
        if (pid <= 0) continue;
        procs.push_back(parse_proc(pid));
    }
    closedir(dir);
    return procs;
}

bool ProcessMonitor::is_suspicious(const ProcessInfo& proc) const {
    for (auto& prot : protected_names_)
        if (proc.name == prot) return false;

    for (auto& pat : suspicious_patterns_) {
        std::regex re(pat, std::regex::icase | std::regex::ECMAScript);
        if (std::regex_search(proc.cmdline, re)) return true;
        if (std::regex_search(proc.name,    re)) return true;
    }
    return false;
}

bool ProcessMonitor::kill_process(int pid) {
    return ::kill(pid, SIGKILL) == 0;
}

bool ProcessMonitor::suspend_process(int pid) {
    return ::kill(pid, SIGSTOP) == 0;
}

double ProcessMonitor::get_cpu_usage() {
    // Read /proc/stat twice with 100ms gap
    auto read_stat = []() -> std::pair<uint64_t,uint64_t> {
        std::ifstream f("/proc/stat");
        std::string label;
        uint64_t user,nice,sys,idle,iow,irq,sirq;
        f >> label >> user >> nice >> sys >> idle >> iow >> irq >> sirq;
        uint64_t total = user+nice+sys+idle+iow+irq+sirq;
        return {idle, total};
    };
    auto [idle1, total1] = read_stat();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    auto [idle2, total2] = read_stat();
    uint64_t dt = total2 - total1;
    uint64_t di = idle2  - idle1;
    if (dt == 0) return 0.0;
    return 100.0 * (1.0 - (double)di / dt);
}

uint64_t ProcessMonitor::get_mem_info(uint64_t& total_kb) {
    struct sysinfo si;
    sysinfo(&si);
    total_kb = si.totalram * si.mem_unit / 1024;
    uint64_t free_kb  = si.freeram  * si.mem_unit / 1024;
    uint64_t avail_kb = si.bufferram * si.mem_unit / 1024;
    return total_kb - free_kb - avail_kb;
}

// ════════════════════════════════════════════════════════════
//  NETWORK GUARDIAN
// ════════════════════════════════════════════════════════════
NetworkGuardian::NetworkGuardian() {
    dangerous_ports_ = {23,135,137,138,139,445,3389,5900,6667,4444,1337};
}
NetworkGuardian::~NetworkGuardian() {}

bool NetworkGuardian::run_ufw_cmd(const std::vector<std::string>& args) {
    std::string cmd = "ufw";
    for (auto& a : args) cmd += " " + a;
    return system(cmd.c_str()) == 0;
}

bool NetworkGuardian::apply_firewall_rules() {
    run_ufw_cmd({"default","deny","incoming"});
    run_ufw_cmd({"default","allow","outgoing"});
    run_ufw_cmd({"allow","ssh"});
    run_ufw_cmd({"allow","80/tcp"});
    run_ufw_cmd({"allow","443/tcp"});
    run_ufw_cmd({"--force","enable"});
    for (int p : dangerous_ports_)
        run_ufw_cmd({"deny", std::to_string(p)});
    return true;
}

std::vector<NetConn> NetworkGuardian::parse_tcp_connections() const {
    std::vector<NetConn> conns;
    std::ifstream f("/proc/net/tcp");
    std::string line;
    std::getline(f, line); // skip header
    while (std::getline(f, line)) {
        std::istringstream ss(line);
        std::string idx, local, remote, state, rest;
        ss >> idx >> local >> remote >> state;

        auto parse_addr = [](const std::string& hex, std::string& ip, int& port) {
            size_t colon = hex.find(':');
            if (colon == std::string::npos) return;
            unsigned int ip_hex = std::stoul(hex.substr(0, colon), nullptr, 16);
            port = std::stoi(hex.substr(colon+1), nullptr, 16);
            unsigned char bytes[4];
            memcpy(bytes, &ip_hex, 4);
            char buf[32];
            snprintf(buf, sizeof(buf), "%d.%d.%d.%d",
                     bytes[0], bytes[1], bytes[2], bytes[3]);
            ip = buf;
        };

        NetConn c;
        parse_addr(local,  c.local_ip,  c.local_port);
        parse_addr(remote, c.remote_ip, c.remote_port);
        unsigned int st = std::stoul(state, nullptr, 16);
        c.state = (st == 1) ? "ESTABLISHED" : (st == 10) ? "LISTEN" : "OTHER";
        conns.push_back(c);
    }
    return conns;
}

std::vector<NetConn> NetworkGuardian::scan_connections() {
    std::lock_guard<std::mutex> lock(mutex_);
    return parse_tcp_connections();
}

bool NetworkGuardian::is_suspicious_port(int port) const {
    return dangerous_ports_.count(port) > 0;
}

bool NetworkGuardian::block_ip(const std::string& ip) {
    std::lock_guard<std::mutex> lock(mutex_);
    blocked_ips_.insert(ip);
    return run_ufw_cmd({"deny","from", ip,"to","any"});
}

bool NetworkGuardian::unblock_ip(const std::string& ip) {
    std::lock_guard<std::mutex> lock(mutex_);
    blocked_ips_.erase(ip);
    return run_ufw_cmd({"delete","deny","from", ip,"to","any"});
}

// ════════════════════════════════════════════════════════════
//  FIREWALL
// ════════════════════════════════════════════════════════════
Firewall::Firewall() : active_(false) {}
Firewall::~Firewall() {}

bool Firewall::run_command(const std::string& cmd) const {
    return system(cmd.c_str()) == 0;
}
bool Firewall::enable()  { active_ = run_command("ufw --force enable"); return active_; }
bool Firewall::disable() { active_ = !run_command("ufw disable"); return !active_; }
bool Firewall::is_active() const { return active_; }
bool Firewall::allow_port(int p, const std::string& proto) {
    return run_command("ufw allow " + std::to_string(p) + "/" + proto);
}
bool Firewall::deny_port(int p, const std::string& proto) {
    return run_command("ufw deny " + std::to_string(p) + "/" + proto);
}
bool Firewall::allow_ip(const std::string& ip) {
    return run_command("ufw allow from " + ip);
}
bool Firewall::deny_ip(const std::string& ip) {
    return run_command("ufw deny from " + ip + " to any");
}
bool Firewall::reset_to_defaults() {
    return run_command("ufw --force reset");
}
std::string Firewall::get_status() const {
    return active_ ? "active" : "inactive";
}

// ════════════════════════════════════════════════════════════
//  MAIN ENGINE
// ════════════════════════════════════════════════════════════
Engine::Engine() {
    start_time_ = std::chrono::steady_clock::now();
}
Engine::~Engine() { stop(); }

bool Engine::start() {
    if (running_.load()) return false;
    running_ = true;

    // Setup firewall
    net_guardian_.apply_firewall_rules();
    firewall_.enable();

    // Start scan thread
    scan_thread_ = std::thread(&Engine::scan_loop, this);
    scan_thread_.detach();

    // Start IPC server (Python bridge connects here)
    start_ipc_server();

    return true;
}

void Engine::stop() {
    running_    = false;
    ipc_running_= false;
}

void Engine::scan_loop() {
    while (running_.load()) {
        // Scan processes
        auto procs = proc_monitor_.scan();
        for (auto& p : procs) {
            if (proc_monitor_.is_suspicious(p)) {
                Threat t;
                t.id          = ++threat_id_counter_;
                t.type        = "process";
                t.description = "Suspicious process: " + p.name + " [PID:" + std::to_string(p.pid) + "]";
                t.source      = p.cmdline.substr(0, 100);
                t.level       = AlertLevel::DANGER;
                t.blocked     = false;
                t.timestamp   = std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count();

                // Auto-suspend suspicious process
                proc_monitor_.suspend_process(p.pid);
                t.blocked = true;
                add_threat(t);
                fire_alert(t);
            }
        }

        // Scan network
        auto conns = net_guardian_.scan_connections();
        for (auto& c : conns) {
            if (net_guardian_.is_suspicious_port(c.remote_port) &&
                c.state == "ESTABLISHED") {
                Threat t;
                t.id          = ++threat_id_counter_;
                t.type        = "network";
                t.description = "Dangerous port connection: " + c.remote_ip +
                                ":" + std::to_string(c.remote_port);
                t.level       = AlertLevel::WARNING;
                t.blocked     = false;
                t.timestamp   = std::chrono::duration_cast<std::chrono::milliseconds>(
                    std::chrono::system_clock::now().time_since_epoch()).count();
                net_guardian_.block_ip(c.remote_ip);
                t.blocked = true;
                add_threat(t);
                fire_alert(t);
            }
        }

        scans_completed_++;
        std::this_thread::sleep_for(std::chrono::seconds(scan_interval_sec_));
    }
}

void Engine::add_threat(Threat t) {
    std::lock_guard<std::mutex> lock(threats_mutex_);
    threats_.push_back(t);
    if (threats_.size() > MAX_THREATS)
        threats_.erase(threats_.begin());
}

void Engine::fire_alert(const Threat& t) {
    if (threat_cb_) threat_cb_(t);
}

SecurityStatus Engine::get_status() const {
    SecurityStatus s;
    s.version    = VERSION;
    s.status     = running_.load() ? "active" : "stopped";
    s.uptime_seconds = std::chrono::duration_cast<std::chrono::seconds>(
        std::chrono::steady_clock::now() - start_time_).count();
    s.threats_detected = (uint32_t)threats_.size();
    s.threats_blocked  = 0;
    {
        std::lock_guard<std::mutex> lock(threats_mutex_);
        for (auto& t : threats_) if (t.blocked) s.threats_blocked++;
    }
    s.scans_completed  = scans_completed_;
    s.firewall_active  = firewall_.is_active();
    s.apparmor_active  = true;
    s.cpu_usage        = const_cast<ProcessMonitor&>(proc_monitor_).get_cpu_usage();
    uint64_t total_kb  = 0;
    s.mem_used_mb      = const_cast<ProcessMonitor&>(proc_monitor_).get_mem_info(total_kb) / 1024;
    s.mem_total_mb     = total_kb / 1024;
    return s;
}

// ── JSON helpers ─────────────────────────────────────────────
std::string Engine::status_to_json() const {
    auto s = get_status();
    std::ostringstream o;
    o << "{"
      << "\"version\":\"" << s.version << "\","
      << "\"status\":\"" << s.status << "\","
      << "\"uptime\":" << s.uptime_seconds << ","
      << "\"threats_detected\":" << s.threats_detected << ","
      << "\"threats_blocked\":" << s.threats_blocked << ","
      << "\"scans_completed\":" << s.scans_completed << ","
      << "\"firewall\":\"" << (s.firewall_active ? "active" : "inactive") << "\","
      << "\"cpu_usage\":" << s.cpu_usage << ","
      << "\"mem_used_mb\":" << s.mem_used_mb << ","
      << "\"mem_total_mb\":" << s.mem_total_mb
      << "}";
    return o.str();
}

std::string Engine::threats_to_json(int count) const {
    std::lock_guard<std::mutex> lock(threats_mutex_);
    std::ostringstream o;
    o << "[";
    int start = std::max(0, (int)threats_.size() - count);
    for (int i = start; i < (int)threats_.size(); i++) {
        if (i > start) o << ",";
        auto& t = threats_[i];
        o << "{"
          << "\"id\":"          << t.id << ","
          << "\"type\":\""      << t.type << "\","
          << "\"description\":\"" << t.description << "\","
          << "\"level\":"       << (int)t.level << ","
          << "\"blocked\":"     << (t.blocked ? "true" : "false") << ","
          << "\"timestamp\":"   << t.timestamp
          << "}";
    }
    o << "]";
    return o.str();
}

// ── IPC Server (Unix socket — Python bridge connects here) ───
bool Engine::start_ipc_server() {
    ipc_running_ = true;
    ipc_thread_ = std::thread(&Engine::ipc_loop, this);
    ipc_thread_.detach();
    return true;
}

void Engine::ipc_loop() {
    ::unlink(SOCKET_PATH);
    int srv = ::socket(AF_UNIX, SOCK_STREAM, 0);
    if (srv < 0) return;

    struct sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path)-1);

    if (::bind(srv, (struct sockaddr*)&addr, sizeof(addr)) < 0) { ::close(srv); return; }
    ::chmod(SOCKET_PATH, 0666);
    ::listen(srv, 5);

    while (ipc_running_.load()) {
        int client = ::accept(srv, nullptr, nullptr);
        if (client < 0) continue;
        std::thread([this, client]() { handle_ipc_client(client); }).detach();
    }
    ::close(srv);
    ::unlink(SOCKET_PATH);
}

void Engine::handle_ipc_client(int fd) {
    char buf[4096] = {};
    ssize_t n = ::recv(fd, buf, sizeof(buf)-1, 0);
    if (n <= 0) { ::close(fd); return; }

    std::string cmd(buf, n);
    std::string response = handle_command(cmd);
    ::send(fd, response.c_str(), response.size(), 0);
    ::close(fd);
}

std::string Engine::handle_command(const std::string& cmd) {
    // Simple command parsing (JSON action field)
    if (cmd.find("get_status")  != std::string::npos) return status_to_json();
    if (cmd.find("get_threats") != std::string::npos) return threats_to_json(50);
    if (cmd.find("fw_enable")   != std::string::npos) {
        firewall_.enable();
        return "{\"ok\":true}";
    }
    if (cmd.find("fw_disable")  != std::string::npos) {
        firewall_.disable();
        return "{\"ok\":true}";
    }
    return "{\"error\":\"unknown command\"}";
}

} // namespace AmitShield

// ════════════════════════════════════════════════════════════
//  C-EXPORT API — Python ctypes bridge calls these
// ════════════════════════════════════════════════════════════
extern "C" {

void* amitshield_create() {
    return new AmitShield::Engine();
}

void amitshield_destroy(void* e) {
    delete static_cast<AmitShield::Engine*>(e);
}

int amitshield_start(void* e) {
    return static_cast<AmitShield::Engine*>(e)->start() ? 1 : 0;
}

void amitshield_stop(void* e) {
    static_cast<AmitShield::Engine*>(e)->stop();
}

int amitshield_is_running(void* e) {
    return static_cast<AmitShield::Engine*>(e)->is_running() ? 1 : 0;
}

const char* amitshield_get_status(void* e) {
    auto s = static_cast<AmitShield::Engine*>(e)->status_to_json();
    char* out = new char[s.size()+1];
    strcpy(out, s.c_str());
    return out;
}

const char* amitshield_get_threats(void* e, int count) {
    auto s = static_cast<AmitShield::Engine*>(e)->threats_to_json(count);
    char* out = new char[s.size()+1];
    strcpy(out, s.c_str());
    return out;
}

void amitshield_free_str(char* str) {
    delete[] str;
}

int amitshield_block_ip(void* e, const char* ip) {
    return static_cast<AmitShield::Engine*>(e)->network().block_ip(ip) ? 1 : 0;
}

int amitshield_firewall_enable(void* e) {
    return static_cast<AmitShield::Engine*>(e)->firewall().enable() ? 1 : 0;
}

int amitshield_firewall_disable(void* e) {
    return static_cast<AmitShield::Engine*>(e)->firewall().disable() ? 1 : 0;
}

} // extern "C"
