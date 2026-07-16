import json


# Task 7.1/7.2: the persistent highscore store. This class is the ONLY thing
# that ever touches the highscore file on disk - every screen that needs to
# read or write scores goes through it, so the file format lives in exactly
# one place.
class HighscoreManager:
    # CHANGED (Task 7.1): the filename is no longer hardcoded - it comes from
    # the config's "highscore_file" key (passed in by whoever builds the
    # manager). The default is only a fallback for when no config value is
    # supplied. load() runs immediately so self.scores is ready to use.
    def __init__(self, filename="highscores.json"):
        self.filename = filename
        self.scores = self.load()

    # Task 7.2: read the file and survive anything wrong with it.
    def load(self):
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

        # NEW (Task 7.2): the JSON parsed, but it might still be the wrong
        # SHAPE (e.g. someone put a number or an object in the file). Keep
        # only well-formed {"name": str, "score": int} entries and drop the
        # rest, so the rest of the game can trust self.scores completely.
        if not isinstance(data, list):
            print("Warning: highscore file has unexpected format, starting fresh.")
            return []
        clean = []
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

    # Task 7.1: write the current table back to disk as JSON.
    def save(self):
        # Task 7.2/10.4: never let a disk error crash the game at exit.
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.scores, f, indent=2)
        except OSError:
            print("Warning: could not save highscores.")

    # Task 7.1: a valid name is a string, 1-10 characters, made only of
    # letters/digits/spaces. CHANGED: the cap was 20 - the plan requires 10.
    def _valid_name(self, name):
        return (
            isinstance(name, str)
            and 0 < len(name) <= 10
            and all(c.isalnum() or c == " " for c in name)
        )

    # Task 7.1: a valid score is a non-negative integer. bool is excluded
    # because in Python True/False are ints - a stray boolean shouldn't count.
    def _valid_score(self, score):
        return isinstance(score, int) and not isinstance(score, bool) and score >= 0

    # Task 7.1: add one result, keep the table sorted and capped at 10, then
    # persist. Invalid input is ignored rather than raising, so a bad name
    # can never crash the end-of-game flow.
    def add(self, name, score):
        if not self._valid_name(name) or not self._valid_score(score):
            return
        self.scores.append({"name": name, "score": score})
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]
        self.save()

    # Task 7.1: the top 10, already sorted descending by add()/load().
    def get_top10(self):
        return self.scores[:10]
