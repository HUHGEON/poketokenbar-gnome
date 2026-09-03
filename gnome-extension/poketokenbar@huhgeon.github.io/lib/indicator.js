/* indicator.js — the panel button and the popup it opens.
 *
 * The panel shows the companion (or the pinned species) beside the limit
 * percentages, coloured by how close they are. The popup carries the detail,
 * in tabs that mirror the macOS app's.
 */

import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

import * as Commands from './commands.js';
import {DEFAULT_QUALITY} from './framecap.js';
import {Sprite} from './sprite.js';
import {
    BagSection, CollectionSection, HomeSection, SettingsSection, ShopSection,
} from './sections.js';
import {ago, button, label, levelClass, row, verticalBox} from './widgets.js';

// The popup is a fixed width so the Pokedex grid never reflows mid-browse.
const POPUP_WIDTH = 380;

export const Indicator = GObject.registerClass(
class Indicator extends PanelMenu.Button {
    _init(reader, settings) {
        super._init(0.5, 'PokeTokenBar', false);
        this._reader = reader;
        this._settings = settings;

        // --- panel ----------------------------------------------------------
        this._panelBox = new St.BoxLayout({style_class: 'poketokenbar-panel'});
        this._sprite = new Sprite({size: 18});
        this._eggLabel = label('', 'poketokenbar-panel-text');
        this._limitBox = new St.BoxLayout({style_class: 'poketokenbar-panel-limits'});
        this._tokensLabel = label('', 'poketokenbar-panel-text');
        this._costLabel = label('', 'poketokenbar-panel-text');

        this._panelBox.add_child(this._sprite);
        this._panelBox.add_child(this._eggLabel);
        this._panelBox.add_child(this._limitBox);
        this._panelBox.add_child(this._tokensLabel);
        this._panelBox.add_child(this._costLabel);
        this.add_child(this._panelBox);

        // --- popup ----------------------------------------------------------
        this._sections = {
            home: new HomeSection(reader),
            shop: new ShopSection(reader),
            bag: new BagSection(reader),
            collection: new CollectionSection(reader),
            settings: new SettingsSection(reader),
        };
        this._currentTab = 'home';

        const item = new PopupMenu.PopupBaseMenuItem({
            reactive: false, can_focus: false, style_class: 'poketokenbar-popup',
        });
        const content = verticalBox({
            style_class: 'poketokenbar-content', x_expand: true,
        });
        content.set_width(POPUP_WIDTH);

        this._tabBar = row([], 'poketokenbar-tabs');
        content.add_child(this._tabBar);

        this._body = new St.ScrollView({
            style_class: 'poketokenbar-scroll',
            // Never horizontal: the popup is a fixed width, so a sideways
            // scrollbar would only ever mean something is laid out wrong.
            hscrollbar_policy: St.PolicyType.NEVER,
            vscrollbar_policy: St.PolicyType.AUTOMATIC,
            y_expand: true,
        });
        this._bodyBox = verticalBox({x_expand: true});
        this._body.set_child(this._bodyBox);
        content.add_child(this._body);

        this._footer = label('', 'poketokenbar-footer');
        content.add_child(this._footer);
        content.add_child(row([
            button('↻', () => Commands.refresh()),
            new St.Widget({x_expand: true}),
            // The daemon has handled these all along; without a control they
            // were reachable only from poketokenctl, which is not where anyone
            // would look for "move my Pokedex to another machine".
            button('Export', () => Commands.exportSave(this._savePath())),
            button('Import', () => Commands.importSave(this._savePath())),
        ], 'poketokenbar-actions'));

        item.add_child(content);
        this.menu.addMenuItem(item);

        // Animation is the compositor's cost, and nobody is watching a closed
        // popup — but the panel sprite keeps running, since that one is visible.
        this.menu.connect('open-state-changed', (_menu, open) => {
            for (const [name, section] of Object.entries(this._sections))
                section.visible = open && name === this._currentTab;
            if (open)
                this._render();
        });

        this._buildTabs();
        this._readerHandler = reader.connect('changed', () => this._render());
        this._render();
    }

    destroy() {
        if (this._readerHandler) {
            this._reader.disconnect(this._readerHandler);
            this._readerHandler = 0;
        }
        super.destroy();
    }

    _buildTabs() {
        this._tabBar.destroy_all_children();
        this._bodyBox.destroy_all_children();
        for (const [name, key] of [
            ['home', 'home'], ['shop', 'shop'], ['bag', 'bag'],
            ['collection', 'collection'], ['settings', 'refresh'],
        ]) {
            const tab = button(this._reader.text(key), () => this._selectTab(name),
                'poketokenbar-tab');
            this._tabBar.add_child(tab);
            this._bodyBox.add_child(this._sections[name]);
            this._sections[name].visible = name === this._currentTab;
        }
    }

    _selectTab(name) {
        this._currentTab = name;
        for (const [key, section] of Object.entries(this._sections))
            section.visible = key === name;
        this._render();
    }

    /** Where a save is written to and read from.
     *
     * A fixed, predictable path rather than a file chooser: an extension has no
     * portal-backed dialog available to it, and inventing one would be more
     * surface than the feature is worth.
     */
    _savePath() {
        return GLib.build_filenamev([
            GLib.get_home_dir(), 'poketokenbar-save.json',
        ]);
    }

    /** Paint everything from the latest snapshot. */
    _render() {
        const state = this._reader.state;
        this._renderPanel(state);
        // Only the visible tab is rebuilt: the others would throw their
        // children away again before anyone saw them.
        this._sections[this._currentTab]?.update(state);
        this._renderFooter(state);
    }

    _renderPanel(state) {
        const panel = state?.panel;
        // The sprite is decoration; the percentages are the point. Keep one
        // from taking the other with it.
        try {
            this._sprite.setQuality(state?.config?.animation_quality ?? DEFAULT_QUALITY);
            this._sprite.setPath(panel?.sprite_path || null);
        } catch (error) {
            logError(error, 'PokeTokenBar: panel sprite');
        }
        const companion = state?.companion;

        // The egg has no sprite of its own, so its percentage stands in —
        // leaving the slot blank until the first hatch reads as broken.
        const eggText = !panel?.sprite_path && companion?.label ? companion.label : '';
        this._eggLabel.text = eggText;
        this._eggLabel.visible = eggText !== '';

        this._limitBox.destroy_all_children();
        const windows = panel?.limit_windows ?? [];
        // A different row shape from limits.session: the panel ships text and
        // a level already computed against the user's own thresholds, while the
        // popup gets the raw utilisation. Same idea, not the same fields.
        windows.forEach((panelWindow, index) => {
            if (index > 0)
                this._limitBox.add_child(label('|', 'poketokenbar-panel-sep'));
            this._limitBox.add_child(label(
                panelWindow.text, `poketokenbar-panel-text ${levelClass(panelWindow.level)}`));
        });

        this._tokensLabel.text = panel?.tokens_text ?? '';
        this._tokensLabel.visible = this._tokensLabel.text !== '';
        this._costLabel.text = panel?.cost_text ?? '';
        this._costLabel.visible = this._costLabel.text !== '';

        // Before the first successful read there is nothing at all to show, and
        // an empty panel button is invisible and unclickable.
        const empty = !panel?.sprite_path && eggText === '' && windows.length === 0 &&
            this._tokensLabel.text === '' && this._costLabel.text === '';
        this._eggLabel.visible = this._eggLabel.visible || empty;
        if (empty)
            this._eggLabel.text = '…';
    }

    _renderFooter(state) {
        if (this._reader.error) {
            this._footer.text = this._reader.error;
            return;
        }
        if (this._reader.isStale()) {
            this._footer.text = this._reader.text('stale_warning');
            return;
        }
        const errors = state?.errors ?? [];
        if (errors.length > 0) {
            this._footer.text = errors.join(', ');
            return;
        }
        // Freshness, so a working daemon looks different from a stopped one
        // before the ten-minute staleness threshold is anywhere near.
        if (state?.scanning) {
            this._footer.text = 'scanning…';
            return;
        }
        const age = this._reader.ageSeconds();
        this._footer.text = age === null ? '' : `Updated ${ago(age)}`;
    }

    /** Pause every sprite in the extension — used while the session is locked. */
    setPaused(paused) {
        this._sprite.setPaused(paused);
    }
});
