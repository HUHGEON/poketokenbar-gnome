# What is verified, and what is not

The rule this port was built under: nothing gets moved across without being
compared against the source it came from, and without a test that fails when it
is wrong. This is the record of where that holds and where it does not.

## Verified mechanically

**Parsers.** All twelve providers were ported against the upstream Swift suite,
which carries the schemas and sample records. Their tests name the upstream case
they came from, so a rule that looks arbitrary can be traced to what it is for.

**Payload contract.** The extension reads `state.json`. A test enumerates the
keys the daemon actually emits and the keys the extension actually reads, and
fails on the difference — top-level blocks, per-block fields, list rows through
their own loop variable, catalogue keys, settings keys, and command names.

What it has caught so far:

- an invented `companion.celebration_kind`;
- shop rows carrying `label`, not `name`;
- the panel and the popup using different limit-row shapes under one name;
- `floating_pet_x/y` having no daemon default, so `config.load` dropped them and
  the pet would have jumped home on every restart;
- the panel sprite reading the companion's path rather than the pinned one,
  which left pinning with nowhere to take effect at all.

It also had a hole, found by injecting a typo rather than by reading it: string
literals were stripped before scanning, and template literals went with them, so
every `${row.field}` was invisible. Only the literal halves are dropped now.

**JavaScript syntax.** Node parses the same ESM grammar GJS does, so a stray
character fails a push rather than a desktop. Teardown of every timer, signal
and actor is asserted from the source, because a leak here is a leak inside the
compositor.

**Install.** CI installs from a clean checkout, starts the daemon, and fails
unless a state file lands.

**Environment independence.** Every path override is cleared before each test.
CI found this: the Cursor tests passed locally and failed on a runner, because a
provider given an explicit `home=` still reads the ambient XDG base. The suite
had been quietly reporting on whoever's machine it ran on.

## Not verified

**Rendering.** Nothing here proves an actor appears, that a GNOME API exists, or
that the popup is laid out sensibly. That needs a GNOME desktop.

**Two provider paths.** Cursor's and Kiro's SQLite stores are the only two whose
Linux location is not pinned by an upstream test; they follow the Electron and
XDG conventions. `CURSOR_DATA_DIR` and `KIRO_CLI_HOME` override them.

**Cursor's dashboard API.** Not ported. The local store is the fallback that
path already uses, so usage reads offline; usage that never touched this machine
will be missing.

**The claude.ai session key.** Deliberately skipped. It exists to avoid macOS
Keychain prompts, and Linux reads `~/.claude/.credentials.json` directly, so the
problem it solves is absent here. Upstream also records that the endpoint
rejects anything that does not look like a browser, which would have meant
shipping a network path that could not be verified from this machine.

## Running them

```bash
python -m pytest -q      # node must be on PATH, or the JavaScript checks skip
```

CI fails if those checks skip: a skip and a pass look identical in the summary,
and they are the only thing covering the extension.
