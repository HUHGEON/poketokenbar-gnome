/* framecap.js — capping a sprite's frame rate without slowing it down.
 *
 * Deliberately free of any gi:// import so it can be run and tested outside a
 * Shell. It is the one piece of sprite handling with an algorithm rather than
 * an API call, and the one place a plausible-looking version is wrong.
 *
 * Ports GIFDecoder.capFrameRate. The rule that matters: **decimate, do not
 * hold.** Raising each frame's own delay to the floor keeps every frame and
 * stretches the whole loop — upstream measured a Gen-V sprite (55 frames x
 * 0.05s = 2.75s) turning into a 22s loop at a 0.4s floor, an eighth of the
 * intended speed. Dropping frames instead keeps one loop the same length as
 * the source and only lowers how many frames it is drawn with.
 */

// Presets, in seconds per frame. These are frame-duration floors, so a larger
// number is fewer frames per second.
//
// None of them is 0. Native frame rate is an idle-wakeup regression: the cost
// of a frame is a recomposite, and a sprite that never stops asking for one
// keeps the machine awake. "saver" is the default for the same reason.
export const FRAME_FLOORS = {
    saver: 0.4,     // about 2.5fps
    balanced: 0.2,  // about 5fps
    smooth: 0.1,    // about 10fps
};

export const DEFAULT_QUALITY = 'saver';

export function frameFloor(quality) {
    return FRAME_FLOORS[quality] ?? FRAME_FLOORS[DEFAULT_QUALITY];
}

/**
 * Thin `frames` so no frame is shown for less than `floor` seconds.
 *
 * Each output frame is the first of its interval, held for the length of that
 * interval, so the total duration of one loop is unchanged.
 *
 * `frames` is `[{delay, ...}]` in seconds; everything else on a frame is
 * carried through untouched.
 */
export function capFrameRate(frames, floor) {
    if (!(floor > 0) || !Array.isArray(frames) || frames.length <= 1)
        return frames;

    const out = [];
    let held = null;
    let accumulated = 0;

    for (const frame of frames) {
        if (held === null)
            held = frame;
        accumulated += frame.delay;
        // The epsilon keeps floating-point accumulation from pushing an
        // interval one frame further than it should: 0.05 x 4 comes out as
        // 0.19999999999999998 as often as 0.20000000000000004.
        if (accumulated + 1e-9 >= floor) {
            out.push({...held, delay: accumulated});
            held = null;
            accumulated = 0;
        }
    }

    // A short tail is merged into the previous frame rather than emitted on its
    // own, so the loop still lasts exactly as long as the source did.
    if (held !== null && accumulated > 0) {
        if (out.length === 0)
            out.push({...held, delay: accumulated});
        else
            out[out.length - 1].delay += accumulated;
    }
    return out;
}
