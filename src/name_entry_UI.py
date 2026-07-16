import os
import sys

import pygame

from src.highscore import HighscoreManager

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# Task 7.3: the input rules, kept as named constants so the on-screen hint
# text and the validation logic can never drift apart.
_MAX_NAME_LENGTH = 10


def _load_font(path, size):
    # Same defensive font loader used elsewhere (GameDemo/Player): a missing
    # font is a clean exit, never a traceback.
    try:
        return pygame.font.Font(path, size)
    except FileNotFoundError:
        print(f"Error: font file '{path}' not found. Cannot start the game.")
        pygame.quit()
        sys.exit(1)


# Task 7.3: the name-entry screen shown after Game Over / Victory. It runs
# its own small blocking loop (the same style as the rest of the game's
# screens today) and only returns once the player has either saved a name or
# skipped. On return, main_menu_UI shows the main menu again.
#
# DECISION (documented per the subtask): the save at game end is guaranteed
# to be REACHED on both endings - GameDemo routes every finished game through
# here. Whether a row is actually written is the player's choice: pressing
# Enter with a valid name saves; pressing Esc skips. HighscoreManager itself
# still only keeps the top 10, so a low score simply falls off the table.
def run_name_entry(screen, score, config):
    font_title = _load_font(
        os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 60
    )
    font_body = _load_font(
        os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 36
    )

    # The name being typed. Built up character by character from key presses.
    name = ""
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            # Closing the window mid-entry quits the whole program cleanly,
            # matching how QUIT is handled everywhere else.
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Confirm. Only a non-empty name is worth saving; an empty
                    # box on Enter just does nothing (stay on the screen).
                    if name:
                        # Build the manager from the config's filename (Task
                        # 7.1 wiring) so the score lands in the right file.
                        manager = HighscoreManager(config.highscore_file)
                        manager.add(name, score)
                        return
                elif event.key == pygame.K_ESCAPE:
                    # Skip saving and go straight back to the menu.
                    return
                elif event.key == pygame.K_BACKSPACE:
                    # Drop the last character. Slicing to [:-1] is safe even
                    # when the string is empty (it just stays empty).
                    name = name[:-1]
                else:
                    # Task 7.3 real-time validation: accept a key ONLY if it is
                    # a single alphanumeric-or-space character AND we're still
                    # under the length cap. event.unicode is the actual typed
                    # character ("a", "7", " "), empty for keys like Shift.
                    char = event.unicode
                    if (
                        len(name) < _MAX_NAME_LENGTH
                        and len(char) == 1
                        and (char.isalnum() or char == " ")
                    ):
                        name += char

        # --- draw the screen every frame ---
        screen.fill((0, 0, 0))
        width, height = screen.get_size()

        title = font_title.render("NEW SCORE", False, (255, 255, 0))
        screen.blit(title, title.get_rect(center=(width / 2, height / 2 - 180)))

        score_line = font_body.render(f"Score  {score}", False, (255, 255, 255))
        screen.blit(score_line, score_line.get_rect(center=(width / 2, height / 2 - 90)))

        prompt = font_body.render("Enter your name:", False, (90, 140, 255))
        screen.blit(prompt, prompt.get_rect(center=(width / 2, height / 2 - 20)))

        # A blinking underscore cursor: get_ticks() // 500 flips between an
        # even and odd number twice a second, so "% 2" toggles the caret.
        caret = "_" if (pygame.time.get_ticks() // 500) % 2 == 0 else " "
        typed = font_body.render(name + caret, False, (255, 255, 255))
        screen.blit(typed, typed.get_rect(center=(width / 2, height / 2 + 50)))

        hint = font_body.render("ENTER = save    ESC = skip", False, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(width / 2, height / 2 + 150)))

        pygame.display.flip()
        clock.tick(60)
