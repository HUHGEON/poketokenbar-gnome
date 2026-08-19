import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as Plasma5Support

Kirigami.FormLayout {
    id: page

    property alias cfg_showTokens: showTokens.checked
    property alias cfg_showCost: showCost.checked

    // Settings live in the daemon's config.json; poketokenctl is the only
    // writer so validation and defaults stay in one place.
    function push(key, value) {
        executable.exec("poketokenctl set " + key + " " + (value ? "true" : "false"));
    }

    QQC2.CheckBox {
        id: showTokens
        Kirigami.FormData.label: i18n("Show token count:")
        onToggled: page.push("show_tokens_in_menu", checked)
    }

    QQC2.CheckBox {
        id: showCost
        Kirigami.FormData.label: i18n("Show cost:")
        onToggled: page.push("show_cost_in_menu", checked)
    }

    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: function(sourceName) { disconnectSource(sourceName); }
        function exec(cmd) { connectSource(cmd); }
    }
}
