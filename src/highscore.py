"""The persistent highscore store (Tasks 7.1 / 7.2).

:class:`HighscoreManager` is the ONLY thing that ever touches the highscore
file on disk - every screen that reads or writes scores goes through it, so the
file format lives in exactly one place. It is hardened against a missing,
corrupt or wrong-shaped file: it never raises, it just warns and starts fresh.
"""
import json
from typing import Any, Dict, List

Score = Dict[str, Any]


class HighscoreManager:
    """Loads, validates, and persists the top-10 highscore table."""

    def __init__(self, filename: str = "highscores.json") -> None:
        """Build the manager and immediately load the table from disk.

        Args:
            filename: Path to the JSON highscore file. Normally supplied from
                the config's ``highscore_file`` key; the default is only a
                fallback for when no config value is given.
        """
        self.filename = filename
        self.scores: List[Score] = self.load()

    def load(self) -> List[Score]:
        """Read the file and return a clean, sorted, top-10 list of scores.

        Survives every failure mode: a missing file (first run) returns an
        empty list, a corrupt/unreadable file warns and returns empty, and a
        wrong-shaped or partially-garbage file keeps only the well-formed rows.
        """
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            # First run - the file simply doesn't exist yet. Not an error:
            # start from an empty table and it gets created on first save().
            return []
        except (json.JSONDecodeError, OSError):
            # File exists but is corrupted / unreadable. Don't crash - warn
            # and start fresh. (OSError also covers permission errors etc.)
            print("Warning: highscore file corrupted, starting fresh.")
            return []

        # The JSON parsed, but it might still be the wrong SHAPE (e.g. a number
        # or an object). Keep only well-formed {"name": str, "score": int}
        # entries and drop the rest, so the game can fully trust self.scores.
        if not isinstance(data, list):
            print("Warning: highscore file has unexpected format, starting fresh.")
            return []
        clean: List[Score] = []
        for entry in data:
            if (
                isinstance(entry, dict)
                and self._valid_name(entry.get("name"))
                and self._valid_score(entry.get("score"))
            ):
                clean.append({"name": entry["name"], "score": entry["score"]})
        # Sort once on load so the table is always ordered, even if the file
        # on disk was hand-edited out of order.
        clean.sort(key=lambda x: x["score"], reverse=True)
        return clean[:10]

    def save(self) -> None:
        """Write the current table back to disk as pretty-printed JSON.

        A disk error at save time (disk full, read-only folder, ...) is caught
        and warned about rather than allowed to crash the game as it exits.
        """
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2)
        except OSError:
            print("Warning: could not save highscores.")

    def _valid_name(self, name: Any) -> bool:
        """Return ``True`` for a 1-10 char alphanumeric-or-space string."""
        return (
            isinstance(name, str)
            and 0 < len(name) <= 10
            and all(c.isalnum() or c == " " for c in name)
        )

    def _valid_score(self, score: Any) -> bool:
        """Return ``True`` for a non-negative, non-boolean integer.

        ``bool`` is excluded because in Python ``True``/``False`` are ints - a
        stray boolean should not count as a score.
        """
        return isinstance(score, int) and not isinstance(score, bool) and score >= 0

    def add(self, name: str, score: int) -> None:
        """Add one result, keep the table sorted and capped at 10, then save.

        Invalid input is ignored rather than raising, so a bad name can never
        crash the end-of-game flow.
        """
        if not self._valid_name(name) or not self._valid_score(score):
            return
        self.scores.append({"name": name, "score": score})
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]
        self.save()

    def get_top10(self) -> List[Score]:
        """Return the top 10 scores, already sorted descending."""
        return self.scores[:10]
