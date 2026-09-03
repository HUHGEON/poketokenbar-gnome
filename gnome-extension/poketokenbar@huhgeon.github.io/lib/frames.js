/* The part of sprite decoding that is not GdkPixbuf.
 *
 * Split out so it can be run under plain node: everything else in sprite.js
 * imports `gi://` and cannot be, which is how a walk that collected exactly one
 * frame of a 177-frame sprite shipped — the animation looked like a still PNG
 * on GNOME, and nothing executed the code that decided so.
 */

// Frames past this are dropped. Gen-V sprites run to a couple of hundred;
// anything far beyond that is not one of ours and is not worth the memory.
export const MAX_FRAMES = 240;
// GIF authoring commonly writes 0 or 10ms delays meaning "as fast as
// possible", which browsers clamp. Without a floor a sprite would spin the
// compositor.
export const MINIMUM_FRAME_MS = 20;
// Seconds added to a frame's delay when asking which frame comes next.
export const BOUNDARY_NUDGE = 0.001;

/**
 * Walk an animation iterator, collecting one entry per frame.
 *
 * Split out from `decodeFrames` and given its clock rather than reading one,
 * so the part that actually went wrong can be tested without GdkPixbuf.
 *
 * What went wrong: `iter.advance(null)` advances the animation to *now*, and
 * nothing in a tight decode loop takes any time, so it always reported "the
 * frame did not change" and the loop stopped at the second frame. Measured on
 * a real Gen-V sprite: 2 frames collected, **one** distinct image — a 178-frame
 * companion rendered as a still picture, which is exactly what it looked like.
 *
 * The clock is therefore advanced by each frame's own delay before advancing
 * the iterator, so the iterator is asked "what is showing at t = 0, 120ms,
 * 180ms…" and answers with the frames in order.
 *
 * `onFrame(delaySeconds)` builds whatever the caller wants out of the current
 * frame and returns it, or throws to stop. `sameAsFirst` reports whether the
 * frame now showing is the one the loop started on, which is how a loop's end
 * is recognised — the iterator itself never says so.
 *
 * Coming back to the first frame only counts once a different one has been
 * seen. A sprite holds a picture across several delay slots — a real Gen-V
 * sprite showed 29 distinct pictures across 177 slots — so "these pixels match
 * the first frame" on its own means "still on the first frame" far more often
 * than it means "wrapped", and treating it as a wrap ends the walk at one
 * frame.
 */
export function walkFrames(iter, clock, onFrame, sameAsFirst) {
    const frames = [];
    let elapsedMs = 0;
    let seenDifferent = false;
    let changed = true;
    for (let i = 0; i < MAX_FRAMES; i++) {
        // Nothing changed and nothing ever has: the file holds a single
        // picture. `sameAsFirst` cannot tell that apart from a held frame, but
        // the iterator can — it reports whether advancing moved the animation.
        if (i > 0 && !changed && !seenDifferent)
            break;
        const atFirst = i > 0 && sameAsFirst();
        // A GIF that has come back round to its first frame has given us the
        // whole loop; going on would repeat it.
        if (atFirst && seenDifferent)
            break;
        if (i > 0 && !atFirst)
            seenDifferent = true;
        // get_delay_time is milliseconds; framecap and the frames themselves
        // work in seconds, so the conversion happens once, here.
        const delay = Math.max(MINIMUM_FRAME_MS, iter.get_delay_time()) / 1000;
        let frame;
        try {
            frame = onFrame(delay);
        } catch (_e) {
            break;
        }
        frames.push(frame);
        elapsedMs += delay * 1000;
        // Nudged past the boundary, not exactly onto it. GdkPixbuf answers
        // "which frame is showing at time t", and at t equal to the first
        // frame's own delay that is still the first frame — so advancing by
        // the delay alone leaves the iterator where it was and the very next
        // comparison reads as "we have looped". Measured: it collected one
        // frame. The recorded duration stays exact; only the query moves.
        clock.advance(delay + BOUNDARY_NUDGE);
        changed = iter.advance(clock.value()) !== false;
        if (frames.length > 1 && elapsedMs > 60000)
            break;  // pathological file; keep what we have
    }
    return frames;
}

/** Whether two pixbufs hold the same picture.
 *
 * An exact comparison rather than a hash, and it costs almost nothing: two
 * different frames of a sprite differ within the first few bytes, so the scan
 * stops there. Only a true repeat reads to the end.
 */
export function samePixels(a, b) {
    if (a === null || b === null)
        return false;
    if (a.length !== b.length)
        return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i])
            return false;
    }
    return true;
}
