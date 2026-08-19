import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

MouseArea {
    id: compact

    readonly property var panel: root.appState ? root.appState.panel : null
    readonly property var windows: panel && panel.limit_windows ? panel.limit_windows : []
    readonly property string spritePath: panel && panel.sprite_path ? panel.sprite_path : ""
    readonly property var companion: root.appState ? root.appState.companion : null

    Layout.minimumWidth: row.implicitWidth
    Layout.preferredWidth: row.implicitWidth
    onClicked: root.expanded = !root.expanded

    function levelColor(level) {
        if (level === "crit")
            return Kirigami.Theme.negativeTextColor;
        if (level === "warn")
            return Kirigami.Theme.neutralTextColor;
        return Kirigami.Theme.positiveTextColor;
    }

    RowLayout {
        id: row
        anchors.fill: parent
        spacing: Kirigami.Units.smallSpacing

        // The companion. AnimatedImage plays the Gen-V GIF directly, which is
        // why no frame decoding was ported from the macOS ImageIO path.
        AnimatedImage {
            source: compact.spritePath ? "file://" + compact.spritePath : ""
            visible: compact.spritePath !== ""
            playing: visible
            fillMode: Image.PreserveAspectFit
            smooth: false          // pixel art
            Layout.preferredHeight: compact.height
            Layout.preferredWidth: compact.height
        }

        // The egg, while it incubates. Without this the companion slot is
        // simply blank until the first hatch, which reads as "broken".
        PlasmaComponents.Label {
            text: compact.companion && compact.companion.label ? compact.companion.label : ""
            visible: text.length > 0 && compact.spritePath === ""
            font.pixelSize: Math.round(compact.height * 0.45)
        }

        // Placeholder until the first state.json read lands.
        PlasmaComponents.Label {
            text: "…"
            visible: !compact.panel
            font.pixelSize: Math.round(compact.height * 0.5)
        }

        Repeater {
            model: compact.windows

            RowLayout {
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Label {
                    text: "|"
                    visible: index > 0
                    opacity: 0.5
                    font.pixelSize: Math.round(compact.height * 0.5)
                }

                PlasmaComponents.Label {
                    text: modelData.text
                    color: compact.levelColor(modelData.level)
                    font.pixelSize: Math.round(compact.height * 0.5)
                    font.bold: modelData.level === "crit"
                }
            }
        }

        // Off by default; the popup carries the detail.
        PlasmaComponents.Label {
            text: compact.panel ? compact.panel.tokens_text : ""
            visible: text.length > 0
            opacity: 0.8
            font.pixelSize: Math.round(compact.height * 0.45)
        }

        PlasmaComponents.Label {
            text: compact.panel ? compact.panel.cost_text : ""
            visible: text.length > 0
            opacity: 0.8
            font.pixelSize: Math.round(compact.height * 0.45)
        }
    }
}
