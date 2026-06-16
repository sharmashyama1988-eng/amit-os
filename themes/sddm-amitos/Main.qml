import QtQuick 2.0
import SddmComponents 2.0

Rectangle {
    width: 640
    height: 480
    color: "#0f172a" // AmitOS Dark Background

    Text {
        anchors.centerIn: parent
        text: "AmitOS"
        color: "#3b82f6" // Blue highlight
        font.pixelSize: 48
        font.bold: true
    }

    Clock {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 50
        color: "#94a3b8"
        timeFont.pixelSize: 36
        dateFont.pixelSize: 18
    }

    // A placeholder for a login area
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 100
        width: 300
        height: 150
        color: "#1e293b"
        radius: 10
        border.color: "#3b82f6"
        border.width: 2

        Text {
            anchors.centerIn: parent
            text: "Login Area Placeholder"
            color: "#94a3b8"
        }
    }
}
