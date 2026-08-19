import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami

PlasmaExtras.Representation {
    id: full

    readonly property var today: root.appState ? root.appState.today : null
    readonly property var providers: root.appState ? root.appState.providers : ({})
    readonly property var limits: root.appState && root.appState.limits ? root.appState.limits : null

    Layout.minimumWidth: Kirigami.Units.gridUnit * 20
    Layout.minimumHeight: Kirigami.Units.gridUnit * 20

    function levelColor(pct) {
        if (pct >= 95)
            return Kirigami.Theme.negativeTextColor;
        if (pct >= 80)
            return Kirigami.Theme.neutralTextColor;
        return Kirigami.Theme.positiveTextColor;
    }

    function resetIn(iso) {
        if (!iso)
            return "";
        var ms = new Date(iso).getTime() - Date.now();
        if (ms <= 0)
            return i18n("resetting now");
        var mins = Math.floor(ms / 60000);
        var hours = Math.floor(mins / 60);
        var days = Math.floor(hours / 24);
        if (days > 0)
            return i18n("resets in %1d %2h", days, hours % 24);
        if (hours > 0)
            return i18n("resets in %1h %2m", hours, mins % 60);
        return i18n("resets in %1m", mins);
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.smallSpacing

        // --- limits -------------------------------------------------------

        PlasmaExtras.Heading {
            level: 4
            text: full.limits && full.limits.plan
                  ? i18n("Limits · %1", full.limits.plan.toUpperCase())
                  : i18n("Limits")
        }

        Repeater {
            model: {
                if (!full.limits)
                    return [];
                var out = [];
                if (full.limits.session)
                    out.push({ "label": i18n("5-hour session"), "w": full.limits.session });
                if (full.limits.weekly)
                    out.push({ "label": i18n("Weekly"), "w": full.limits.weekly });
                return out;
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                RowLayout {
                    Layout.fillWidth: true

                    PlasmaComponents.Label { text: modelData.label }

                    Item { Layout.fillWidth: true }

                    PlasmaComponents.Label {
                        text: Math.round(modelData.w.utilization) + "%"
                        color: full.levelColor(modelData.w.utilization)
                        font.bold: true
                    }
                }

                PlasmaComponents.ProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    value: modelData.w.utilization
                }

                PlasmaComponents.Label {
                    text: full.resetIn(modelData.w.resets_at)
                    opacity: 0.7
                    font.pointSize: Kirigami.Theme.smallFont.pointSize
                }
            }
        }

        PlasmaComponents.Label {
            visible: !full.limits || (!full.limits.session && !full.limits.weekly)
            text: i18n("Limits unavailable")
            opacity: 0.7
        }

        Kirigami.Separator { Layout.fillWidth: true }

        // --- today --------------------------------------------------------

        PlasmaExtras.Heading {
            level: 4
            text: i18n("Today")
        }

        PlasmaExtras.Heading {
            level: 2
            text: full.today ? full.today.tokens_grouped : "—"
        }

        PlasmaComponents.Label {
            text: full.today ? i18n("%1 tokens", full.today.tokens_grouped) : ""
            visible: false
        }

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
