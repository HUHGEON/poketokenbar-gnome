import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami

PlasmaExtras.Representation {
    id: full

    readonly property var today: root.appState ? root.appState.today : null
    readonly property var providers: root.appState ? root.appState.providers : ({})

    Layout.minimumWidth: Kirigami.Units.gridUnit * 18
    Layout.minimumHeight: Kirigami.Units.gridUnit * 14

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing

        PlasmaExtras.Heading {
            level: 4
            text: i18n("Today")
        }

        PlasmaExtras.Heading {
            level: 1
            text: full.today ? full.today.tokens_grouped : "—"
        }

        PlasmaComponents.Label {
            text: full.today ? full.today.cost_text : ""
            opacity: 0.7
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Repeater {
            model: full.providers ? Object.keys(full.providers) : []

            RowLayout {
                Layout.fillWidth: true

                PlasmaComponents.Label { text: modelData }

                Item { Layout.fillWidth: true }

                PlasmaComponents.Label {
                    text: full.providers[modelData].total_tokens.toLocaleString()
                    opacity: 0.7
                }
            }
        }

        Item { Layout.fillHeight: true }

        PlasmaComponents.Label {
            visible: text.length > 0
            text: root.stateError.length > 0
                  ? root.stateError
                  : (root.appState && root.appState.errors.length > 0
                     ? root.appState.errors.join(", ")
                     : "")
            color: Kirigami.Theme.negativeTextColor
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }
}
