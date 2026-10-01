import random
import pygame
from game.text_box import TextBox


# Timer duration per card (in seconds)
TIMER_DURATION = 10

# Streak thresholds: (min_streak_needed, multiplier)
STREAK_TIERS = [
    (5, 3),
    (3, 2),
    (0, 1),
]


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.score = 0
        self.total_attempts = 0
        self.feedback_msg = "Solve the card and press Enter!"
        self.feedback_color = (200, 205, 215)

        self.num_a = 0
        self.num_b = 0
        self.operator = "+"

        # Task 3: streak tracker
        self.streak = 0
        self.multiplier = 1

        # Task 2: countdown timer state
        self.timer_seconds = TIMER_DURATION
        self.timer_active = True
        self._last_tick = pygame.time.get_ticks()

        box_w, box_h = 130, 44
        self.input_box = TextBox(width // 2 - 110, 248, box_w, box_h)
        self.submit_btn = pygame.Rect(width // 2 + 30, 248, 90, box_h)

        self.font_title = pygame.font.SysFont(None, 38)
        self.font_hud   = pygame.font.SysFont(None, 26)
        self.font_card  = pygame.font.SysFont(None, 56)
        self.font_btn   = pygame.font.SysFont(None, 24)

        self.generate_new_card()

    # Task 4: support +, -, *, / with guaranteed whole-number division
    def generate_new_card(self):
        self.operator = random.choice(["+", "-", "*", "/"])

        if self.operator == "/":
            divisor       = random.randint(2, 9)
            quotient      = random.randint(2, 12)
            self.num_a    = divisor * quotient   # dividend (always divisible)
            self.num_b    = divisor
        else:
            self.num_a = random.randint(3, 15)
            self.num_b = random.randint(2, 12)
            if self.operator == "-" and self.num_a < self.num_b:
                self.num_a, self.num_b = self.num_b, self.num_a

        self.input_box.clear()

        # Reset timer for the new card
        self.timer_seconds = TIMER_DURATION
        self.timer_active  = True
        self._last_tick    = pygame.time.get_ticks()

    # Task 1 (BUG FIX): evaluate actual arithmetic instead of string-concatenating
    def compute_expected_answer(self):
        if self.operator == "+":
            return self.num_a + self.num_b
        elif self.operator == "-":
            return self.num_a - self.num_b
        elif self.operator == "*":
            return self.num_a * self.num_b
        elif self.operator == "/":
            return self.num_a // self.num_b

    # Task 3: derive multiplier from current streak
    def _get_multiplier(self):
        for min_streak, mult in STREAK_TIERS:
            if self.streak >= min_streak:
                return mult
        return 1

    def submit_answer(self):
        val_str = self.input_box.text.strip()
        if not val_str or val_str == "-":
            self.feedback_msg = "Type an answer first!"
            self.feedback_color = (240, 175, 40)
            return

        user_answer = int(val_str)
        expected    = self.compute_expected_answer()
        self.total_attempts += 1

        if user_answer == expected:
            # Task 3: increment streak and calculate points
            self.streak    += 1
            self.multiplier = self._get_multiplier()
            points          = self.multiplier
            self.score     += points

            mult_label = f"  x{self.multiplier} STREAK!" if self.multiplier > 1 else ""
            self.feedback_msg = (
                f"CORRECT! {self.num_a} {self.operator} {self.num_b} "
                f"= {expected}  +{points}pt{mult_label}"
            )
            self.feedback_color = (80, 230, 110)
            self.generate_new_card()
        else:
            # Task 3: reset streak on wrong answer
            self.streak     = 0
            self.multiplier = 1

            self.feedback_msg   = f"WRONG! Expected {expected}."
            self.feedback_color = (240, 75, 75)
            self.input_box.clear()

    def handle_event(self, event):
        self.input_box.handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.submit_answer()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_btn.collidepoint(event.pos):
                self.submit_answer()

        # Task 2: listen for the timed "next card" event after time's up
        if event.type == pygame.USEREVENT + 1:
            self.generate_new_card()

    # Task 2: tick the countdown timer every frame
    def update(self):
        if not self.timer_active:
            return

        now        = pygame.time.get_ticks()
        elapsed_ms = now - self._last_tick
        self._last_tick = now

        self.timer_seconds -= elapsed_ms / 1000.0

        if self.timer_seconds <= 0:
            self.timer_seconds = 0
            self.timer_active  = False

            # Count as a failed attempt and reset streak
            self.total_attempts += 1
            self.streak          = 0
            self.multiplier      = 1

            expected              = self.compute_expected_answer()
            self.feedback_msg     = f"TIME'S UP!  Answer was {expected}."
            self.feedback_color   = (240, 80, 200)

            # Auto-advance to next card after 1.8 s
            pygame.time.set_timer(pygame.USEREVENT + 1, 1800, loops=1)

    def render(self, screen):
        screen.fill((25, 29, 37))

        # Title
        title_surf = self.font_title.render("Math Flashcards Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 14))

        # Score HUD
        score_surf = self.font_hud.render(
            f"Score: {self.score} / {self.total_attempts}", True, (255, 220, 80)
        )
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 52))

        # Task 3: streak indicator
        if self.streak >= 2:
            streak_color = (255, 160, 50) if self.multiplier > 1 else (160, 230, 160)
            streak_surf  = self.font_hud.render(
                f"Streak: {self.streak}  x{self.multiplier}", True, streak_color
            )
            screen.blit(streak_surf, (self.width // 2 - streak_surf.get_width() // 2, 74))

        # Flashcard
        card_rect = pygame.Rect(self.width // 2 - 130, 98, 260, 100)
        pygame.draw.rect(screen, (240, 242, 245), card_rect, border_radius=12)
        pygame.draw.rect(screen, (85, 120, 175), card_rect, width=3, border_radius=12)

        card_str  = f"{self.num_a}  {self.operator}  {self.num_b}"
        card_surf = self.font_card.render(card_str, True, (25, 30, 42))
        screen.blit(
            card_surf,
            (card_rect.centerx - card_surf.get_width() // 2,
             card_rect.centery - card_surf.get_height() // 2),
        )

        # Task 2: timer bar below the flashcard
        bar_x      = card_rect.x
        bar_y      = card_rect.bottom + 6
        bar_w      = card_rect.width
        bar_h      = 10
        fill_ratio = max(0.0, self.timer_seconds / TIMER_DURATION)
        fill_w     = int(bar_w * fill_ratio)

        pygame.draw.rect(screen, (50, 55, 65), pygame.Rect(bar_x, bar_y, bar_w, bar_h), border_radius=5)
        if fill_w > 0:
            red       = int(80 + 175 * (1.0 - fill_ratio))
            green     = int(220 * fill_ratio)
            bar_color = (min(red, 255), min(green, 220), 50)
            pygame.draw.rect(screen, bar_color, pygame.Rect(bar_x, bar_y, fill_w, bar_h), border_radius=5)

        secs_label = max(0, int(self.timer_seconds) + (1 if self.timer_seconds % 1 > 0 else 0))
        timer_surf = self.font_hud.render(f"{secs_label}s", True, (180, 185, 195))
        screen.blit(timer_surf, (bar_x + bar_w + 6, bar_y - 2))

        # Input box and submit button
        self.input_box.render(screen)

        pygame.draw.rect(screen, (45, 140, 80), self.submit_btn, border_radius=6)
        pygame.draw.rect(screen, (215, 225, 220), self.submit_btn, width=2, border_radius=6)
        btn_txt = self.font_btn.render("SUBMIT", True, (255, 255, 255))
        screen.blit(
            btn_txt,
            (self.submit_btn.centerx - btn_txt.get_width() // 2,
             self.submit_btn.centery - btn_txt.get_height() // 2),
        )

        # Feedback message
        msg_surf = self.font_hud.render(self.feedback_msg, True, self.feedback_color)
        screen.blit(msg_surf, (self.width // 2 - msg_surf.get_width() // 2, 310))