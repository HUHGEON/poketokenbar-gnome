/* sprite.js — animated Gen-V sprites as Shell actors.
 *
 * The Plasma port got this for free: QML's AnimatedImage plays a GIF directly.
 * St has no equivalent, so the frames are decoded with GdkPixbuf and swapped on
 * a timer, which is what the macOS app does with ImageIO.
 *
 * Cheap on purpose. A Shell extension runs inside the compositor process, so a
 * frame swap here is a local content assignment with no IPC — but a leaked
 * timer is a leak in the compositor, which is why every actor stops its own on
 * destroy.
 */

import Clutter from 'gi://Clutter';
import Cogl from 'gi://Cogl';
import GdkPixbuf from 'gi://GdkPixbuf';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

// GIF authoring commonly writes 0 or 10ms delays meaning "as fast as possible",
// which browsers clamp. Without a floor a sprite would spin the compositor.
const MINIMUM_FRAME_MS = 20;
// Frames past this are dropped. Gen-V sprites run ~55 frames; anything far
// beyond that is not one of ours and is not worth the memory.
const MAX_FRAMES = 240;

/** One decoded frame: content ready to assign, and how long to hold it. */
function contentFromPixbuf(pixbuf) {
    const content = St.ImageContent.new_with_preferred_size(
        pixbuf.get_width(), pixbuf.get_height());
    content.set_bytes(
        pixbuf.read_pixel_bytes(),
        pixbuf.get_has_alpha() ? Cogl.PixelFormat.RGBA_8888 : Cogl.PixelFormat.RGB_888,
        pixbuf.get_width(),
        pixbuf.get_height(),
        pixbuf.get_rowstride());
    return content;
}

/**
 * Decode every frame of a sprite file.
 *
 * Returns [] when the file cannot be read, so callers fall back to a glyph
 * rather than rendering a broken image. A still PNG comes back as one frame,
 * which is also what a GIF with a single frame should look like.
 */
export function decodeFrames(path) {
    if (!path)
        return [];
    let animation;
    try {
        animation = GdkPixbuf.PixbufAnimation.new_from_file(path);
    } catch (_e) {
        return [];
    }

    if (animation.is_static_image()) {
        try {
            return [{content: contentFromPixbuf(animation.get_static_image()), delay: 0}];
        } catch (_e) {
            return [];
        }
    }

    const frames = [];
    // Walking the iterator by its own advertised delays is what keeps the loop
    // the same length as the source; stepping by a fixed interval would play
    // the animation at the wrong speed.
    let iter;
    try {
        // Passing null starts the iterator at "now"; delays are then relative.
        iter = animation.get_iter(null);
    } catch (_e) {
        return [];
    }

    let elapsedMs = 0;
    for (let i = 0; i < MAX_FRAMES; i++) {
        let content;
        try {
            content = contentFromPixbuf(iter.get_pixbuf());
        } catch (_e) {
            break;
        }
        const delay = Math.max(MINIMUM_FRAME_MS, iter.get_delay_time());
        frames.push({content, delay});
        elapsedMs += delay;
        // advance() returns false when the frame did not change, which for a
        // loop means we are back where we started.
        if (!iter.advance(null) && i > 0)
            break;
        if (frames.length > 1 && elapsedMs > 60000)
            break;  // pathological file; keep what we have
    }
    return frames;
}

/**
 * An actor that plays a decoded sprite.
 *
 * `size` is the square box the sprite fits inside. Gen-V GIF canvases are not
 * square and differ per species — Spoink is 36x66, Pikachu 50x46 — so a plain
 * size x size assignment stretches them. The aspect is preserved and the actor
 * asks for the fitted width, which is also what keeps the panel from jumping
 * as the companion evolves.
 */
export const Sprite = GObject.registerClass(
class Sprite extends St.Widget {
    _init(params = {}) {
        const size = params.size ?? 22;
        super._init({
            style_class: 'poketokenbar-sprite',
            // Pixel art: never smooth it.
            x_align: Clutter.ActorAlign.CENTER,
            y_align: Clutter.ActorAlign.CENTER,
            ...params,
        });
        this._size = size;
        this._frames = [];
        this._index = 0;
        this._timer = 0;
        this._path = null;
        this._paused = false;

        this.connect('destroy', () => this._stopTimer());
    }

    /** Point the actor at a sprite file. A repeat of the same path is a no-op.
     *
     * Re-decoding on every poll would rebuild ~55 textures every two seconds
     * for a sprite that had not changed.
     */
    setPath(path) {
        if (path === this._path)
            return;
        this._path = path;
        this._stopTimer();
        this._index = 0;
        this._frames = decodeFrames(path);

        if (this._frames.length === 0) {
            this.content = null;
            this.visible = false;
            return;
        }
        this.visible = true;
        this._applyFrame(0);
        if (this._frames.length > 1 && !this._paused)
            this._scheduleNext();
    }

    setSize(size) {
        if (size === this._size)
            return;
        this._size = size;
        if (this._frames.length > 0)
            this._applyFrame(this._index);
    }

    /** Stop or resume animating without discarding the decoded frames.
     *
     * Used when the popup closes and while the screen is locked or blanked:
     * a sprite nobody can see must not keep waking the compositor.
     */
    setPaused(paused) {
        if (paused === this._paused)
            return;
        this._paused = paused;
        if (paused)
            this._stopTimer();
        else if (this._frames.length > 1)
            this._scheduleNext();
    }

    _applyFrame(index) {
        const frame = this._frames[index];
        if (!frame)
            return;
        this.content = frame.content;
        const [width, height] = frame.content.get_preferred_size();
        // contentMode "fit": the long edge touches the box, the aspect holds.
        const scale = Math.min(this._size / width, this._size / height);
        this.set_size(Math.max(1, Math.round(width * scale)),
            Math.max(1, Math.round(height * scale)));
    }

    _scheduleNext() {
        const frame = this._frames[this._index];
        const delay = frame ? frame.delay : MINIMUM_FRAME_MS;
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, delay, () => {
            this._timer = 0;
            this._index = (this._index + 1) % this._frames.length;
            this._applyFrame(this._index);
            this._scheduleNext();
            return GLib.SOURCE_REMOVE;
        });
    }

    _stopTimer() {
        if (this._timer) {
            GLib.Source.remove(this._timer);
            this._timer = 0;
        }
    }
});
