/* Walking a GdkPixbuf animation.
 *
 * The GNOME companion rendered as a still picture. It was: the walk asked the
 * iterator to advance to "now", nothing in a decode loop takes any time, so it
 * always reported "the frame did not change" and stopped at the second frame.
 * Measured on a real Gen-V sprite: 2 frames collected, one distinct image.
 *
 * The fake below has the semantics that broke it — an iterator is a function of
 * a clock, and a sprite holds one picture across several delay slots.
 */

import assert from 'node:assert/strict';
import test from 'node:test';

import {MAX_FRAMES, samePixels, walkFrames} from
    '../../gnome-extension/poketokenbar@huhgeon.github.io/lib/frames.js';

/** An animation as a list of [pixels, delayMs], played on a clock. */
function fakeAnimation(script) {
    const bounds = [];
    let at = 0;
    for (const [pixels, delayMs] of script) {
        bounds.push({pixels, delayMs, from: at, to: at + delayMs});
        at += delayMs;
    }
    const total = at;
    let nowMs = 0;
    const current = () => {
        const t = total === 0 ? 0 : nowMs % total;
        return bounds.find(slot => t >= slot.from && t < slot.to) ?? bounds[0];
    };
    return {
        iter: {
            get_delay_time: () => current().delayMs,
            pixels: () => Uint8Array.from(current().pixels),
            advance(value) {
                const before = current();
                nowMs = value;
                return current() !== before;
            },
        },
        clock: (() => {
            let seconds = 0;
            return {
                advance(by) {
                    seconds += by;
                },
                value() {
                    return Math.round(seconds * 1000);
                },
            };
        })(),
    };
}

function walk(script) {
    const {iter, clock} = fakeAnimation(script);
    let first = null;
    const frames = walkFrames(
        iter, clock,
        delay => {
            if (first === null)
                first = iter.pixels();
            return {delay, pixels: iter.pixels()};
        },
        () => samePixels(first, iter.pixels()));
    return frames;
}

test('a looping animation is walked exactly once round', () => {
    const frames = walk([[[1], 100], [[2], 100], [[3], 100]]);
    assert.equal(frames.length, 3);
    assert.deepEqual(frames.map(f => f.pixels[0]), [1, 2, 3]);
});

test('the walked loop is as long as the source', () => {
    const frames = walk([[[1], 120], [[2], 60], [[3], 60]]);
    const seconds = frames.reduce((total, frame) => total + frame.delay, 0);
    assert.ok(Math.abs(seconds - 0.24) < 0.001, `loop was ${seconds}s`);
});

test('a picture held across several slots is not mistaken for the loop ending', () => {
    // The regression. Frames 1 and 2 repeat frame 0's picture, which a naive
    // "same as the first frame" check reads as having come back round.
    const frames = walk([[[9], 60], [[9], 60], [[9], 60], [[7], 60], [[8], 60]]);
    assert.equal(frames.length, 5, 'stopped early on a held frame');
});

test('advancing lands past the boundary, not on it', () => {
    // Advancing by exactly the delay leaves the iterator on the same frame,
    // because a frame shown "for 100ms from t=0" is still showing at t=100.
    const frames = walk([[[1], 100], [[2], 100]]);
    assert.deepEqual(frames.map(f => f.pixels[0]), [1, 2]);
});

test('a file holding one picture forever yields one frame', () => {
    // Real single-picture files are caught by is_static_image before they get
    // here, but a walk that cannot end is a hang, not a fallback.
    assert.equal(walk([[[1], 100]]).length, 1);
});

test('a pathological file is capped rather than decoded forever', () => {
    // Every frame distinct, so nothing ever looks like the first one.
    const script = Array.from({length: 1000}, (_value, i) => [[i % 251], 20]);
    assert.equal(walk(script).length, MAX_FRAMES);
});

test('a frame that cannot be built stops the walk instead of raising', () => {
    const {iter, clock} = fakeAnimation([[[1], 60], [[2], 60], [[3], 60]]);
    let built = 0;
    const frames = walkFrames(
        iter, clock,
        () => {
            if (built >= 2)
                throw new Error('decode failed');
            built += 1;
            return {};
        },
        () => false);
    assert.equal(frames.length, 2);
});

test('samePixels compares content, not identity', () => {
    assert.ok(samePixels(Uint8Array.from([1, 2]), Uint8Array.from([1, 2])));
    assert.ok(!samePixels(Uint8Array.from([1, 2]), Uint8Array.from([1, 3])));
    assert.ok(!samePixels(Uint8Array.from([1]), Uint8Array.from([1, 2])));
    assert.ok(!samePixels(null, Uint8Array.from([1])));
});
