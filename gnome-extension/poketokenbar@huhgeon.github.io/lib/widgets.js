/* widgets.js — the small pieces every popup section builds out of.
 *
 * Kept together so the popup reads as layout rather than as St boilerplate, and
 * so a spacing or colour decision lands in one place instead of five.
 */

import Clutter from 'gi://Clutter';
import GObject from 'gi://GObject';
import St from 'gi://St';

/** Utilisation bands, matching limits.level() in the daemon. */
export function levelClass(level) {
    if (level === 'crit')
        return 'poketokenbar-crit';
    if (level === 'warn')
        return 'poketokenbar-warn';
    return 'poketokenbar-ok';
}

export function label(text, styleClass = '') {
    return new St.Label({
        text: text ?? '',
        style_class: styleClass,
        y_align: Clutter.ActorAlign.CENTER,
    });
}

export function row(children, styleClass = 'poketokenbar-row') {
    const box = new St.BoxLayout({style_class: styleClass});
    for (const child of children)
        box.add_child(child);
    return box;
}

export function column(children, styleClass = 'poketokenbar-column') {
    const box = new St.BoxLayout({vertical: true, style_class: styleClass});
    for (const child of children)
        box.add_child(child);
    return box;
}

/** A left label and a right value on one line. */
export function statLine(name, value, valueClass = 'poketokenbar-value') {
    const left = label(name, 'poketokenbar-key');
    const spacer = new St.Widget({x_expand: true});
    return row([left, spacer, label(value, valueClass)]);
}

/**
 * A horizontal progress bar.
 *
 * Drawn as two nested widgets rather than with a repaint handler: the fill only
 * ever changes width, and letting the layout do that keeps it out of the
 * compositor's paint path.
 */
export const Meter = GObject.registerClass(
class Meter extends St.Widget {
    _init(styleClass = 'poketokenbar-meter') {
        super._init({style_class: styleClass, x_expand: true});
        this._fill = new St.Widget({style_class: 'poketokenbar-meter-fill'});
        this.add_child(this._fill);
        this._fraction = 0;
        this.connect('notify::width', () => this._layoutFill());
    }

    /** `fraction` is 0..1; anything past 1 is clamped so a full bar stays full. */
    setFraction(fraction, level = 'ok') {
        this._fraction = Math.max(0, Math.min(1, fraction || 0));
        this._fill.style_class = `poketokenbar-meter-fill ${levelClass(level)}`;
        this._layoutFill();
    }

    _layoutFill() {
        const width = this.get_width();
        this._fill.set_size(Math.round(width * this._fraction), this.get_height());
    }
});

/** A section heading with a hairline under it. */
export function heading(text) {
    return label(text, 'poketokenbar-heading');
}

/** Text shown in place of a list that has nothing in it yet. */
export function placeholder(text) {
    return label(text, 'poketokenbar-placeholder');
}

/**
 * A flat button that looks like a row rather than a dialog button.
 *
 * `onClick` is wired here rather than by the caller so that every button in the
 * popup is reactive and track-hover in the same way — a button that is only
 * sometimes reactive reads as broken.
 */
export function button(text, onClick, styleClass = 'poketokenbar-button') {
    const widget = new St.Button({
        label: text,
        style_class: styleClass,
        can_focus: true,
        reactive: true,
        track_hover: true,
        x_expand: false,
    });
    widget.connect('clicked', () => onClick());
    return widget;
}

/** Compact "12,345" style text for a token count the daemon did not preformat. */
export function grouped(value) {
    // The daemon preformats everything it ships, so this is only for numbers
    // computed here. JS toLocaleString on a large float renders 8.55336e+07 in
    // some locales, hence the explicit grouping.
    const n = Math.round(value || 0);
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
