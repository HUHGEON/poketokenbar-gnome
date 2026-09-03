/* Runs the real loop detector under node, against the shape the sprite that
 * exposed the bug actually has.
 *
 * The decoder walks a GdkPixbuf animation, which never ends — the iterator
 * wraps round and hands out the same loop again — so where to stop is a
 * decision made from the frames themselves. Getting it wrong is not a crash:
 * it is a sprite that plays a third of its animation, or one that plays it
 * three times over. Neither is visible in a screenshot.
 */

import assert from 'node:assert/strict';
import test from 'node:test';

import {
    LOOP_SIGNATURE, loopLength,
} from '../../gnome-extension/poketokenbar@huhgeon.github.io/lib/framecap.js';

/** A sequence that repeats `body` forever, as the decoder would see it. */
const repeating = (body, times) =>
    Array.from({length: body.length * times}, (_, i) => body[i % body.length]);

test('a sequence that never repeats has no loop', () => {
    assert.equal(loopLength(['a', 'b', 'c', 'd', 'e']), 0);
});

test('the wrap is found at the start of the second pass', () => {
    assert.equal(loopLength(repeating(['a', 'b', 'c', 'd'], 3)), 4);
});

test('a pose struck twice is not the wrap', () => {
    // Lombre's idle returns to its opening frame at 33 of 112 and again at 59,
    // which is why one matching frame cannot end the walk: cutting there drops
    // two thirds of the animation. What follows the repeat is what tells them
    // apart.
    const body = ['a', 'b', 'c', 'd', 'a', 'e', 'f', 'g'];
    assert.equal(loopLength(repeating(body, 3)), body.length);
});

test('a two-frame blink loops at two', () => {
    assert.equal(loopLength(repeating(['a', 'b'], 6)), 2);
});

test('a wrap with no room left to confirm it is not claimed', () => {
    // Only the signature's worth of frames proves a wrap. Anything shorter is
    // the caller being asked to guess, and the decoder keeps walking instead.
    const almost = ['a', 'b', 'c', 'a', 'b'];
    assert.ok(almost.length < 3 + LOOP_SIGNATURE);
    assert.equal(loopLength(almost), 0);
});

test('nothing to walk is not a loop', () => {
    assert.equal(loopLength([]), 0);
    assert.equal(loopLength(null), 0);
    assert.equal(loopLength(['a']), 0);
});
