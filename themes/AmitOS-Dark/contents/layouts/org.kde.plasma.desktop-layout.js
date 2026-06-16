// AmitOS-Dark — Default KDE Plasma Desktop Layout
// Creates a bottom panel with Kickoff launcher, Task Manager, System Tray, and Digital Clock.

var panel = new Panel();
panel.location = "bottom";
panel.height = 44;
panel.floating = false;

// Application Launcher (Kickoff)
var kickoff = panel.addWidget("org.kde.plasma.kickoff");
kickoff.currentConfigGroup = ["Shortcuts"];
kickoff.writeConfig("global", "Alt+F1");

// Task Manager
var tasks = panel.addWidget("org.kde.plasma.taskmanager");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("grouping", 1);          // Group by application
tasks.writeConfig("sortingStrategy", 1);   // Sort by activity

// Spacer (flexible)
panel.addWidget("org.kde.plasma.panelspacer");

// System Tray
var tray = panel.addWidget("org.kde.plasma.systemtray");
tray.currentConfigGroup = ["General"];
tray.writeConfig("extraItems", [
    "org.kde.plasma.networkmanagement",
    "org.kde.plasma.volume",
    "org.kde.plasma.battery",
    "org.kde.plasma.bluetooth"
]);

// Digital Clock
var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateFormat", "shortDate");
clock.writeConfig("use24hFormat", 2);      // 24-hour time

// Desktop/Show Desktop button
panel.addWidget("org.kde.plasma.showdesktop");
