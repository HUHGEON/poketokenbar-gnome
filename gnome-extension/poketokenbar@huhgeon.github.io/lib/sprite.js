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

import {DEFAULT_QUALITY, capFrameRate, frameFloor} from './framecap.js';

// GIF authoring commonly writes 0 or 10ms delays meaning "as fast as possible",
// which browsers clamp. Without a floor a sprite would spin the compositor.
const MINIMUM_FRAME_MS = 20;
// Frames past this are dropped. Gen-V sprites run ~55 frames; anything far
// beyond that is not one of ours and is not worth the memory.
const MAX_FRAMES = 240;

/** The Cogl context `set_bytes` wants, on the versions that want one.
 *
 * GNOME 48 gave `St.ImageContent.set_bytes` and `set_data` a new first
 * parameter. Resolved lazily and remembered: `global` does not exist until the
 * Shell is up, so reaching for it at import time throws before the extension
 * has even loaded.
 */
let coglContext;
let coglContextResolved = false;

function getCoglContext() {
    if (!coglContextResolved) {
        coglContextResolved = true;
        try {
            coglContext = global.stage.context.get_backend().get_cogl_context();
        } catch (_e) {
            // Older Shell: there is no such parameter to pass.
            coglContext = null;
        }
    }
    return coglContext;
}

/** `set_bytes` gained a leading `Cogl.Context` in GNOME 48.
 *
 * Tried in turn rather than version-checked: the manifest spans 45 to 51, and
 * a version check would be a second thing to keep correct across all of them.
 *
 * `new_with_preferred_size` needs no such handling — it has taken two ints in
 * every release, checked against the headers on both gnome-48 and main. An
 * earlier version of this file guessed otherwise while chasing the GrapheneSize
 * error, which turned out to come from the actor constructor instead.
 */
function setContentBytes(content, bytes, format, width, height, rowstride) {
    const context = getCoglContext();
    if (context) {
        try {
            content.set_bytes(context, bytes, format, width, height, rowstride);
            return;
        } catch (_e) {
            // Fall through to the older four-argument form.
        }
    }
    content.set_bytes(bytes, format, width, height, rowstride);
}

/** Content ready to assign, with the pixel size that goes with it.
 *
 * Matches the pattern GNOME Shell's own screenshot UI uses: an ImageContent
 * sized to the pixbuf, then the raw bytes with their format and rowstride.
 */
function frameFromPixbuf(pixbuf, delay) {
    const width = pixbuf.get_width();
    const height = pixbuf.get_height();
    const content = St.ImageContent.new_with_preferred_size(width, height);
    setContentBytes(
        content,
        pixbuf.read_pixel_bytes(),
        pixbuf.get_has_alpha() ? Cogl.PixelFormat.RGBA_8888 : Cogl.PixelFormat.RGB_888,
        width,
        height,
        pixbuf.get_rowstride());
    return {content, delay, width, height};
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
            return [frameFromPixbuf(animation.get_static_image(), 0)];
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
        // get_delay_time is milliseconds; framecap and the frames themselves
        // work in seconds, so the conversion happens once, here.
        const delay = Math.max(MINIMUM_FRAME_MS, iter.get_delay_time()) / 1000;
        let frame;
        try {
            frame = frameFromPixbuf(iter.get_pixbuf(), delay);
        } catch (_e) {
            break;
        }
        frames.push(frame);
        elapsedMs += delay * 1000;
        // advance() returns false when the frame did not change, which for a
        // loop means we are back where we started.
        if (!iter.advance(null) && i > 0)
            break;
        if (frames.length > 1 && elapsedMs > 60000)
            break;  // pathological file; keep what we have
    }
    return frames;
}

/* Decoded frames, keyed by path.
 *
 * Rebuilding a section makes fresh Sprite actors for files that have not
 * changed — the Pokedex grid alone is 24 of them — and decoding one Gen-V GIF
 * means uploading ~55 textures. Clutter content is refcounted and shareable
 * between actors, so a second Sprite on the same path can simply be handed the
 * frames the first one decoded.
 */
