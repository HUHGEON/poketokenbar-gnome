import QtQuick
import QtQuick.Controls as QQC2
import Qt.labs.platform as Platform
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property var appState: null
    property string stateError: ""

    readonly property var companion: appState && appState.companion && appState.companion.stage
                                     ? appState.companion : null
    readonly property var panel: appState ? appState.panel : null
    // Size comes from the shared config so the popup's slider drives it.
    readonly property int petSize: settings.floating_pet_size
                                   ? settings.floating_pet_size : 96
    readonly property bool bubblesEnabled: settings.floating_pet_bubble_alerts !== false

    property var settings: ({})
    property string bubbleText: ""

    readonly property string homeDir:
        Platform.StandardPaths.writableLocation(Platform.StandardPaths.HomeLocation)
            .toString().replace("file://", "")

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    // Same executable-engine read as the panel widget: Qt refuses XHR against
    // file:// without a session-wide security opt-out.
    Plasma5Support.DataSource {
        id: stateSource
        engine: "executable"
        connectedSources: ["cat " + root.homeDir + "/.local/state/poketokenbar/state.json"]
        interval: 3000

        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0)
                return;
            try {
                root.appState = JSON.parse(data["stdout"]);
                root.stateError = "";
            } catch (e) {
                root.stateError = i18n("waiting for poketokend");
            }
        }
    }

    Plasma5Support.DataSource {
        id: configSource
        engine: "executable"
        connectedSources: ["cat " + root.homeDir + "/.config/poketokenbar/config.json"]
        interval: 10000

        onNewData: function(sourceName, data) {
            if (data["exit code"] !== 0)
                return;
            try {
                root.settings = JSON.parse(data["stdout"]);
            } catch (e) {
                // No config yet; defaults apply.
            }
        }
    }

    Plasma5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName) { disconnectSource(sourceName); }
        function run(cmd) { connectSource(cmd); }
    }

    // A limit crossing pops a bubble, then clears itself. Edge-triggered on the
    // level so it does not re-fire every poll while the window stays high.
    property string lastLevel: ""
    onAppStateChanged: {
        if (!bubblesEnabled || !panel || !panel.limit_windows
                || panel.limit_windows.length === 0)
            return;
        var level = panel.limit_windows[0].level;
        if (level !== root.lastLevel) {
            root.lastLevel = level;
            if (level === "crit")
                showBubble(i18n("Limit almost gone!"));
            else if (level === "warn")
                showBubble(i18n("Getting close to the limit."));
        }
    }

    function showBubble(text) {
        root.bubbleText = text;
        bubbleTimer.restart();
    }

    Timer {
        id: bubbleTimer
        interval: 8000
        onTriggered: root.bubbleText = ""
    }

    fullRepresentation: Item {
        implicitWidth: root.petSize
        implicitHeight: root.petSize

        // Speech bubble above the pet.
        Rectangle {
            id: bubble
            visible: root.bubbleText !== ""
            anchors.bottom: petImage.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(bubbleLabel.implicitWidth + Kirigami.Units.largeSpacing,
                            root.petSize * 2.5)
            height: bubbleLabel.implicitHeight + Kirigami.Units.largeSpacing
            radius: Kirigami.Units.smallSpacing
            color: Kirigami.Theme.backgroundColor
            border.color: Kirigami.Theme.textColor
            border.width: 1
            opacity: 0.95

            PlasmaComponents.Label {
                id: bubbleLabel
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.largeSpacing
                text: root.bubbleText
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
            }
        }

        AnimatedImage {
            id: petImage
            anchors.fill: parent
            source: root.companion && root.companion.sprite_path
                    ? "file://" + root.companion.sprite_path : ""
            visible: root.companion !== null && root.companion.stage === "mon"
            playing: visible
            smooth: false            // pixel art
            fillMode: Image.PreserveAspectFit
        }

        PlasmaComponents.Label {
            anchors.centerIn: parent
            visible: root.companion !== null && root.companion.stage === "egg"
            text: "\u{1F95A}"
            font.pixelSize: root.petSize * 0.7
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            hoverEnabled: true

            onEntered: {
                if (root.companion)
                    root.showBubble(root.companion.status_message);
            }

            onClicked: function(mouse) {
                if (mouse.button === Qt.RightButton)
                    petMenu.popup();
                else if (root.companion)
                    root.showBubble(
                        i18n("%1 · %2 to %3",
                             root.companion.name ? root.companion.name : i18n("Egg"),
                             root.companion.remaining_text ? root.companion.remaining_text : "",
                             root.companion.goal ? root.companion.goal : i18n("hatch")));
            }
        }

        QQC2.Menu {
            id: petMenu

            QQC2.MenuItem {
                text: i18n("Today: %1", root.appState && root.appState.today
                                        ? root.appState.today.tokens_compact : "—")
                enabled: false
            }
            QQC2.MenuSeparator {}
            QQC2.MenuItem {
                text: i18n("Refresh now")
                onTriggered: runner.run("poketokenctl refresh")
            }
            QQC2.MenuItem {
                text: i18n("Hide floating pet")
                onTriggered: runner.run("poketokenctl set floating_pet_enabled false")
            }
        }
    }
}
