# How To Package Pac-Man for Itch.io — Beginner Walkthrough

This is a **type-this, see-that** guide. You do **not** need to understand
packaging. Just do each step in order, top to bottom. Every command and every
file's full contents are written out for you.

- Your computer: **Windows**, using **PowerShell** (the blue terminal).
- End result: a folder you upload to **Itch.io** that anyone can download and play
  **without installing Python**.

> 💡 If a step ever errors, jump to **Section 14 — Troubleshooting** at the bottom,
> then come back.

---

## Section 1 — Open the terminal in the right folder

1. Open **PowerShell**.
2. Go to your project folder by pasting this and pressing Enter:

```powershell
cd "C:\Users\keidi\OneDrive\PacMan42"
```

3. Confirm you're in the right place — this should list files like `pac-man.py`:

```powershell
ls
```

You should see `pac-man.py`, `config.json`, `src`, `assets`, etc. ✅

---

## Section 2 — Set up your Python environment

You need a "virtual environment" (a private box for this project's tools).

**If you do NOT already have a `venv` folder**, create one:

```powershell
python -m venv venv
```

**Activate it** (do this every time you open a new terminal for this project):

```powershell
venv\Scripts\Activate.ps1
```

After activating, your prompt line starts with `(venv)`. ✅

> ⚠️ If you see a red error about "running scripts is disabled", run this once,
> then activate again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

Now install everything the game needs, **plus the packaging tool (PyInstaller)**:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

Check PyInstaller installed:

```powershell
pyinstaller --version
```

If it prints a number (like `6.x`), you're good. ✅

---

## Section 3 — Create the file `src/resources.py`

This new file lets the game find its images/fonts both when you run it normally
**and** when it's packaged. **Create a new file** at `src\resources.py` and paste
this **exactly**:

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

Save the file. ✅

---

## Section 4 — Edit 5 existing files (the same tiny change in each)

In **each** of these 5 files, there is one identical line near the top. You will
replace it with two lines.

**Files to edit:**
1. `src\GameDemo.py`
2. `src\Player.py`
3. `src\ghost.py`
4. `src\pacgums.py`
5. `src\screens.py`

**FIND this line** (it looks the same in every file):

```python
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
```

**REPLACE it with these two lines:**

```python
from src.resources import asset_dir
_ASSETS = asset_dir()
```

Do this in all 5 files. Save each one.

> 🔎 **How to find the line fast:** in your code editor press `Ctrl+F`, paste
> `_ASSETS = os.path.join`, and it jumps right to it.

> ✅ **Special note for `src\screens.py`:** it has an extra line just below,
> `_FONT = os.path.join(_ASSETS, ...)`. **Leave that one alone** — you only change
> the `_ASSETS = os.path.join(...)` line.

---

## Section 5 — Replace the whole `pac-man.py` file

This lets the game start when someone double-clicks it (no typing needed), while
still working the old way from the command line.

**Open `pac-man.py`, delete everything in it, and paste this exactly:**

```python
"""Command-line entry point: validate the args and launch the game.

Usage::

    python pac-man.py config.json

If no argument is given (for example when launched from a packaged build by
double-click), the bundled default ``config.json`` is used instead.
"""
import sys

from src.config import Config
from src.app import run_game
from src.resources import default_config_path


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No argument (e.g. launched from Itch.io by double-click): use the
        # bundled default config that ships inside the package.
        config_file_path = default_config_path()
    elif len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        config_file_path = sys.argv[1]
    else:
        print("Usage: python pac-man.py [config.json]")
        sys.exit(1)

    config = Config(config_file_path)
    run_game(config)
```

Save. ✅

---

## Section 6 — Create the file `CONTROLS.txt`

This is the little instructions file that ships **inside** your download (the
subject requires it). **Create a new file** `CONTROLS.txt` in the main project
folder and paste:

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

Save. ✅

---

## Section 7 — Create the file `pacman.spec`

This is the "recipe" that tells PyInstaller how to build the package. **Create a
new file** `pacman.spec` in the main project folder and paste this exactly:

```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — one-folder build of the Pac-Man game.
# Rebuild with:  pyinstaller pacman.spec

block_cipher = None

a = Analysis(
    ['pac-man.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),        # fonts + images
        ('config.json', '.'),        # default config
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
    console=False,           # GUI game: no black terminal window
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
    name='pacman',           # final output: dist\pacman\
)
```

Save. ✅

---

## Section 8 — Add PyInstaller to `requirements.txt`

Open `requirements.txt`. Add one new line with the word:

```
pyinstaller
```

Put it on its own line (order doesn't matter). Save. ✅

---

## Section 9 — Build the package

Make sure your terminal still shows `(venv)` at the start of the line. Then run:

```powershell
pyinstaller pacman.spec
```

This takes a minute. When it finishes with no red errors, you will have a new
folder: **`dist\pacman\`**. Inside it is `pacman.exe` and everything it needs. ✅

> If it errored, see **Section 14 — Troubleshooting**.

---

## Section 10 — Test the packaged game (important!)

1. In File Explorer, go to `C:\Users\keidi\OneDrive\PacMan42\dist\pacman\`.
2. **Double-click `pacman.exe`.**
3. The game should open in fullscreen with the menu, sprites, and fonts.
4. Check these work:
   - Start a game (it runs even though you didn't type a config file). ✅
   - Play, die or win, enter a name — the highscore saves. ✅
   - Cheat keys work (press `I`, `N`, etc.). ✅

> 🧪 **Best test:** copy the whole `dist\pacman\` folder to your Desktop and run
> `pacman.exe` from there. If it works away from the project, it will work for
> anyone who downloads it.

If the game runs, **your package is done.** Now you publish it.

---

## Section 11 — Create your Itch.io page

1. Go to **itch.io** and make a free account.
2. Click your avatar → **Upload new project** (or Dashboard → "Create new project").
3. Fill in:
   - **Title:** Pac-Man (or anything).
   - **Kind of project:** **Downloadable**.
   - **Pricing:** **No payments** (free).
   - **Visibility & access:** choose **Restricted / Draft** so it stays
     **unlisted/private** (the subject requires this — it must not be a public
     store listing).
4. Click **Save** at the bottom. Note your **username** and the game's **URL name**
   (the slug). Together they are `username/pacman`.

You do NOT need to manually upload the zip here — `butler` (next step) does it.

---

## Section 12 — Upload with butler

`butler` is Itch.io's official uploader.

1. Download **butler** for Windows from the Itch.io butler page
   (search "itch.io butler download"). You get a `butler.exe`.
2. The simplest approach: **copy `butler.exe` into your project folder**
   (`C:\Users\keidi\OneDrive\PacMan42\`) so the commands below find it.
3. In PowerShell (in the project folder), log in once:

```powershell
.\butler.exe login
```

A browser opens — approve it. Now upload your built folder (replace `USERNAME`
with your itch.io username):

```powershell
.\butler.exe push dist\pacman USERNAME/pacman:windows
```

When it finishes, refresh your Itch.io project page — the `windows` build appears.
🎉 **You have published the game.**

> 🔁 **This is also how you "regenerate during review":** just run
> `pyinstaller pacman.spec` again, then the `butler push` command again.

---

## Section 13 — Save your work to Git

The subject requires the packaging spec to be **in your git repository**. Commit
the new/changed files:

```powershell
git add pac-man.py pacman.spec CONTROLS.txt requirements.txt src\resources.py src\GameDemo.py src\Player.py src\ghost.py src\pacgums.py src\screens.py .gitignore
git commit -m "Add Itch.io packaging (PyInstaller spec + resource loader)"
```

> Do NOT commit the `build\` or `dist\` folders or `butler.exe` — they're already
> ignored. They are regenerated by the build command.

You're done. ✅

---

## Section 14 — Troubleshooting

| Symptom | Fix |
|---|---|
| `Set-ExecutionPolicy` needed / can't activate venv | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, press `Y`, then activate again. |
| `pyinstaller` not recognized | You forgot to activate the venv (`venv\Scripts\Activate.ps1`) or install it (`pip install pyinstaller`). |
| Build error mentioning `mazegenerator` | Run `pip install -r requirements.txt` again so the maze wheel is installed, then rebuild. |
| Packaged game opens then closes instantly | Temporarily change `console=False` to `console=True` in `pacman.spec`, rebuild, run from PowerShell to read the error message. Switch it back when fixed. |
| Fonts/images missing in the packaged game | You missed one of the 5 files in Section 4, or the `_FONT` line in `screens.py` was changed by mistake. Recheck Section 4. |
| `butler` not recognized | Use `.\butler.exe` (with the `.\`) and make sure `butler.exe` is in the project folder. |
| Game must also run on the reviewer's **Linux** machine | A Windows build only runs on Windows. To make a Linux build, run `pyinstaller pacman.spec` on Linux or WSL, then `butler push dist/pacman USERNAME/pacman:linux`. |

---

## Quick recap (the whole thing in 10 lines)

```powershell
cd "C:\Users\keidi\OneDrive\PacMan42"
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install pyinstaller
# ... create src\resources.py, CONTROLS.txt, pacman.spec ...
# ... edit the 5 files + pac-man.py + requirements.txt ...
pyinstaller pacman.spec
# double-click dist\pacman\pacman.exe to test
.\butler.exe login
.\butler.exe push dist\pacman USERNAME/pacman:windows
```
