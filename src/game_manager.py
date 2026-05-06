import random
import math
import pygame
from src.objects import GameObject, Bomb, Particle

class GameManager:
    def __init__(self, assets, screen_size=(1920,1080)):
        self.assets = assets
        self.screen_w, self.screen_h = screen_size
        self.objects = []
        self.particles = []
        self.state = "MENU"
        self.mode = None
        self.score = 0
        self.time_left = 120.0
        self.combo = 0
        self.spawn_timer = 0.0
        self.spawn_interval = 1.2
        self.screen_shake = 0.0
        self.flash_alpha = 0.0

        # Seuils
        self.slice_max_distance = 150
        self.slice_cursor_speed = 250
        self.slice_motion_backup = 0.4

        # Gestion du bip
        self.last_bip_second = 0   # seconde entière à laquelle on a joué le dernier bip

    def reset(self):
        self.objects.clear()
        self.particles.clear()
        self.score = 0
        self.time_left = 120.0
        self.combo = 0
        self.spawn_timer = 0.0
        self.screen_shake = 0.0
        self.flash_alpha = 0.0
        self.last_bip_second = 0

    def start_mode(self, mode):
        self.reset()
        self.state = "PLAYING"
        self.mode = mode

    def return_to_menu(self):
        self.reset()
        self.state = "MENU"
        self.mode = None

    def update(self, dt, cursor_pos, motion_mask_getter, cursor_speed=0.0):
        if self.state != "PLAYING":
            return

        if self.mode == "CHRONO":
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.state = "MENU"
                return
            # Bip toutes les secondes si temps restant <= 10
            if 0 < self.time_left <= 10:
                current_second = int(self.time_left)
                if current_second != self.last_bip_second and self.assets['sounds']['bip']:
                    self.assets['sounds']['bip'].play()
                self.last_bip_second = current_second
            else:
                self.last_bip_second = -1  # pour réinitialiser quand on repasse sous 10

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_object()
            self.spawn_timer = self.spawn_interval

        for obj in self.objects[:]:
            obj.update(dt)
            if obj.is_off_screen:
                self.objects.remove(obj)
                continue

            if obj.is_cut or not isinstance(obj, GameObject):
                continue

            should_slice = False
            if cursor_pos is not None:
                dist = math.hypot(obj.x - cursor_pos[0], obj.y - cursor_pos[1])
                if dist < self.slice_max_distance and cursor_speed > self.slice_cursor_speed:
                    should_slice = True
                else:
                    rect = obj.rect
                    motion_avg = motion_mask_getter(rect.x, rect.y, rect.w, rect.h)
                    if motion_avg > self.slice_motion_backup:
                        should_slice = True
            else:
                rect = obj.rect
                motion_avg = motion_mask_getter(rect.x, rect.y, rect.w, rect.h)
                if motion_avg > self.slice_motion_backup:
                    should_slice = True

            if should_slice:
                self.handle_slice(obj)

        for p in self.particles[:]:
            if not p.update(dt):
                self.particles.remove(p)

        if self.screen_shake > 0:
            self.screen_shake -= dt * 5
            if self.screen_shake < 0:
                self.screen_shake = 0
        if self.flash_alpha > 0:
            self.flash_alpha -= dt * 3
            if self.flash_alpha < 0:
                self.flash_alpha = 0

    def spawn_object(self):
        is_bomb = self.mode in ("ARCADE", "CHRONO") and random.random() < 0.2

        if random.random() < 0.5:
            x = random.randint(200, self.screen_w - 200)
            y = self.screen_h + 50
            vy = random.uniform(-750, -550)
            vx = random.uniform(-200, 200)
        else:
            x = random.randint(100, self.screen_w - 100)
            y = -50
            vy = random.uniform(200, 400)
            vx = random.uniform(-300, 300)

        angular_vel = random.uniform(-3, 3)

        if is_bomb:
            obj = Bomb(self.assets['bomb'], x, y, vx, vy, 600, angular_vel)
        else:
            fruit_name = random.choice(list(self.assets['fruit_whole'].keys()))
            whole = self.assets['fruit_whole'][fruit_name]
            cut = self.assets['fruit_cut'][fruit_name]
            obj = GameObject(whole, cut, x, y, vx, vy, 600, angular_vel)
        self.objects.append(obj)

    def handle_slice(self, obj):
        if isinstance(obj, Bomb):
            obj.is_cut = True
            if self.assets['sounds']['boom']:
                self.assets['sounds']['boom'].play()
            if self.mode == "ARCADE":
                self.score -= 200
            elif self.mode == "CHRONO":
                self.time_left -= 10
            self.combo = 0
            self.screen_shake = 1.0
            self.flash_alpha = 1.0
            for _ in range(20):
                self.particles.append(Particle(obj.x, obj.y, (255,50,50), 0.6))
            self.objects.remove(obj)
        else:
            if self.assets['sounds']['slice']:
                self.assets['sounds']['slice'].play()
            if self.mode in ("ARCADE", "CHRONO"):
                self.score += 100
            if self.mode == "CHRONO":
                self.combo += 1
                if self.combo % 5 == 0:
                    self.time_left += 5
            halves = obj.slice()
            for half in halves:
                self.objects.append(half)
            fruit_colors = [(255,165,0),(220,20,60),(154,205,50),(139,69,19),(0,128,0),
                            (255,255,0),(255,0,0),(255,200,0),(255,0,0),(255,255,0)]
            col = random.choice(fruit_colors)
            for _ in range(10):
                self.particles.append(Particle(obj.x, obj.y, col, 0.4))
            self.objects.remove(obj)

    def get_shake_offset(self):
        if self.screen_shake > 0:
            intensity = int(15 * self.screen_shake)
            return (random.randint(-intensity, intensity),
                    random.randint(-intensity, intensity))
        return (0,0)

    def draw(self, screen):
        shake = self.get_shake_offset()
        for obj in self.objects:
            obj.draw(screen, offset=shake)
        for p in self.particles:
            p.draw(screen, offset=shake)
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.screen_w, self.screen_h))
            flash_surf.set_alpha(int(150 * self.flash_alpha))
            flash_surf.fill((255,0,0))
            screen.blit(flash_surf, (0,0))