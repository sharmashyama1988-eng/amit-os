// ============================================================
//  AMITSHIELD DAEMON — Standalone C++ daemon entry point
//  Starts the engine + IPC server, waits for signals
// ============================================================

#include "amitshield_core.h"
#include <iostream>
#include <csignal>
#include <fstream>
#include <chrono>
#include <thread>

static AmitShield::Engine* g_engine = nullptr;

void signal_handler(int sig) {
    std::cout << "\n[AmitShield] Signal " << sig << " received — shutting down\n";
    if (g_engine) g_engine->stop();
    std::exit(0);
}

int main() {
    std::signal(SIGTERM, signal_handler);
    std::signal(SIGINT,  signal_handler);

    std::cout << "\n";
    std::cout << "  ╔══════════════════════════════════════════╗\n";
    std::cout << "  ║  AmitShield Daemon v" << AmitShield::VERSION << "             ║\n";
    std::cout << "  ║  Amit OS Security Engine                 ║\n";
    std::cout << "  ║  IPC Socket: " << AmitShield::SOCKET_PATH << "  ║\n";
    std::cout << "  ╚══════════════════════════════════════════╝\n\n";

    // Write PID file
    std::ofstream pid_file("/var/run/amitshield.pid");
    if (pid_file.is_open()) {
        pid_file << getpid();
        pid_file.close();
    }

    AmitShield::Engine engine;
    g_engine = &engine;

    // Register callbacks
    engine.set_threat_callback([](const AmitShield::Threat& t) {
        std::cout << "[THREAT] " << t.description << "\n";
    });

    engine.set_status_callback([](const AmitShield::SecurityStatus& s) {
        std::cout << "[STATUS] scans=" << s.scans_completed
                  << " threats=" << s.threats_detected << "\n";
    });

    if (!engine.start()) {
        std::cerr << "[AmitShield] Failed to start engine!\n";
        return 1;
    }

    std::cout << "[AmitShield] ✓ Engine running. Python bridge can now connect.\n\n";

    // Keep alive
    while (engine.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}
