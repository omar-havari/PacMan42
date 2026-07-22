# Makefile — A Beginner's Guide (for the PacMan42 project)

> Written for two people who have **never made a Makefile before**.
> By the end you will understand *why* a Makefile exists, *what* ours must do,
> *how* to write it line by line, and you'll have a finished Makefile that
> passes the 42 subject requirements.

---

## 1. What is a Makefile? (The purpose)

A **Makefile** is a little text file, named exactly `Makefile` (capital M, no
extension), that lives in the root of your project. It is a **menu of named
shortcuts for terminal commands**.

Instead of typing long commands by hand every time:

```bash
flake8 . && mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

…you write that command **once** inside the Makefile under a short name, and
from then on everyone just types:

```bash
make lint
```

**Why this matters for us:**

1. **The reviewer expects it.** The 42 subject (Chapter 3.2) says *"Include a
   Makefile… It must contain the following rules."* During peer review, your
   evaluator will literally run `make run`, `make lint`, etc. If those don't
   work, you lose points.
2. **Consistency.** You, your teammate, and the reviewer all run the *exact same*
   command. Nobody has to remember the long flags.
3. **No memorizing.** New teammate? They just read the Makefile to see every
   thing the project can do.

Think of the Makefile as the **front desk** of your project: you walk up and say
a short word ("run", "lint", "clean"), and it does the whole long job for you.

---

## 2. What OUR Makefile must accomplish

The subject (Chapter 3.2) gives us a **mandatory list** of "rules" (shortcuts)
the Makefile must contain. Here is each one, in plain English, mapped to our
actual project:

| Shortcut | What it must do | The real command for our project |
|---|---|---|
| `make install` | Install the libraries the game needs | `pip install -r requirements.txt` |
| `make run` | Start the game | `python pac-man.py config.json` |
| `make debug` | Start the game inside Python's debugger | `python -m pdb pac-man.py config.json` |
| `make clean` | Delete junk/cache files | remove `__pycache__`, `.mypy_cache`, `*.pyc` |
| `make lint` | Check code style **and** types | `flake8 .` **and** `mypy .` (with specific flags) |
| `make lint-strict` | Stricter type check (optional) | `flake8 .` **and** `mypy . --strict` |

The exact `lint` command the subject demands is:

```
flake8 .
mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

> ⚠️ **This is the #1 thing your current Makefile gets wrong** — your `lint`
> only runs `flake8` and forgets `mypy`. We fix that at the end of this guide.

---

## 3. The main logic of a Makefile (the mental model)

A Makefile is a list of **rules**. Every rule has the same three-part shape:

```
target: prerequisites
<TAB>recipe
```

- **target** — the name you type after `make` (e.g. `run` → you type `make run`).
- **prerequisites** — other things that must be ready *first* (often empty for us).
- **recipe** — the actual shell command(s) to run. **Must be indented with a TAB.**

### How `make` thinks

When you type `make run`, `make` finds the rule whose target is `run` and
executes its recipe lines one by one in the shell.

Originally, `make` was built to **compile C programs**, so it has a clever trick:
it only re-runs a target if the files it depends on **changed** (by comparing
file timestamps). For us — where targets are *actions* like "run" or "clean",
not files — we don't want that timestamp behavior. We switch it off with a
special line called `.PHONY` (explained in the dictionary below). For now, just
know: **all our targets are "phony"** because they are commands, not files.

### 🏆 THE GOLDEN RULE (memorize this!)

> **Every recipe line MUST begin with a real TAB character — never spaces.**

This is the single most common beginner mistake. If you indent a recipe with
spaces, `make` fails with the cryptic error:

```
Makefile:4: *** missing separator.  Stop.
```

That error almost always means: *"you used spaces where a TAB was required."*

- ✅ Correct: `<TAB>python pac-man.py config.json`
- ❌ Wrong:   `····python pac-man.py config.json`  (4 spaces)

**Tip:** In VS Code, if your editor turns Tabs into spaces, click the
`Spaces: 4` button in the bottom bar → "Indent Using Tabs", or set
`"editor.insertSpaces": false` for `.makefile`/`Makefile`. You can verify a TAB
is really there by moving the cursor with the arrow keys: a TAB jumps in one
press; spaces move one at a time.

---

## 4. Anatomy of a rule — a worked example

Let's build the simplest possible rule and read it out loud.

```makefile
run:
	python pac-man.py config.json
```

Reading it line by line:

| Line | Meaning |
|---|---|
| `run:` | Declares a target named **run**. The colon `:` ends the target name. Nothing after the colon = no prerequisites. |
| `<TAB>python pac-man.py config.json` | The recipe. Indented with a **TAB**. This is the shell command that runs when you type `make run`. |

