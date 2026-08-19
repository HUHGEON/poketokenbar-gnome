import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents

MouseArea {
    id: compact

    readonly property var panel: root.appState ? root.appState.panel : null

    Layout.minimumWidth: row.implicitWidth
    Layout.preferredWidth: row.implicitWidth
    onClicked: root.expanded = !root.expanded

    RowLayout {
        id: row
        anchors.fill: parent
        spacing: 4

        PlasmaComponents.Label {
            text: compact.panel ? compact.panel.tokens_text : "…"
            visible: text.length > 0
            font.pixelSize: Math.round(compact.height * 0.5)
        }

        PlasmaComponents.Label {
            text: compact.panel ? compact.panel.cost_text : ""
            visible: text.length > 0
            opacity: 0.8
            font.pixelSize: Math.round(compact.height * 0.45)
        }

        PlasmaComponents.Label {
            text: compact.panel ? compact.panel.limit_text : ""
            visible: text.length > 0
            opacity: 0.9
            font.pixelSize: Math.round(compact.height * 0.45)
        }
    }
}
