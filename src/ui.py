import pygame
import math

class HoverButton:
    def __init__(self, x, y, w, h, text, font, hold_time=2.5, sounds=None,
                 base_color=(50,50,50), border_color=(255,255,255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.hold_time = hold_time
        self.progress = 0.0
        self.active = False
        self.action = None
        self.border_color = border_color
        self.base_color = base_color
        self.sounds = sounds or {}
        self.hover_played = False

    def update(self, dt, cursor_pos, motion_magnitude):
        if cursor_pos is None:
            self.progress = max(0.0, self.progress - dt / self.hold_time)
            self.active = False
            self.hover_played = False
            return False

        if self.rect.collidepoint(cursor_pos):
            if not self.active:
                if self.sounds.get('hover') and not self.hover_played:
                    self.sounds['hover'].play()
                    self.hover_played = True
            self.progress += dt / self.hold_time
            self.active = True
        else:
            self.progress -= dt / self.hold_time
            self.active = False
            self.hover_played = False

        self.progress = max(0.0, min(1.0, self.progress))
        if self.progress >= 1.0:
            self.progress = 0.0
            if self.sounds.get('click'):
                self.sounds['click'].play()
            return True
        return False

    def draw(self, screen, offset=(0,0)):
        rect = self.rect.move(offset)
        r, g, b = self.base_color
        base_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        for y in range(rect.h):
            alpha = 180 + int(40 * (1 - y / rect.h))
            pygame.draw.line(base_surf, (r, g, b, alpha), (0,y), (rect.w,y))
        screen.blit(base_surf, rect.topleft)
        pygame.draw.rect(screen, self.border_color, rect, 4)
        if self.active:
            pygame.draw.rect(screen, (0,255,0), rect, 6)
        text_surf = self.font.render(self.text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        if self.progress > 0:
            center = rect.center
            radius = min(rect.w, rect.h)//2 + 10
            angle = 360 * self.progress
            pygame.draw.arc(screen, (0,255,0),
                           (center[0]-radius, center[1]-radius, radius*2, radius*2),
                           0, math.radians(angle), width=8)
            end_angle = math.radians(angle)
            ex = center[0] + radius * math.cos(end_angle)
            ey = center[1] + radius * math.sin(end_angle)
            pygame.draw.circle(screen, (0,255,0), (int(ex), int(ey)), 6)

class UI:
    def __init__(self, font, sounds=None):
        self.font = font
        self.buttons = []
        self.back_button = None
        self.sounds = sounds or {}
        self.howto_lines = None

    def create_main_menu(self, start_zen, start_arcade, start_chrono, show_howto, quit_action,
                         screen_width=1280, screen_height=720):
        self.buttons = []
        btn_w = 300
        btn_h = 90
        spacing = 40   # réduit pour caser 5 boutons
        total_height = 5 * btn_h + 4 * spacing
        start_y = (screen_height - total_height) // 2
        x_center = screen_width // 2

        self.buttons.append(HoverButton(x_center - btn_w//2, start_y, btn_w, btn_h,
                                        "ZEN", self.font, hold_time=2.0, sounds=self.sounds))
        self.buttons[0].action = start_zen

        self.buttons.append(HoverButton(x_center - btn_w//2, start_y + btn_h + spacing, btn_w, btn_h,
                                        "ARCADE", self.font, hold_time=2.0, sounds=self.sounds))
        self.buttons[1].action = start_arcade

        self.buttons.append(HoverButton(x_center - btn_w//2, start_y + 2*(btn_h + spacing), btn_w, btn_h,
                                        "CHRONO", self.font, hold_time=2.0, sounds=self.sounds))
        self.buttons[2].action = start_chrono

        self.buttons.append(HoverButton(x_center - btn_w//2, start_y + 3*(btn_h + spacing), btn_w, btn_h,
                                        "HOW TO PLAY", self.font, hold_time=2.0, sounds=self.sounds))
        self.buttons[3].action = show_howto

        # Bouton Quitter avec fond rouge foncé
        self.buttons.append(HoverButton(x_center - btn_w//2, start_y + 4*(btn_h + spacing), btn_w, btn_h,
                                        "QUITTER", self.font, hold_time=2.0, sounds=self.sounds,
                                        base_color=(120, 30, 30)))
        self.buttons[4].action = quit_action

        self.back_button = None
        self.howto_lines = None

    def create_back_button(self, action, hold_time=1.8):
        self.back_button = HoverButton(20, 20, 200, 80, "RETOUR", self.font,
                                       hold_time=hold_time, sounds=self.sounds,
                                       base_color=(80, 20, 20))
        self.back_button.action = action
        self.buttons = []

    def create_howto_screen(self, screen_width, screen_height, back_action):
        self.buttons = []
        self.back_button = HoverButton(screen_width//2 - 100, screen_height - 120, 200, 80,
                                       "BACK", self.font, hold_time=1.5, sounds=self.sounds,
                                       base_color=(20, 20, 80))
        self.back_button.action = back_action
        self.howto_lines = [
            "HOW TO PLAY",
            "",
            "- Move your hand in front of the camera.",
            "- Use your index finger to point at buttons.",
            "- Hold your finger on a button to fill the gauge.",
            "- In game, swipe your hand across fruits to slice them.",
            "- Avoid bombs! They shake the screen and cost points/time.",
            "- In CHRONO mode, slice 5 fruits in a row for +5 seconds.",
            "",
            "No click, no keyboard – just your hand!",
        ]

    def update(self, dt, cursor_pos, motion_magnitude):
        for btn in self.buttons:
            if btn.update(dt, cursor_pos, motion_magnitude):
                return btn.action
        if self.back_button and self.back_button.update(dt, cursor_pos, motion_magnitude):
            return self.back_button.action
        return None

    def draw(self, screen):
        for btn in self.buttons:
            btn.draw(screen)
        if self.back_button:
            self.back_button.draw(screen)

        if self.howto_lines:
            y = 150
            for line in self.howto_lines:
                shadow = self.font.render(line, True, (0,0,0))
                screen.blit(shadow, (122, y+2))
                text_surf = self.font.render(line, True, (255,255,255))
                screen.blit(text_surf, (120, y))
                y += 50

    def draw_hud(self, screen, mode, score, time_left, combo, shake_offset=(0,0)):
        if mode == "ZEN":
            return
        x, y = 50, 100
        if mode == "ARCADE":
            screen.blit(self.font.render(f"Score: {score}", True, (255,255,255)),
                        (x+shake_offset[0], y+shake_offset[1]))
        elif mode == "CHRONO":
            screen.blit(self.font.render(f"Temps: {int(max(0,time_left))}s", True, (255,255,255)),
                        (x+shake_offset[0], y+shake_offset[1]))
            screen.blit(self.font.render(f"Score: {score}", True, (255,255,255)),
                        (x+shake_offset[0], y+50+shake_offset[1]))
            if combo > 0:
                screen.blit(self.font.render(f"Combo: {combo}", True, (255,215,0)),
                            (x+shake_offset[0], y+100+shake_offset[1]))