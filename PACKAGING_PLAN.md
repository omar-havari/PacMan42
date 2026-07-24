# Packaging Plan — Pac-Man → Itch.io

This document is the step-by-step recipe for turning the source game into a
downloadable, installable build published on **Itch.io**, as required by
**Chapter 7 "Project packaging"** of the subject.

It explains **every file, code change, package, and configuration** involved and
**what each one does**. Follow the steps in order. Nothing here changes gameplay —
it only wraps the finished game so a player (or reviewer) can install and run it
without a Python environment.

---

## 0. The goal (what the subject demands)

From Chapter 7, the deliverable must:

1. Be **installable and launchable from a public platform** (Steam/Itch.io) as a
   **free, unlisted/private** build.
2. Be **fully functional** when packaged.
3. Ship **minimal in-package instructions** (controls, options, configuration).
4. Keep the **full source + the packaging script/spec at the repo root**.
5. Be **regenerable on demand** during peer review.

**Chosen strategy:** **Itch.io** (free, accepts an uploaded folder, supports
unlisted builds) + **PyInstaller one-folder** bundle (a standalone folder with an
`.exe` and all assets; the player needs no Python installed).

---

## 1. The two things that make this work

A packaged app is different from `python pac-man.py config.json` in two ways, and
both need a small code change **before** bundling:

| Problem | Why it breaks when frozen | Fix (this plan) |
|---|---|---|
| **Asset paths** | Your code finds `assets/` relative to each source file's location on disk. Inside a PyInstaller bundle there is no normal source tree — files live in a temp unpack dir exposed as `sys._MEIPASS`. | A single `resource_path` helper (`src/resources.py`) that returns the bundle dir when frozen, the project root otherwise. |
| **Config argument** | The game **requires** a `config.json` CLI argument and exits otherwise. A player double-clicking the `.exe` passes no arguments. | Make the entry point fall back to a **bundled default `config.json`** when no argument is given. |

Everything else (the `.spec`, build script, Itch.io upload) is packaging config,
not code.

---

## 2. Packages you need to install

Add these to your dev environment (inside your venv):

| Package | What it is | What it does here |
|---|---|---|
| **PyInstaller** | A tool that freezes a Python program into a standalone executable + its dependencies. | Produces the `dist/pacman/` folder you upload to Itch.io. Reads `pacman.spec`. |
| **butler** | Itch.io's official command-line uploader (a standalone binary, *not* a pip package). | Pushes the built folder to your Itch.io page and versions it. Also used to regenerate/re-upload during review. |

Install PyInstaller (add it to `requirements.txt` too — see Step 8):

```bash
pip install pyinstaller
```

Install butler (download the binary from Itch.io — see Step 7). It is **not**
`pip install`-able.

---

## 3. Code change #1 — the resource resolver

### File to create: `src/resources.py`

