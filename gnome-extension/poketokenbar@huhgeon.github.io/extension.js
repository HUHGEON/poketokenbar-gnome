/* PokeTokenBar for GNOME.
 *
 * The extension is a view over one file. Everything that reads logs, counts
 * tokens and raises the companion lives in the poketokend daemon; this puts it
 * on screen and sends back the handful of commands a click can produce.
 *
 * Lifecycle rules that matter in an extension, because getting them wrong leaks
 * inside the compositor rather than in a process someone can just close:
 *   - every timer and signal connected in enable() is undone in disable();
 *   - the desktop pet is an actor on the stage, so it must be destroyed too;
 *   - sprites stop animating while the session is locked, because nobody is
 *     watching and the frames still cost a redraw.
 */

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension, gettext as _} from 'resource:///org/gnome/shell/extensions/extension.js';

import * as Config from './lib/config.js';
import {DesktopPet} from './lib/pet.js';
import {Indicator} from './lib/indicator.js';
import {StateReader, bindTranslations} from './lib/state.js';

// Matches config.py's default pet size, and the size the daemon persists.
const DEFAULT_PET_SIZE = 96;

export default class PokeTokenBarExtension extends Extension {
    enable() {
        bindTranslations(_);

        this._reader = new StateReader();
        this._indicator = new Indicator(this._reader, null);
        Main.panel.addToStatusArea(this.uuid, this._indicator);

        this._pet = null;
        this._readerHandler = this._reader.connect('changed', () => this._syncPet());
        this._reader.start();

        // The pet is a stage actor and would keep animating behind the lock
        // screen, where it is both invisible and a redraw per frame.
        this._lockHandler = Main.sessionMode.connect('updated', () => this._syncPaused());
        this._syncPaused();
    }

    disable() {
        if (this._lockHandler) {
            Main.sessionMode.disconnect(this._lockHandler);
            this._lockHandler = 0;
        }
        if (this._readerHandler) {
            this._reader.disconnect(this._readerHandler);
            this._readerHandler = 0;
        }
        this._reader?.stop();
        this._reader = null;

        this._pet?.destroy();
        this._pet = null;

        this._indicator?.destroy();
        this._indicator = null;
    }

    /** Create, update or remove the pet to match the daemon's settings. */
    _syncPet() {
        const state = this._reader?.state;
        const config = state?.config ?? {};
        const wanted = Boolean(config.floating_pet_enabled);

        if (!wanted) {
            this._pet?.destroy();
            this._pet = null;
            return;
        }

        if (!this._pet) {
            this._pet = new DesktopPet(this._reader, {
                onActivate: kind => this._onPetActivated(kind),
                onSavePosition: (x, y) => {
                    // Persisted through the daemon's own config so the pet
                    // comes back where it was left, including after a reboot.
                    Config.set('floating_pet_x', x);
                    Config.set('floating_pet_y', y);
                },
            });
            // Below windows: the pet decorates the desktop, it does not sit on
            // top of what someone is working in.
            Main.layoutManager._backgroundGroup.add_child(this._pet);
            const size = Number(config.floating_pet_size) || DEFAULT_PET_SIZE;
            this._pet.setSize(size);
            this._pet.place(
                Number(config.floating_pet_x) || 80,
                Number(config.floating_pet_y) || 80);
        }

        this._pet.setSize(Number(config.floating_pet_size) || DEFAULT_PET_SIZE);
        this._pet.update(state);
        this._syncPaused();
    }

    _onPetActivated(_kind) {
        // Both buttons open the popup. Upstream's right-click menu duplicates
        // what the popup already offers, and a second menu here would be one
        // more surface to keep in step for no new capability.
        this._indicator?.menu.toggle();
    }

    _syncPaused() {
        const locked = Main.sessionMode.isLocked || Main.sessionMode.currentMode === 'unlock-dialog';
        this._indicator?.setPaused(locked);
        this._pet?.setPaused(locked);
    }
}
