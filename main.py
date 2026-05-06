import pygame
import sys
import cv2
import math
from src.vision_engine import VisionEngine
from src.game_manager import GameManager
from src.ui import UI

FALLBACK_SIZE = (1280, 720)
CAMERA_INDEX = 0
MOTION_THRESHOLD = 2.0
HOLD_TIME_MENU = 1.8
HOLD_TIME_BACK = 1.5

def load_assets():
    assets = {
        'fruit_whole': {},
        'fruit_cut': {},
        'bomb': None,
        'sounds': {}
    }
    fruit_names = ["orange", "grenade", "figue", "datte", "pasteque",
                   "citron", "fraise", "melon", "pomme", "banane"]

    colors = [(255,165,0), (220,20,60), (154,205,50), (139,69,19), (0,128,0),
              (255,255,0), (255,0,0), (255,200,0), (255,0,0), (255,255,0)]
    for i, name in enumerate(fruit_names):
        surf = pygame.Surface((80,80), pygame.SRCALPHA)
        pygame.draw.circle(surf, colors[i], (40,40), 38)
        pygame.draw.circle(surf, (0,0,0), (40,40), 38, 3)
        pygame.draw.line(surf, (0,100,0), (40,5), (45,15), 4)
        assets['fruit_whole'][name] = surf

        half1 = pygame.Surface((40,80), pygame.SRCALPHA)
        half2 = pygame.Surface((40,80), pygame.SRCALPHA)
        half1.fill((0,0,0,0))
        half2.fill((0,0,0,0))
        pygame.draw.ellipse(half1, colors[i], (0,0, 80,80))
        pygame.draw.ellipse(half1, (0,0,0), (0,0, 80,80), 3)
        mask = pygame.Surface((40,80), pygame.SRCALPHA)
        mask.fill((255,255,255,255))
        half1.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.ellipse(half2, colors[i], (-40,0, 80,80))
        pygame.draw.ellipse(half2, (0,0,0), (-40,0, 80,80), 3)
        assets['fruit_cut'][name] = [half1, half2]

    bomb_surf = pygame.Surface((60,60), pygame.SRCALPHA)
    pygame.draw.circle(bomb_surf, (30,30,30), (30,30), 28)
    pygame.draw.circle(bomb_surf, (0,0,0), (30,30), 28, 3)
    pygame.draw.line(bomb_surf, (255,140,0), (30,5), (35,0), 5)
    assets['bomb'] = bomb_surf

    # Sons
    try:
        pygame.mixer.init()
        assets['sounds']['slice'] = pygame.mixer.Sound("assets/sounds/slice.wav")
        assets['sounds']['boom'] = pygame.mixer.Sound("assets/sounds/boom.wav")
        assets['sounds']['hover'] = pygame.mixer.Sound("assets/sounds/hover.wav")
        assets['sounds']['click'] = pygame.mixer.Sound("assets/sounds/click.wav")
        assets['sounds']['bip'] = pygame.mixer.Sound("assets/sounds/bip.wav")
        pygame.mixer.music.load("assets/sounds/music.mp3")
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("Sons non trouvés ou erreur, lecture désactivée :", e)
        for key in ['slice', 'boom', 'hover', 'click', 'bip']:
            assets['sounds'][key] = None

    try:
        font = pygame.font.Font("assets/fonts/game_font.ttf", 48)
    except:
        font = pygame.font.Font(None, 48)
    assets['font'] = font
    return assets

def main():
    pygame.init()
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    SCREEN_SIZE = screen.get_size()
    pygame.display.set_caption("SplashVision")
    clock = pygame.time.Clock()

    vision = VisionEngine(camera_index=CAMERA_INDEX, motion_threshold=MOTION_THRESHOLD)
    assets = load_assets()

    manager = GameManager(assets, SCREEN_SIZE)
    ui = UI(assets['font'], assets['sounds'])

    # Variable pour sortir de la boucle
    running = True

    def quit_game():
        nonlocal running
        running = False

    def setup_menu():
        ui.create_main_menu(
            start_zen=lambda: start_game("ZEN"),
            start_arcade=lambda: start_game("ARCADE"),
            start_chrono=lambda: start_game("CHRONO"),
            show_howto=lambda: set_state("HOWTO"),
            quit_action=quit_game,
            screen_width=SCREEN_SIZE[0],
            screen_height=SCREEN_SIZE[1]
        )

    def set_state(new_state):
        nonlocal state
        if new_state == "MENU":
            setup_menu()
            ui.back_button = None
            manager.mode = None
        elif new_state == "HOWTO":
            ui.create_howto_screen(SCREEN_SIZE[0], SCREEN_SIZE[1],
                                   back_action=lambda: set_state("MENU"))
        elif new_state == "PLAYING":
            ui.create_back_button(lambda: set_state("MENU"), HOLD_TIME_BACK)
        state = new_state

    def start_game(mode):
        manager.start_mode(mode)
        set_state("PLAYING")

    state = "MENU"
    setup_menu()

    def motion_in_rect(x, y, w, h):
        return vision.get_motion_in_rect(x, y, w, h)

    prev_cursor = None
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        frame, motion_mask, cursor_pos = vision.process_frame()
        if frame is None:
            continue

        if vision.hand_landmarks:
            vision.mp_draw.draw_landmarks(
                frame,
                vision.hand_landmarks,
                vision.mp_hands.HAND_CONNECTIONS,
                vision.mp_draw.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                vision.mp_draw.DrawingSpec(color=(255,255,255), thickness=2)
            )

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surf = pygame.image.frombuffer(frame_rgb.tobytes(), frame_rgb.shape[1::-1], "RGB")
        screen.blit(pygame.transform.scale(frame_surf, SCREEN_SIZE), (0,0))

        if cursor_pos:
            scale_x = SCREEN_SIZE[0] / frame.shape[1]
            scale_y = SCREEN_SIZE[1] / frame.shape[0]
            screen_cursor = (int(cursor_pos[0] * scale_x), int(cursor_pos[1] * scale_y))
        else:
            screen_cursor = None

        cursor_speed = 0.0
        if prev_cursor and screen_cursor:
            dx = screen_cursor[0] - prev_cursor[0]
            dy = screen_cursor[1] - prev_cursor[1]
            dist = math.hypot(dx, dy)
            cursor_speed = dist / dt if dt > 0 else 0.0
        prev_cursor = screen_cursor

        # Gestion des actions UI
        action = ui.update(dt, screen_cursor, None)
        if action:
            action()

        # Mise à jour du jeu
        if state == "PLAYING":
            manager.update(dt, screen_cursor, motion_in_rect, cursor_speed)
            if manager.state == "MENU":
                set_state("MENU")

        # Dessin
        if state == "PLAYING":
            manager.draw(screen)

        ui.draw(screen)
        if state == "PLAYING":
            ui.draw_hud(screen, manager.mode, manager.score,
                        manager.time_left, manager.combo,
                        shake_offset=manager.get_shake_offset())

        if screen_cursor:
            pygame.draw.circle(screen, (0,255,255), screen_cursor, 10, 2)

        pygame.display.flip()

    vision.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()