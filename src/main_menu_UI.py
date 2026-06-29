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

    font_main = load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 300)
    main_title = font_main.render("Pacman", False, (255, 255, 0))
    font_menu_buttons = load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 100)
    start_game = font_menu_buttons.render("New Game", False, (255, 255, 0))
    high_scores = font_menu_buttons.render("High scores", False, (255, 255, 0))
    screen_width, screen_height = screen.get_size()

    # Layout based on actual rendered sizes instead of fixed pixel offsets,
    # so the spacing still works if a font size changes later.
    GAP = 60
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

    pacman_icon = ImageElement(
        os.path.join(_ASSETS, 'images', 'Screenshot_From_2026-06-13_15-17-12-removebg-preview.png'),
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
            screen.fill((0, 0, 0))
            screen.blit(main_title, main_title_box)
            screen.blit(start_game, start_game_box)
            screen.blit(high_scores, high_scores_box)
            pacman_icon.draw(screen)
            pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()