Now you type `make run` in the terminal → it runs `python pac-man.py config.json`.
That's the whole idea. Everything else is just more rules like this.

---

## 5. Step-by-step: writing our Makefile from an empty file

Follow these in order. Create a new file named `Makefile` at the project root.

### Step 1 — Declare the phony targets

At the very top, list every target that is a *command* (not a real file):

```makefile
.PHONY: install run debug clean lint lint-strict
```

This tells `make`: "these names are actions; always run them, don't look for
files with these names." (Full explanation in the dictionary, Section 6.)

### Step 2 — The `install` rule

```makefile
install:
	pip install -r requirements.txt
```

- `install:` → target.
- Recipe reads our `requirements.txt` (which lists `pygame`, `mypy`, `flake8`,
  `pytest`, and the maze-generator wheel) and installs them all with `pip`.

### Step 3 — The `run` rule

```makefile
run:
	python pac-man.py config.json
```

- Launches the game exactly the way the subject specifies:
  `python3 pac-man.py config.json`.

### Step 4 — The `debug` rule

```makefile
debug:
	python -m pdb pac-man.py config.json
```

- `-m pdb` loads Python's built-in **debugger** and runs our program inside it,
  so you can step through the code line by line. Required by the subject.

### Step 5 — The `clean` rule

```makefile
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache
	find . -name "*.pyc" -delete
```

Three recipe lines (each a TAB-indented command, run top to bottom):

1. Find every folder named `__pycache__` and delete it.
2. Delete the `.mypy_cache` folder.
3. Find and delete leftover compiled `*.pyc` files.

> 💡 `find` and `rm` are **Linux/Mac** commands. See Section 8 for the Windows note.

### Step 6 — The `lint` rule (the important one)

```makefile
lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

- **First** recipe line: `flake8 .` checks code **style** across the whole
  project (`.` means "this folder and everything under it").
- **Second** recipe line: `mypy .` checks **types**, with the exact flags the
  subject requires. Both must be present — this is what your current Makefile is
  missing.

### Step 7 — The `lint-strict` rule (optional but nice)

```makefile
lint-strict:
	flake8 .
	mypy . --strict
```

- Same idea, but `--strict` turns on *all* of mypy's checks — a tougher bar.

That's it — seven rules, and you have a complete, compliant Makefile. The full
assembled version is in Section 7.

---

## 6. Dictionary of Makefile keywords, symbols & commands

Keep this handy. These are the pieces you'll see in almost any Makefile.

### Core structure

| Term / symbol | Purpose |
|---|---|
| **target** | The name you type after `make` (e.g. `make lint` → target is `lint`). Ends with a colon `:`. |
| **prerequisite** | A thing that must be done/ready before the target's recipe runs. Written after the colon: `target: prereq1 prereq2`. Often empty for command-style targets like ours. |
| **recipe** | The shell command(s) under a target. **Each line must start with a TAB.** |
| **`:` (colon)** | Separates a target from its prerequisites. |
| **TAB** | The mandatory indentation character before every recipe line. **Not spaces.** (The Golden Rule.) |
| **`#`** | A comment. Everything after `#` on a line is ignored by `make`. Use it to explain rules. |

### Special targets & directives

| Keyword | Purpose |
|---|---|
| **`.PHONY`** | Lists targets that are **actions, not files**. Without it, if a file named `clean` ever existed, `make clean` would think "clean is already up to date" and do nothing. `.PHONY` forces the recipe to always run. Rule of thumb: every command-style target (install/run/clean/lint…) should be listed here. |
| **`.DEFAULT_GOAL`** | Sets which target runs when you type just `make` with no name. E.g. `.DEFAULT_GOAL := run`. (Optional.) |

### Automatic variables (used mostly when compiling files — good to recognize)

| Symbol | Meaning | Example |
|---|---|---|
| **`$@`** | The **target** name | in rule `game:` , `$@` = `game` |
| **`$<`** | The **first** prerequisite | `main.o: main.c` → `$<` = `main.c` |
| **`$^`** | **All** prerequisites (space-separated) | `app: a.o b.o` → `$^` = `a.o b.o` |

> We don't need these for our Python project (we have no compilation step), but
> you'll see them everywhere in C Makefiles, so it's good to recognize them.

### Variables (your own)

| Syntax | Purpose | Example |
|---|---|---|
| `NAME = value` | Define a variable | `PY = python` |
| `$(NAME)` | Use a variable | `$(PY) pac-man.py config.json` |

Variables let you avoid repeating yourself. If we defined `PY = python` at the
top, every rule could say `$(PY) …` and we'd change the interpreter in one place.

### Recipe-line prefixes (symbols at the start of a recipe line)

