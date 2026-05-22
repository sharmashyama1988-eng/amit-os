cmake_minimum_required(VERSION 3.16)
project(AmitShieldCore VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ── Release build flags (max performance) ────────────────────
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# ── Security hardening flags ─────────────────────────────────
add_compile_options(
    -Wall -Wextra -Wpedantic
    -fstack-protector-strong
    -D_FORTIFY_SOURCE=2
    -fPIE
)
add_link_options(-Wl,-z,relro -Wl,-z,now)

find_package(Threads REQUIRED)

# ── Shared library (.so) — Python ctypes loads this ──────────
add_library(amitshield SHARED
    amitshield_core.cpp
)
target_include_directories(amitshield PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(amitshield PRIVATE Threads::Threads)
set_target_properties(amitshield PROPERTIES
    OUTPUT_NAME "amitshield"
    VERSION     ${PROJECT_VERSION}
    SOVERSION   1
    POSITION_INDEPENDENT_CODE ON
)

# ── Standalone daemon binary ──────────────────────────────────
add_executable(amitshield-daemon daemon_main.cpp)
target_link_libraries(amitshield-daemon PRIVATE amitshield Threads::Threads)
target_include_directories(amitshield-daemon PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

# ── Install targets ───────────────────────────────────────────
include(GNUInstallDirs)
install(TARGETS amitshield LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(TARGETS amitshield-daemon RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(FILES amitshield_core.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

message(STATUS "")
message(STATUS "╔══════════════════════════════════════╗")
message(STATUS "║  AmitShield C++ Core — Build Config  ║")
message(STATUS "║  Build Type : ${CMAKE_BUILD_TYPE}")
message(STATUS "║  CXX Std    : C++${CMAKE_CXX_STANDARD}")
message(STATUS "║  Install    : ${CMAKE_INSTALL_PREFIX}")
message(STATUS "╚══════════════════════════════════════╝")
message(STATUS "")
