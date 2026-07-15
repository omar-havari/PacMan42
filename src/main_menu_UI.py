import os
import pygame
import sys
from src.pacman_images import ImageElement
from src.GameDemo import GameDemo

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def load_path(path, size):
    try:
        return pygame.font.Font(path, size)
    except FileNotFoundError:
        print(f"Error: font file '{path}' not found. Cannot start the game.")
        pygame.quit()
        sys.exit(1)


def run_main_menu(config):
    pygame.init()
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    screen = pygame.display.set_mode(
        (screen_width, screen_height), pygame.FULLSCREEN
    )
    pygame.display.set_caption("Test")

    # --- Blue theme, matching the maze wall color (33, 33, 255) ---
    BORDER_COLOR = (33, 33, 255)
    TEXT_COLOR = (90, 140, 255)
    BG_COLOR = (0, 0, 0)
    BORDER_THICKNESS = 6
    BORDER_RADIUS = 16
    PANEL_PADDING = 70

    # Smaller fonts than before (was 300 / 100)
    font_main = load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 120)
    main_title = font_main.render("Pacman", False, TEXT_COLOR)
    font_menu_buttons = load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 45)
    start_game = font_menu_buttons.render("New Game", False, TEXT_COLOR)
    high_scores = font_menu_buttons.render("High scores", False, TEXT_COLOR)
    screen_width, screen_height = screen.get_size()

    # Layout based on actual rendered sizes instead of fixed pixel offsets,
    # so the spacing still works if a font size changes later.
    GAP = 40
    total_height = (
        main_title.get_height()
        + GAP
        + start_game.get_height()
        + GAP
        + high_scores.get_height()
    )
    top_y = (screen_height - total_height) / 2

    main_title_box = main_title.get_rect(
        centerx=screen_width / 2,
        top=top_y
    )
    start_game_box = start_game.get_rect(
        centerx=screen_width / 2,
        top=main_title_box.bottom + GAP
    )
    high_scores_box = high_scores.get_rect(
        centerx=screen_width / 2,
        top=start_game_box.bottom + GAP
    )

    # Border panel wraps title + buttons with padding on all sides
    panel_rect = main_title_box.unionall([start_game_box, high_scores_box])
    panel_rect = panel_rect.inflate(PANEL_PADDING * 2, PANEL_PADDING * 2)

    pacman_icon = ImageElement(
        os.path.join(_ASSETS, 'images', 'Screenshot_From_2026-07-10_12-31-14-removebg-preview.png'),
        (150, 150),
        (screen_width / 2, 3 * screen_height / 4)
    )
    game = None
    clock = pygame.time.Clock()
    running = True
    while running:
        if game is not None:
            # --- IN GAME ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    game.handle_event(event)
            game_over = game.update()
            game.draw()
            pygame.display.flip()
            if game_over:
                game = None
        else:
            # --- IN MENU ---
            pygame.mouse.set_visible(True)
            mouse_pos = pygame.mouse.get_pos()
            if (start_game_box.collidepoint(mouse_pos)
                    or high_scores_box.collidepoint(mouse_pos)):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_game_box.collidepoint(event.pos):
                        game = GameDemo(screen, config)
                    if high_scores_box.collidepoint(event.pos):
                        print("Placeholder")
            screen.fill(BG_COLOR)
            pygame.draw.rect(
                screen, BORDER_COLOR, panel_rect,
                width=BORDER_THICKNESS, border_radius=BORDER_RADIUS
            )
            screen.blit(main_title, main_title_box)
            screen.blit(start_game, start_game_box)
            screen.blit(high_scores, high_scores_box)
            pacman_icon.draw(screen)
            pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()