| Prefix | Purpose |
|---|---|
| **`@`** | Run the command **silently** (don't echo the command text first). E.g. `@echo "Done"` prints just `Done`. |
| **`-`** | **Ignore errors** on this line — keep going even if the command fails. E.g. `-rm file` won't stop `make` if the file is missing. |

### Shell operators you'll use inside recipes

| Symbol | Purpose |
|---|---|
| **`&&`** | Run the next command **only if** the previous one succeeded. `flake8 . && mypy .` = "lint types only if style passed." |
| **`;`** | Run commands one after another regardless of success. |
| **`\`** (at end of line) | **Line continuation** — join a long command across several lines for readability. |

### The `make` command itself (what you type in the terminal)

| Command | What it does |
|---|---|
| `make` | Runs the **first** target in the file (or `.DEFAULT_GOAL` if set). |
| `make run` | Runs the `run` target. |
| `make clean` | Runs the `clean` target. |
| `make -n lint` | **Dry run** — prints the commands *without* executing them (great for checking). |

---

## 7. The finished Makefile for PacMan42 (copy this)

Here is the complete, subject-compliant Makefile, with comments explaining each
block. This is the target we're building toward.

```makefile
# Declare every target as "phony": these are actions/commands, not filenames,
# so make must always run them and never skip them because a file exists.
.PHONY: install run debug clean lint lint-strict

# Install all project dependencies (pygame, flake8, mypy, pytest, and the
# local maze-generator wheel) listed in requirements.txt.
install:
	pip install -r requirements.txt

# Launch the game the way the subject specifies: python pac-man.py config.json
run:
	python pac-man.py config.json

# Run the game inside Python's built-in debugger (pdb) for step-by-step debugging.
debug:
	python -m pdb pac-man.py config.json

# Delete Python caches and compiled artifacts to keep the repo clean.
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache
	find . -name "*.pyc" -delete

# Mandatory lint: style check (flake8) AND type check (mypy) with the exact
# flags the subject requires. Both must run.
lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# Optional stricter lint: flake8 plus mypy in full --strict mode.
lint-strict:
	flake8 .
	mypy . --strict
```

### How this differs from your CURRENT Makefile (what to change)

Your existing Makefile has these problems (found during the compliance audit):

1. **`lint` is missing mypy.** It only runs `flake8 src/ pac-man.py`. The subject
   requires **flake8 *and* mypy**. → Fixed above.
2. **`lint-strict` uses the wrong flags.** It repeats the non-strict flags
   instead of `mypy . --strict`. → Fixed above.
3. **Scoped to `src/ pac-man.py` instead of `.`.** The subject says `flake8 .`
   and `mypy .` (the whole project). → Fixed above. (Note: because of this,
   `flake8 .` currently reports errors in two leftover files, `MainMenu.py` and
   `test_maze.py` — those should be removed/relocated so `make lint` passes.)

---

## 8. Running & testing your Makefile

From the project root, in a terminal:

```bash
make install     # install dependencies
make run         # play the game
make lint        # check style + types
make clean       # remove caches
make -n lint     # DRY RUN: just print what lint would do, without doing it
```

### ⚠️ Important note for Windows users (that's us)

`make`, `find`, and `rm` are **Linux/Mac** tools and are **not installed on
Windows by default**. On your Windows machines:

- Typing `make` will likely say *"command not found"* — that does **not** mean
  your Makefile is wrong.
- **42 peer reviews almost always run on Linux**, where `make` and these Unix
  commands exist. So this Makefile is written for that environment (correctly).
- If you *want* to test `make` on Windows, options are:
  1. Use **WSL** (Windows Subsystem for Linux) — run the project inside a Linux
     shell where `make` works.
  2. Install `make` via a package manager (e.g. `choco install make`) — but the
     `find`/`rm` lines in `clean` still need Unix tools, so WSL is the safer bet.
- The **Git Bash** terminal you may already have provides some Unix commands,
  but not `make` itself.

**Bottom line:** write the Makefile for Linux (as above), and test it on Linux
or WSL. Don't panic if `make` isn't recognized on plain Windows.

---

## 9. Quick recap — the 5 things to remember

1. **Purpose:** a Makefile is a menu of named shortcuts for long terminal
   commands; the reviewer runs `make run` / `make lint`, so it must work.
2. **Shape of a rule:** `target:` on one line, then a **TAB**-indented recipe.
3. 🏆 **Golden rule:** recipe lines start with a **real TAB**, never spaces
   (spaces → `missing separator` error).
4. **`.PHONY`:** list every command-style target so make always runs it.
5. **Our must-have targets:** `install`, `run`, `debug`, `clean`, `lint`,
   `lint-strict` — and `lint` must run **both** flake8 **and** mypy.

---

*Once you both understand this, I can apply the corrected Makefile to the repo
and (optionally) remove the two leftover files so `make lint` passes cleanly.
Just say the word.*
