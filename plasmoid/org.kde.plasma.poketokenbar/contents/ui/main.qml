import QtQuick
import Qt.labs.platform as Platform
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root

    // Parsed state.json, or null before the first successful read.
    property var appState: null
    property string stateError: ""

    // QML cannot read $XDG_STATE_HOME, so the default location is used. The
    // daemon falls back to the same path, so the two agree unless the user
    // overrides XDG_STATE_HOME — which install.sh does not do.
    readonly property string homeDir:
        Platform.StandardPaths.writableLocation(Platform.StandardPaths.HomeLocation)
            .toString().replace("file://", "")
    readonly property string stateUrl:
        "file://" + homeDir + "/.local/state/poketokenbar/state.json"

    function reload() {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return;
            try {
                root.appState = JSON.parse(xhr.responseText);
                root.stateError = "";
            } catch (e) {
                // Keep the last good appState so a transient torn read does not
                // blank the panel. state.write() is atomic, so this is rare.
                root.stateError = i18n("Waiting for poketokend…");
            }
        };
        xhr.open("GET", root.stateUrl);
        xhr.send();
    }

    Component.onCompleted: reload()

    Timer {
        interval: 2000
        running: true
        repeat: true
        onTriggered: root.reload()
    }

    compactRepresentation: CompactRepresentation {}
    fullRepresentation: FullRepresentation {}
}
