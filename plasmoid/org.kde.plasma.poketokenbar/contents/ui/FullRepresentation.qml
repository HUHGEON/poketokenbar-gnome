import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.kirigami as Kirigami

PlasmaExtras.Representation {
    id: full

    readonly property var today: root.appState ? root.appState.today : null
    readonly property var providers: root.appState ? root.appState.providers : ({})
    readonly property var limits: root.appState && root.appState.limits ? root.appState.limits : null
    readonly property var companion: root.appState && root.appState.companion
                                     && root.appState.companion.stage
                                     ? root.appState.companion : null
    readonly property var shopItems: root.appState && root.appState.shop ? root.appState.shop : []
    readonly property var bagItems: root.appState && root.appState.bag ? root.appState.bag : []
    readonly property var dexItems: root.appState && root.appState.dex ? root.appState.dex : []

    Layout.minimumWidth: Kirigami.Units.gridUnit * 22
    Layout.minimumHeight: Kirigami.Units.gridUnit * 24

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

    function grouped(n) {
        return n ? n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "0";
    }

    // Every action goes through poketokenctl, so validation and defaults stay
    // in the daemon rather than being duplicated here.
    Plasma5Support.DataSource {
        id: runner
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName) { disconnectSource(sourceName); }
        function run(cmd) { connectSource(cmd); }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing

        QQC2.TabBar {
            id: tabs
            Layout.fillWidth: true
            QQC2.TabButton { text: i18n("Home") }
            QQC2.TabButton { text: i18n("Shop") }
            QQC2.TabButton { text: i18n("Bag") }
            QQC2.TabButton { text: i18n("Dex") }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex

            // ---------------- Home ----------------
            ColumnLayout {
                spacing: Kirigami.Units.smallSpacing

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
                        }
                    }
                }

                Kirigami.Separator { Layout.fillWidth: true }

                RowLayout {
                    Layout.fillWidth: true
                    visible: full.companion !== null
                    spacing: Kirigami.Units.largeSpacing

                    AnimatedImage {
                        source: full.companion && full.companion.sprite_path
                                ? "file://" + full.companion.sprite_path : ""
                        visible: full.companion !== null && full.companion.stage === "mon"
                        playing: visible
                        smooth: false
                        fillMode: Image.PreserveAspectFit
                        Layout.preferredWidth: Kirigami.Units.gridUnit * 3
                        Layout.preferredHeight: Kirigami.Units.gridUnit * 3
                    }

                    PlasmaComponents.Label {
                        text: "\u{1F95A}"
                        visible: full.companion !== null && full.companion.stage === "egg"
                        font.pixelSize: Kirigami.Units.gridUnit * 2
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        PlasmaComponents.Label {
                            font.bold: true
                            text: {
                                if (!full.companion)
                                    return "";
                                if (full.companion.stage === "egg")
                                    return i18n("Egg");
                                var bits = [full.companion.name
                                            ? full.companion.name
                                            : "#" + full.companion.species_id];
                                if (full.companion.is_shiny)
                                    bits.push(i18n("Shiny"));
                                if (full.companion.nature)
                                    bits.push(full.companion.nature);
                                return bits.join(" · ");
                            }
                        }

                        PlasmaComponents.ProgressBar {
                            Layout.fillWidth: true
                            from: 0
                            to: 1
                            value: full.companion
                                   ? (full.companion.stage === "egg"
                                      ? full.companion.egg_progress
                                      : full.companion.stage_progress)
                                   : 0
                        }

                        PlasmaComponents.Label {
                            opacity: 0.7
                            text: {
                                if (!full.companion)
                                    return "";
                                if (full.companion.stage === "egg")
                                    return i18n("%1% incubated",
                                                Math.round(full.companion.egg_progress * 100));
                                return i18n("Stage %1 of %2 · %3 · %4%",
                                            full.companion.stage_index + 1,
                                            full.companion.total_forms,
                                            full.companion.rarity,
                                            Math.round(full.companion.stage_progress * 100));
                            }
                        }
                    }
                }

                Kirigami.Separator { Layout.fillWidth: true }

                PlasmaExtras.Heading { level: 4; text: i18n("Today") }

                PlasmaExtras.Heading {
                    level: 2
                    text: full.today ? full.today.tokens_grouped : "—"
                }

                PlasmaComponents.Label {
                    text: full.today ? full.today.cost_text : ""
                    opacity: 0.7
                }

                Repeater {
                    model: full.providers ? Object.keys(full.providers) : []

                    RowLayout {
                        Layout.fillWidth: true
                        PlasmaComponents.Label { text: modelData }
                        Item { Layout.fillWidth: true }
                        PlasmaComponents.Label {
                            text: full.providers[modelData].total_tokens_text
                            opacity: 0.7
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // ---------------- Shop ----------------
            ColumnLayout {
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Label {
                    font.bold: true
                    text: full.companion
                          ? i18n("Wallet: %1", full.grouped(full.companion.spendable_tokens))
                          : ""
                }

                Repeater {
                    model: full.shopItems

                    RowLayout {
                        Layout.fillWidth: true

                        ColumnLayout {
                            spacing: 0
                            PlasmaComponents.Label { text: modelData.label }
                            PlasmaComponents.Label {
                                text: modelData.price_text
                                opacity: 0.7
                            }
                        }

                        Item { Layout.fillWidth: true }

                        QQC2.Button {
                            text: modelData.owned ? i18n("Owned") : i18n("Buy")
                            enabled: modelData.affordable
                            onClicked: runner.run("poketokenctl buy " + modelData.key)
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // ---------------- Bag ----------------
            ColumnLayout {
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Label {
                    text: i18n("Your bag is empty.")
                    visible: full.bagItems.length === 0
                    opacity: 0.7
                }

                Repeater {
                    model: full.bagItems

                    RowLayout {
                        Layout.fillWidth: true

                        PlasmaComponents.Label {
                            text: modelData.emoji
                            font.pixelSize: Kirigami.Units.gridUnit
                        }

                        PlasmaComponents.Label {
                            text: modelData.label + " ×" + modelData.count
                        }

                        Item { Layout.fillWidth: true }

                        PlasmaComponents.Label {
                            text: i18n("active")
                            visible: modelData.passive
                            opacity: 0.7
                        }

                        QQC2.Button {
                            text: i18n("Use")
                            visible: !modelData.passive
                            enabled: modelData.usable
                            onClicked: runner.run("poketokenctl use " + modelData.key)
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            // ---------------- Dex ----------------
            ColumnLayout {
                spacing: Kirigami.Units.smallSpacing

                PlasmaComponents.Label {
                    text: i18n("No graduates yet. Keep coding!")
                    visible: full.dexItems.length === 0
                    opacity: 0.7
                }

                PlasmaComponents.Label {
                    font.bold: true
                    text: i18n("%1 recorded", full.dexItems.length)
                    visible: full.dexItems.length > 0
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 4
                    columnSpacing: Kirigami.Units.smallSpacing
                    rowSpacing: Kirigami.Units.smallSpacing

                    Repeater {
                        model: full.dexItems

                        ColumnLayout {
                            spacing: 0

                            Image {
                                source: modelData.sprite_path
                                        ? "file://" + modelData.sprite_path : ""
                                smooth: false
                                fillMode: Image.PreserveAspectFit
                                Layout.preferredWidth: Kirigami.Units.gridUnit * 2.5
                                Layout.preferredHeight: Kirigami.Units.gridUnit * 2.5
                            }

                            PlasmaComponents.Label {
                                text: (modelData.is_shiny ? "✨" : "")
                                      + (modelData.name ? modelData.name
                                                        : "#" + modelData.final_id)
                                elide: Text.ElideRight
                                Layout.maximumWidth: Kirigami.Units.gridUnit * 3
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }
        }

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