const frameCache = new Map();

// Bounded because the entries are textures living in the compositor, and a
// full Pokedex is a thousand species. Comfortably more than one popup shows.
const MAX_CACHED_SPRITES = 96;

function cachedFrames(path) {
    if (frameCache.has(path)) {
        // Re-inserted so the least recently used entry is the one that goes:
        // Map iterates in insertion order.
        const frames = frameCache.get(path);
        frameCache.delete(path);
        frameCache.set(path, frames);
        return frames;
    }
    const frames = decodeFrames(path);
    frameCache.set(path, frames);
    if (frameCache.size > MAX_CACHED_SPRITES)
        frameCache.delete(frameCache.keys().next().value);
    return frames;
}

/** Drop every decoded sprite. Called from disable(): the textures are held in
 * the compositor's memory, and a disabled extension must not be holding any. */
export function clearFrameCache() {
    frameCache.clear();
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
        // `size` is ours, and it must not reach the actor's constructor.
        //
        // Clutter.Actor already has a `size` property and its type is the boxed
        // graphene_size_t, so spreading this straight through made every
        // `new Sprite({size: 18})` throw "Wrong type number; boxed type
        // GrapheneSize expected" — which took the whole extension down before
        // it had drawn anything, because the panel builds a sprite first.
        const {size = 22, ...actorParams} = params;
        super._init({
            style_class: 'poketokenbar-sprite',
            // Pixel art: never smooth it.
            x_align: Clutter.ActorAlign.CENTER,
            y_align: Clutter.ActorAlign.CENTER,
            ...actorParams,
        });
        this._size = size;
        this._frames = [];
        this._index = 0;
        this._timer = 0;
        this._path = null;
        this._paused = false;
        this._quality = DEFAULT_QUALITY;
        // Frames as decoded, before the rate cap. Kept so changing quality does
        // not mean re-reading and re-uploading the whole GIF.
        this._sourceFrames = [];

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
        // A sprite that cannot be decoded must cost the numbers nothing. This
        // is the one place the extension touches an API whose signature moved
        // between the versions the manifest claims, and an uncaught throw here
        // takes the whole panel down — usage tracker included — over a picture.
        try {
            this._sourceFrames = cachedFrames(path);
        } catch (error) {
            logError(error, `PokeTokenBar: could not decode ${path}`);
            this._sourceFrames = [];
        }
        this._frames = capFrameRate(this._sourceFrames, frameFloor(this._quality));

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

    /** Change how smoothly this sprite animates.
     *
     * Re-caps the frames already decoded rather than reading the file again:
     * the pixels have not changed, only how many of them get drawn.
     */
    setQuality(quality) {
        if (quality === this._quality)
            return;
        this._quality = quality;
        if (this._sourceFrames.length === 0)
            return;
        this._stopTimer();
        this._frames = capFrameRate(this._sourceFrames, frameFloor(quality));
        this._index = 0;
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
        // The natural size is carried on the frame, not asked of the content.
        // Clutter.Content.get_preferred_size returns a boolean with width and
        // height as out-parameters, so in GJS it is [ok, width, height] —
        // destructuring two names off it silently binds the boolean to width.
        const {width, height} = frame;
        if (!width || !height) {
            this.set_size(this._size, this._size);
            return;
        }
        // contentMode "fit": the long edge touches the box, the aspect holds.
        const scale = Math.min(this._size / width, this._size / height);
        this.set_size(Math.max(1, Math.round(width * scale)),
            Math.max(1, Math.round(height * scale)));
    }

    _scheduleNext() {
        const frame = this._frames[this._index];
        // framecap works in seconds, GLib in milliseconds.
        const delay = Math.max(
            MINIMUM_FRAME_MS, Math.round((frame ? frame.delay : 0.1) * 1000));
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
