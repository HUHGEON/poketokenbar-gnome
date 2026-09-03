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

/**
 * A vertical St.BoxLayout, whichever way this Shell wants to be told.
 *
 * `vertical` is deprecated as of GNOME 48 and slated for removal, and its
 * replacement `orientation` is not documented as existing in 45. Rather than
 * pick one and hope, the property that is actually present wins — which is also
 * the only way one file can serve the whole 45-49 range this extension claims.
 */
export function verticalBox(params = {}) {
    const box = new St.BoxLayout(params);
    if ('orientation' in box)
        box.orientation = Clutter.Orientation.VERTICAL;
    else
        box.vertical = true;
    return box;
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
    const box = verticalBox({style_class: styleClass});
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
 * A settings row with a label on the left and an on/off control on the right.
 *
 * Not PopupSwitchMenuItem: that is a PopupBaseMenuItem and only works inside a
 * PopupMenu via addMenuItem. Adding one to an St container does not lay out —
 * the whole settings tab would have rendered as nothing.
 */
export function toggleRow(text, value, onToggle) {
    const control = new St.Button({
        label: value ? 'on' : 'off',
        style_class: value ? 'poketokenbar-toggle-on' : 'poketokenbar-toggle-off',
        can_focus: true,
        reactive: true,
        track_hover: true,
    });
    control.connect('clicked', () => onToggle(!value));
    const spacer = new St.Widget({x_expand: true});
    return row([label(text, 'poketokenbar-key'), spacer, control]);
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


/** Seconds until an ISO-8601 instant, or null if it is not one. */
export function remainingSeconds(iso) {
    if (!iso)
        return null;
    const remaining = new Date(iso).getTime() - Date.now();
    return Number.isNaN(remaining) ? null : remaining / 1000;
}

/** A coarse "two units" duration, the way the popover writes a countdown.
 *
 * Two units at most and never a smaller beside a larger: "6일 2시간",
 * "2시간 36분", "26초". Through the catalogue, because it used to build
 * "6d 2h" out of English letters — so a Korean install counted down in
 * English under a Korean label.
 */
export function duration(seconds, strings) {
    const total = Math.max(0, Math.floor(seconds));
    const days = Math.floor(total / 86400);
    const hours = Math.floor((total % 86400) / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const secs = total % 60;
    const unit = (key, value) => strings(key).replace('%1', String(value));
    if (days)
        return hours ? `${unit('unit_day', days)} ${unit('unit_hour', hours)}` : unit('unit_day', days);
    if (hours)
        return minutes ? `${unit('unit_hour', hours)} ${unit('unit_minute', minutes)}` : unit('unit_hour', hours);
    if (minutes)
        return secs ? `${unit('unit_minute', minutes)} ${unit('unit_second', secs)}` : unit('unit_minute', minutes);
    return unit('unit_second', secs);
}

/**
 * "2시간 36분" from an ISO-8601 instant.
 *
 * `resets_at` arrives as the raw timestamp the API returned. Rendering it
 * verbatim puts `2026-09-03T10:00:00Z` under the meter, which is data rather
 * than an answer to "how long have I got".
 */
export function resetsIn(iso, strings) {
    const remaining = remainingSeconds(iso);
    if (remaining === null)
        return '';
    if (remaining <= 0)
        return strings('resetting_now');
    return duration(remaining, strings);
}

/** "방금 갱신" / "3분 전 갱신" for the footer's freshness line.
 *
 * It used to return English regardless of the language, which is the one
 * string on screen at all times.
 */
export function ago(seconds, strings) {
    if (seconds === null || seconds === undefined)
        return '';
    if (seconds < 90)
        return strings('updated_just_now');
    return strings('updated_minutes_ago').replace('%1', String(Math.round(seconds / 60)));
}

/** A small pill, for badges like RAISING or a provider incident. */
export function badge(text, styleClass = 'poketokenbar-badge') {
    return label(text, styleClass);
}