**What it does:** one place that answers "where do my data files live *right now*?"
When running from source it returns the project root; when running as a frozen
PyInstaller app it returns `sys._MEIPASS` (the bundle's temp dir). Every asset
and the default config are resolved through it, so the same code works both ways.

```python
"""Resolve on-disk resource paths for both source and packaged (frozen) runs.

When the game runs from source, data files live next to the project root. When
it runs as a PyInstaller bundle, they are unpacked into ``sys._MEIPASS``. This
module hides that difference so every asset lookup works in both cases.
"""
import os
import sys


def base_path() -> str:
    """Return the directory that contains ``assets/`` and ``config.json``.

    Frozen (PyInstaller) builds expose the bundled data under ``sys._MEIPASS``;
    a normal source checkout uses the project root (the parent of ``src/``).
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass is not None:
            return str(meipass)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_dir() -> str:
    """Absolute path to the bundled ``assets/`` directory."""
    return os.path.join(base_path(), "assets")


def default_config_path() -> str:
    """Absolute path to the bundled default ``config.json``."""
    return os.path.join(base_path(), "config.json")
```

> **Why `getattr(sys, "_MEIPASS", None)` and `str(...)`?** `sys._MEIPASS` only
> exists inside a frozen app, so `getattr` avoids an `AttributeError` when running
> from source, and wrapping in `str(...)` keeps `mypy --warn-return-any` happy
> (so `make lint` still passes).

### Files to edit: replace the repeated `_ASSETS` line in 5 files

Each of these files currently has the **identical** line:

```python
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
```

Replace it in **all five** with:

```python
from src.resources import asset_dir

_ASSETS = asset_dir()
```

The five files:

| File | Assets it loads |
|---|---|
| `src/GameDemo.py` | HUD + centred-text font (`PressStart2P-Regular.ttf`) |
| `src/Player.py` | Pac-Man sprites + font |
| `src/ghost.py` | Ghost sprite |
| `src/pacgums.py` | Pac-gum + super-pac-gum sprites |
| `src/screens.py` | Menu font + title image |

**What this achieves:** nothing changes when you run from source (`_ASSETS`
still points at `<root>/assets`), but inside the bundle `_ASSETS` now points at
`<bundle>/assets`, so fonts and images load correctly in the packaged game.

---

## 4. Code change #2 — default config fallback

### File to edit: `pac-man.py`

**What it does:** lets the game launch with **no arguments** (double-click / Itch.io
launch) by falling back to the bundled `config.json`, while still accepting an
explicit `config.json` argument on the command line exactly as the subject's
usage spec requires.

Replace the current argument check:

```python
if len(sys.argv) != 2 or not sys.argv[1].endswith(".json"):
    print("Usage: python pac-man.py config.json")
    sys.exit(1)

config_file_path = sys.argv[1]
```

with:

```python
if len(sys.argv) == 1:
    # No argument (e.g. launched from Itch.io by double-click): use the
    # bundled default config that ships inside the package.
    config_file_path = default_config_path()
elif len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
    config_file_path = sys.argv[1]
else:
    print("Usage: python pac-man.py [config.json]")
    sys.exit(1)
```

and add the import at the top:

```python
from src.resources import default_config_path
```

> **Safe by design:** your `Config` class already tolerates a missing/broken file
> by falling back to defaults, so even if the bundled config were absent the game
> would still start. The CLI form (`python pac-man.py config.json`) is unchanged,
> so nothing in the review's "launch from the command line" spec breaks.

---

## 5. In-package instructions

### File to create: `CONTROLS.txt` (repo root)

**What it does:** satisfies the Chapter 7 requirement to *"provide minimal
in-package instructions (controls, options, configuration)."* The `.spec` bundles
it next to the executable so it ships inside the download.

```
PAC-MAN — Controls & Options
============================

MOVE          Arrow keys (or WASD)
PAUSE         P or ESC
CONFIRM/MENU  Mouse click, or ENTER on the name-entry screen

GOAL
  Eat every pac-gum to clear a level. Eat a super-pac-gum (corners) to
  turn the ghosts blue and edible for a few seconds. Clear 10 levels to win.

CHEAT KEYS (for reviewers)
  I  toggle invincibility        G  toggle ghost freeze
  B  toggle speed boost          L  grant one extra life
  N  skip to the next level

CONFIGURATION
  The game reads config.json (shipped next to the executable). Editable keys:
  lives, points_per_pacgum, points_per_super_pacgum, points_per_ghost,
  seed, level_max_time, width, height, highscore_file.
  Lines starting with # are treated as comments.
```

---

## 6. The PyInstaller spec — the packaging "recipe"

### File to create: `pacman.spec` (repo root)

**What it is:** the PyInstaller build definition. It is the **"packaging
script/spec at the root"** the subject requires. Running `pyinstaller pacman.spec`
rebuilds the whole package deterministically — this is how you *regenerate* during
review.

**What each part does:**

- **`Analysis`** — the entry script + everything it needs.
  - `datas` — non-code files to copy into the bundle: the `assets/` tree,
    `config.json`, and `CONTROLS.txt`. The tuple is `(source, dest_in_bundle)`.
  - `hiddenimports` — modules PyInstaller can't detect automatically. The maze
    generator is imported dynamically-ish via `mazegenerator.mazegenerator`, so
    we name it explicitly to be safe.
- **`PYZ`** — bundles the pure-Python modules into one archive.
- **`EXE`** — the launcher executable. `console=False` = no black terminal window
  behind the game (it's a GUI). `name='pacman'` = the `.exe`/binary name.
- **`COLLECT`** — gathers the exe + libs + `datas` into the final
  `dist/pacman/` **one-folder** output (the thing you zip and upload).

```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — one-folder build of the Pac-Man game.
# Regenerate the package with:  pyinstaller pacman.spec   (or: make package)

block_cipher = None

a = Analysis(
    ['pac-man.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),        # fonts + images -> <bundle>/assets
        ('config.json', '.'),        # default config -> <bundle>/config.json
        ('CONTROLS.txt', '.'),       # in-package instructions
    ],
    hiddenimports=[
        'mazegenerator',
        'mazegenerator.mazegenerator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pacman',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # GUI app: no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='pacman',           # -> dist/pacman/
)
```

> **Important prerequisite for the spec:** the maze generator must be installed in
> the environment you build from (`pip install -r requirements.txt`, which
> installs the bundled wheel). PyInstaller bundles the *installed* package, so if
> it isn't installed, `hiddenimports` can't find it.

> **Cross-platform note:** a PyInstaller build is **OS-specific**. Building on
> Windows produces a Windows `.exe`; to also ship a Linux build (42 reviews are
> often on Linux) run the same `pyinstaller pacman.spec` on Linux/WSL and upload
> that as a separate Itch.io channel (see Step 7).

---

## 7. Itch.io setup + upload

### 7a. One-time account/page setup (manual, in a browser)

1. Create a free account at itch.io.
2. **Create a new project**: Dashboard → "Create new project".
   - **Kind of project:** "Downloadable".
   - **Pricing:** "No payments" (free).
   - **Visibility:** set to **Draft/Restricted** so the build is unlisted/private,
     as the subject requires.
3. Note your **username** and the **project (game) URL slug**; you'll need them as
   `user/game` for butler.

### 7b. Install and authenticate butler

1. Download butler for your OS from the Itch.io butler page (or via the itch app).
2. Put it on your `PATH` (or note its full path).
3. Authenticate once:

```bash
butler login
```

This opens a browser to link butler to your account and stores a key locally.

### 7c. Build, then upload

Build the package:

```bash
pyinstaller pacman.spec
```

This produces `dist/pacman/`. Upload that folder to a **channel**
(the last path segment names the platform channel):

```bash
# Windows build:
butler push dist/pacman USERNAME/pacman:windows

# (optional) Linux build, built on Linux/WSL:
butler push dist/pacman USERNAME/pacman:linux
```

Replace `USERNAME` with your Itch.io username. butler uploads, versions, and
de-duplicates automatically. Re-running the two commands is exactly how you
**regenerate + re-publish during review**.

### File to create (optional convenience): `itch_upload.sh`

**What it does:** wraps build + push into one command so review regeneration is
a single step. Edit `ITCH_TARGET` to your `user/game`.

```bash
#!/usr/bin/env bash
# Build the package and push it to Itch.io. Usage: ./itch_upload.sh
set -euo pipefail

ITCH_TARGET="USERNAME/pacman"   # <-- change to your itch.io user/game

echo ">> Cleaning old build..."
rm -rf build dist

echo ">> Building package with PyInstaller..."
pyinstaller pacman.spec

echo ">> Pushing to Itch.io..."
butler push dist/pacman "${ITCH_TARGET}:windows"

echo ">> Done. Channel: ${ITCH_TARGET}:windows"
```

Make it executable once: `chmod +x itch_upload.sh`.

---

## 8. Wire it into the build tooling

### Edit: `requirements.txt`

Add PyInstaller so the build tool installs with everything else:

```
pyinstaller
```

(Add it as its own line, alongside `pygame`, `mypy`, `flake8`, `pytest`, and the
maze wheel.)

### Edit: `Makefile` — add a `package` target

**What it does:** gives you `make package` as the canonical, documented build
command (nice for the review: one obvious command).

```makefile
# Build the standalone Itch.io package into dist/pacman/.
package:
	$(PY) -m PyInstaller pacman.spec
```

Also add `package` to the `.PHONY` line at the top of the Makefile.

---

## 9. `.gitignore` (already fixed)

**Status: DONE in this session.** Two bugs were corrected:

- `*.spec` was ignored → the required `pacman.spec` would never be committed.
  Added `!pacman.spec` to force-track it.
- A malformed line was ignoring the entire `src/` folder → new source files
  (like `src/resources.py`) would be silently dropped from git. Removed it.

`build/` and `dist/` stay ignored (they're regenerated artifacts, not source).

---

## 10. Clean-up: the broken Dockerfile (recommended)

The existing `Dockerfile` is **dead and misleading**: it references files that
don't exist (`flake8_dependencies.txt`, `pygame_dependencies.txt`) and runs
`main_menu_UI.py`, which isn't in the repo. Docker is also **not** a "public
gaming platform," so it doesn't satisfy Chapter 7. **Recommendation:** delete
`Dockerfile` and `.dockerignore` to avoid confusing the reviewer, since Itch.io
is now the delivery path.

---

## 11. Test & verify (before you call it done)

1. **Source still runs:** `python pac-man.py config.json` — unchanged behavior.
2. **Lint still passes:** `make lint` — the new `resources.py` and edits are typed.
3. **Build succeeds:** `make package` (or `pyinstaller pacman.spec`) with no errors.
4. **Packaged game runs from a clean spot:** copy `dist/pacman/` somewhere with no
   Python/venv, run the executable, and confirm:
   - the menu, fonts, and sprites all appear (asset paths OK);
   - a game starts with **no config argument** (default-config fallback OK);
   - highscores save and reload;
   - cheat keys work (for the reviewer).
5. **Upload works:** `butler push dist/pacman USERNAME/pacman:windows`, then
   install it back through the Itch.io app and play it.

---

## 12. Final checklist → subject Chapter 7

| Chapter 7 requirement | Delivered by |
|---|---|
| Installable/launchable from a public platform, free & unlisted | Itch.io draft page + `butler push` (Step 7) |
| Packaged game fully functional | `resources.py` + config fallback + verify (Steps 3, 4, 11) |
| Minimal in-package instructions | `CONTROLS.txt`, bundled via the spec (Steps 5, 6) |
| Full source + packaging script/spec **at repo root** | `pacman.spec` (+ `itch_upload.sh`), tracked via `.gitignore` fix (Steps 6, 9) |
| Regenerable during review | `make package` / `pyinstaller pacman.spec` / `itch_upload.sh` (Steps 6–8) |

---

## Order of operations (TL;DR)

1. `pip install pyinstaller` and add it to `requirements.txt`.
2. Create `src/resources.py`.
3. Edit the 5 files' `_ASSETS` line to use `asset_dir()`.
4. Edit `pac-man.py` for the no-argument default-config fallback.
5. Create `CONTROLS.txt`.
6. Create `pacman.spec`.
7. Add the `make package` target.
8. `make package` → test `dist/pacman/` on a machine with no Python.
9. Create the Itch.io draft page; `butler login`; `butler push`.
10. (Recommended) delete the dead `Dockerfile` / `.dockerignore`.
11. Commit: `pacman.spec`, `src/resources.py`, `CONTROLS.txt`, edited files,
    `itch_upload.sh`, updated `Makefile`/`requirements.txt`/`.gitignore`.
```
