"""Guide the player through the gameplay controls, one action at a time."""

from __future__ import annotations

import math
from pathlib import Path
from typing import ClassVar

import pygame

from ...maps.game_map import GameMap, NEON_GRID_MAP
from ...ui.button import Button
from ...ui.text_object import TextObject, get_font
from .gameplay.enemy.glitchworm import Glitchworm
from .gameplay.gameplay import EnemySpawn, Gameplay


class Tutorial(Gameplay):
    """Keep the regular board, with a local script and two single-enemy waves."""

    ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[3] / "asset_files" / "tutorial"
    )
    CAT_IMG = pygame.image.load(ASSET_DIR / "cat.png")
    BACK_LIT_IMG = pygame.image.load(ASSET_DIR / "back_lit.png")
    BACK_UNLIT_IMG = pygame.image.load(ASSET_DIR / "back_unlit.png")
    CONTINUE_PROMPT = "PRESS [N] OR CLICK"
    OUTRO_LINES = (
        "Oh...you did...surprisingly well...",
        "But you won't beat this!",
    )
    SKIP_PROMPT_DELAY = 5.0
    ENTER_DURATION = 0.45
    EXIT_DURATION = 0.45
    CAT_REST_OVERLAP = 8
    INTRO_LINES = (
        "Oh mreow!!!",
        "I did not notice you there!",
        "You wanted to try the tutorial?",
        "Heh...",
        "Noob >:)",
        "But if you insist...",
    )

    ENTERING = "entering"
    INTRO = "intro"
    INTRO_OUT = "intro_out"
    CHOOSE_TOWER = "choose_tower"
    CANCEL_PLACEMENT = "cancel_placement"
    RESELECT_TOWER = "reselect_tower"
    PLACE_TOWER = "place_tower"
    INSPECT_TOWER = "inspect_tower"
    CLOSE_SIDEBAR = "close_sidebar"
    STATS = "stats"
    START_WAVE = "start_wave"
    WATCH_WAVE = "watch_wave"
    SKIP_WAVE = "skip_wave"
    WAVES = "waves"
    GOOD_LUCK = "good_luck"
    EXITING = "exiting"
    FAILED = "failed"

    LESSONS = {
        CHOOSE_TOWER: (
            "Choose a tower by clicking the highlighted selection panel.",
            "CLICK A TOWER",
        ),
        CANCEL_PLACEMENT: (
            "Before placing, try cancelling your selection with [Q].",
            "PRESS [Q]",
        ),
        RESELECT_TOWER: (
            "Now choose the tower again. Next, we will place it.",
            "CLICK A TOWER",
        ),
        PLACE_TOWER: (
            "Click a highlighted slot to place your tower. "
            "[Q] cancels placement.",
            "CLICK A SLOT",
        ),
        INSPECT_TOWER: (
            "Click the tower you placed to view its status.",
            "CLICK YOUR TOWER",
        ),
        CLOSE_SIDEBAR: (
            "This panel shows your tower's stats and upgrades. "
            "Click to close it.",
            "CLICK TO CLOSE",
        ),
        STATS: (
            "Your health and power are shown here. "
            "Power pays for towers and upgrades.",
            CONTINUE_PROMPT,
        ),
        START_WAVE: (
            "Press [SPACE] or click START to begin wave 1. "
            "It contains one enemy.",
            "[SPACE] OR CLICK START",
        ),
        WATCH_WAVE: (
            "Wave 1 has started. Watch your tower attack the enemy.",
            "WATCH THE WAVE",
        ),
        SKIP_WAVE: (
            "Press [S] or click SKIP to start wave 2 early. "
            "The first enemy stays on the path.",
            "[S] OR CLICK SKIP",
        ),
        WAVES: (
            "Your tower attacks automatically. "
            "Let it finish the two tutorial enemies.",
            "WAVE 2 / 2",
        ),
    }

    def __init__(self, app: App, game_map: GameMap = NEON_GRID_MAP) -> None:
        super().__init__(app, game_map)
        self.phase = self.ENTERING
        self.intro_index = 0
        self.outro_index = 0
        self.guide_text = self.INTRO_LINES[0]
        self.prompt = self.CONTINUE_PROMPT
        self.bob_time = 1.0
        self.guide_time = 0.0
        self.cat_pop = 0.0
        self.cat_target = 0.0
        # Trim padding; the cropped torso rests behind the box's upper edge.
        cat = self.CAT_IMG.subsurface(self.CAT_IMG.get_bounding_rect())
        self.cat_image = pygame.transform.scale(cat, (96, 96))
        self.message_text = TextObject(
            font_size=11, color="#efffff", anchor="topleft"
        )
        self.prompt_text = TextObject(
            font_size=9, color="#9feef8", anchor="bottomright"
        )
        self.step_text = TextObject(
            font_size=8, color="#73acba", anchor="bottomleft"
        )
        self.message_font = get_font(
            self.message_text.font, self.message_text.font_size
        )
        self.prompt_font = get_font(
            self.prompt_text.font, self.prompt_text.font_size
        )
        self.message_box = pygame.Rect(10, 256, 330, 84)
        self.enter_progress = 0.0
        self.exit_progress = 0.0
        self.exit_start_y = self.message_box.top
        self.health_power_highlight = (
            self.HEALTHBAR_IMG.get_bounding_rect().move(10, 15).inflate(4, 4)
        )

        self.wave_state.MAX_WAVES = 2
        self.wave_state.next_ready = False
        # Keep the start/skip controls clear of the bottom-left dialogue.
        self.wave_ready_rect.midtop = (335, 8)
        self.skip_wave_rect.midtop = (335, 8)
        self.wave_ready_text.position = self.wave_ready_rect.center
        self.skip_wave_text.position = self.skip_wave_rect.center
        self.back_button = Button(
            position=(590, 10),
            anchor="topright",
            lit_img=self.BACK_LIT_IMG,
            unlit_img=self.BACK_UNLIT_IMG,
            action=self.leave_tutorial,
        )
        hidden_image = pygame.Surface((1, 1), pygame.SRCALPHA)
        for button in (
            self.home_button, self.settings_button,
            self.pause_button, self.restart_button,
        ):
            button.unlit_img = button.lit_img = hidden_image
            button.rect = pygame.Rect(0, 0, 0, 0)

    def leave_tutorial(self) -> None:
        """Slide the cat and dialogue away before returning to map selection."""
        if self.phase == self.EXITING:
            return
        self.exit_start_y = self._message_rect().top
        self.exit_progress = 0.0
        self._set_phase(self.EXITING)
        self.cat_target = 0.0
        self.prompt = ""

    @staticmethod
    def _left_click(event: pygame.event.Event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

    @classmethod
    def _advance_pressed(cls, event: pygame.event.Event) -> bool:
        return cls._left_click(event) or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_n
        )

    def _set_phase(self, phase: str) -> None:
        self.phase = phase
        self.guide_time = 0.0
        if phase in self.LESSONS:
            self.guide_text, self.prompt = self.LESSONS[phase]
        self.wave_state.next_ready = phase == self.START_WAVE

    def handle_event(self, event: pygame.event.Event) -> None:
        """Only accept the action being taught; never forward arbitrary input."""
        if self.phase == self.EXITING:
            return
        if self.back_button.handle_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.leave_tutorial()
            return
        if event.type == pygame.KEYDOWN and getattr(event, "repeat", False):
            return
        if self.phase == self.ENTERING:
            return

        click = self._left_click(event)
        if self.phase == self.INTRO:
            if self._advance_pressed(event):
                self._advance_intro()
        elif self.phase == self.GOOD_LUCK:
            if self._advance_pressed(event):
                if self.outro_index + 1 < len(self.OUTRO_LINES):
                    self.outro_index += 1
                    self.guide_text = self.OUTRO_LINES[self.outro_index]
                    self.bob_time = 0.0
                else:
                    self.leave_tutorial()
        elif self.phase == self.FAILED:
            if self._advance_pressed(event):
                self.app.change_screen(Tutorial(self.app, self.game_map))
        elif self.phase in (self.CHOOSE_TOWER, self.RESELECT_TOWER):
            if click and any(
                rect.collidepoint(event.pos)
                for rect in self.tower_selection_rects
            ):
                previous_phase = self.phase
                super().handle_event(event)
                if self.selected_tower_type is not None:
                    self._set_phase(
                        self.CANCEL_PLACEMENT
                        if previous_phase == self.CHOOSE_TOWER
                        else self.PLACE_TOWER
                    )
                else:
                    self.guide_text = (
                        "That tower costs more power than you have. "
                        "Choose the first tower."
                    )
        elif self.phase == self.CANCEL_PLACEMENT:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                self.cancel_tower_placement()
                self._set_phase(self.RESELECT_TOWER)
        elif self.phase == self.PLACE_TOWER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                self.cancel_tower_placement()
                self._set_phase(self.RESELECT_TOWER)
            elif event.type == pygame.MOUSEMOTION:
                super().handle_event(event)
            elif click and any(
                slot.rect.collidepoint(event.pos) and not slot.occupied
                for slot in self.tower_slots
            ):
                count = len(self.towers)
                super().handle_event(event)
                if len(self.towers) > count:
                    self._set_phase(self.INSPECT_TOWER)
                elif self.selected_tower_type is None:
                    self._set_phase(self.RESELECT_TOWER)
        elif self.phase == self.INSPECT_TOWER:
            if click:
                for index, tower in enumerate(self.towers):
                    if tower.rect.collidepoint(event.pos):
                        self.sidebar_tower = tower
                        self.sidebar_tower_idx = index
                        self._set_phase(self.CLOSE_SIDEBAR)
                        break
        elif self.phase == self.CLOSE_SIDEBAR:
            if click:
                self.sidebar_tower = self.sidebar_tower_idx = None
                self._set_phase(self.STATS)
        elif self.phase == self.STATS:
            if self._advance_pressed(event):
                self._set_phase(self.START_WAVE)
        elif self.phase == self.START_WAVE:
            if (
                event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
            ) or (click and self.wave_ready_rect.collidepoint(event.pos)):
                self.start_wave()
        elif self.phase == self.SKIP_WAVE:
            if (
                event.type == pygame.KEYDOWN and event.key == pygame.K_s
            ) or (click and self.skip_wave_rect.collidepoint(event.pos)):
                self.skip_wave()

    def _advance_intro(self) -> None:
        if self.intro_index + 1 < len(self.INTRO_LINES):
            self.intro_index += 1
            self.guide_text = self.INTRO_LINES[self.intro_index]
            self.bob_time = 0.0
            # Only the first appearance rises fully; later lines gently bob.
            self.cat_target = 1.0
        else:
            self._set_phase(self.INTRO_OUT)
            self.prompt = "LET'S BEGIN!"
            self.cat_target = 0.0

    def start_wave(self) -> None:
        """Gate both UI and direct calls, queuing one enemy per lesson wave."""
        wave = self.wave_state.round
        allowed = (
            self.phase == self.START_WAVE and wave == 1
        ) or (self.phase == self.SKIP_WAVE and wave == 2)
        if (
            not allowed or not self.wave_state.next_ready
            or self.paused or self.game_over or self.wave_state.won
        ):
            return
        self.enemy_state.spawn_queue.append(EnemySpawn(Glitchworm, 1, wave))
        self.enemy_state.count = 0
        self.wave_state.active = True
        self.wave_state.active_waves.add(wave)
        self.wave_state.cleared = False
        self.wave_state.cleared_start_time = None
        now = pygame.time.get_ticks()
        self.enemy_state.spawn_time = now
        self.enemy_state.wave_spawn_times[wave] = now
        if wave == 1:
            self.spawn_enemy(1)
            self._set_phase(self.WATCH_WAVE)
        else:
            # Leave a spawn interval between the enemies so both are visible.
            self._set_phase(self.WAVES)

    @property
    def can_skip_wave(self) -> bool:
        return (
            self.phase == self.SKIP_WAVE and self.wave_state.round == 1
            and super().can_skip_wave
        )

    def skip_wave(self) -> None:
        """Teach the real skip behavior: start wave two, retaining wave one."""
        if self.can_skip_wave:
            super().skip_wave()

    def set_wave_cleared(self, current_time: int) -> None:
        super().set_wave_cleared(current_time)
        if self.wave_state.round == 2 and self.wave_state.cleared:
            self.cancel_tower_placement()
            self.set_next_wave_ready(current_time)

    def set_next_wave_ready(self, current_time: int) -> None:
        """Finish the tutorial waves and go straight to the closing dialogue."""
        super().set_next_wave_ready(current_time)
        if self.wave_state.won:
            self._set_phase(self.GOOD_LUCK)
            self.outro_index = 0
            self.guide_text = self.OUTRO_LINES[0]
            self.prompt = self.CONTINUE_PROMPT
            self.cat_target = 1.0
            self.bob_time = 0.0

    def set_game_over(self) -> None:
        super().set_game_over()
        self._set_phase(self.FAILED)
        self.guide_text = "Let's try that again. I'll walk you through it!"
        self.prompt = self.CONTINUE_PROMPT
        self.cat_target = 1.0
        self.bob_time = 0.0

    def update(self, dt: float) -> None:
        self.bob_time += dt
        previous_guide_time = self.guide_time
        self.guide_time += dt
        if self.cat_pop < self.cat_target:
            self.cat_pop = min(self.cat_target, self.cat_pop + dt / 0.35)
        elif self.cat_pop > self.cat_target:
            self.cat_pop = max(self.cat_target, self.cat_pop - dt / 0.28)
        if self.phase == self.ENTERING:
            self.enter_progress = min(1.0, self.enter_progress + dt / self.ENTER_DURATION)
            if self.enter_progress == 1.0:
                self._set_phase(self.INTRO)
            return
        if self.phase == self.EXITING:
            self.exit_progress = min(1.0, self.exit_progress + dt / self.EXIT_DURATION)
            if self.exit_progress == 1.0:
                self.app.get_map_selection()
            return
        if self.phase == self.INTRO_OUT and self.cat_pop == 0.0:
            self._set_phase(self.CHOOSE_TOWER)

        if self.phase == self.WATCH_WAVE:
            # Play the first moments before introducing skipping. Clamp a slow
            # frame so it cannot run through the entire lesson in one update.
            watch_dt = min(dt, max(0.0, self.SKIP_PROMPT_DELAY - previous_guide_time))
            super().update(watch_dt)
            if self.phase == self.WATCH_WAVE and self.guide_time >= self.SKIP_PROMPT_DELAY:
                self._set_phase(self.SKIP_WAVE)
        elif self.phase == self.WAVES:
            super().update(dt)
        else:
            # Keep the board still until the player has practised skipping.
            self.update_towers(dt)
            self.update_insufficient_funds(pygame.time.get_ticks())

    def draw_wave_ready(self, window: pygame.Surface) -> None:
        if self.phase == self.START_WAVE:
            super().draw_wave_ready(window)

    def draw_wave_cleared(self, window: pygame.Surface) -> None:
        """Use the cat's closing dialogue instead of the campaign banner."""

    def draw_game_over(self, window: pygame.Surface) -> None:
        """The local retry message handles a loss without campaign buttons."""

    def draw(self, window: pygame.Surface) -> None:
        # Suppress the campaign victory label while reusing the whole board.
        self.victory_text.text = ""
        super().draw(window)
        self._draw_highlight(window)
        self._draw_message(window)
        self.back_button.draw(window)

    def _draw_highlight(self, window: pygame.Surface) -> None:
        if self.phase in (self.CHOOSE_TOWER, self.RESELECT_TOWER):
            rects = [pygame.Rect(445, 295, 154, 54)]
        elif self.phase == self.PLACE_TOWER:
            rects = [
                slot.rect.inflate(4, 4)
                for slot in self.tower_slots if not slot.occupied
            ]
        elif self.phase == self.INSPECT_TOWER:
            rects = [tower.rect.inflate(6, 6) for tower in self.towers]
        elif self.phase == self.CLOSE_SIDEBAR:
            rects = [pygame.Rect(371, 1, 227, 348)]
        elif self.phase == self.STATS:
            rects = [self.health_power_highlight]
        elif self.phase == self.START_WAVE:
            rects = [self.wave_ready_rect.inflate(4, 4)]
        elif self.phase == self.SKIP_WAVE:
            rects = [self.skip_wave_rect.inflate(4, 4)]
        else:
            rects = []

        alpha = 150 + int(80 * (0.5 + 0.5 * math.sin(self.guide_time * 5)))
        overlay = pygame.Surface(window.get_size(), pygame.SRCALPHA)
        for rect in rects:
            pygame.draw.rect(overlay, (75, 242, 255, 20), rect, border_radius=3)
            pygame.draw.rect(
                overlay, (95, 233, 255, alpha), rect, 2, border_radius=3
            )
        window.blit(overlay, (0, 0))

    def _message_rect(self) -> pygame.Rect:
        if self.phase == self.ENTERING:
            eased = self.enter_progress ** 2 * (3 - 2 * self.enter_progress)
            bubble = self.message_box.copy()
            start_y = self.game_map.height + 2
            bubble.y = round(start_y + (bubble.y - start_y) * eased)
            return bubble
        if self.phase == self.EXITING:
            eased = self.exit_progress ** 2 * (3 - 2 * self.exit_progress)
            bubble = self.message_box.copy()
            bubble.y = round(
                self.exit_start_y
                + (self.game_map.height + 2 - self.exit_start_y) * eased
            )
            return bubble
        bob = 0
        if self.cat_target and self.bob_time < 0.4:
            bob = round(4 * math.sin(math.pi * self.bob_time / 0.4))
        return self.message_box.move(0, -bob)

    def _cat_rect(self, bubble: pygame.Rect) -> pygame.Rect:
        # Ease the entrance without restarting it when a sentence changes.
        eased_pop = self.cat_pop * self.cat_pop * (3 - 2 * self.cat_pop)
        top = (
            bubble.top + self.CAT_REST_OVERLAP
            - round(self.cat_image.get_height() * eased_pop)
        )
        return self.cat_image.get_rect(topleft=(bubble.left + 26, top))

    def _wrapped_message(self) -> list[str]:
        lines = []
        line = ""
        for word in self.guide_text.split():
            candidate = f"{line} {word}".strip()
            if (
                line and self.message_font.size(candidate)[0]
                > self.message_box.width - 28
            ):
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        return lines

    def _draw_message(self, window: pygame.Surface) -> None:
        bubble = self._message_rect()
        # Draw the cat first and mask everything below the box's upper edge.
        # The cropped torso meets that edge, including during the talking bob.
        if self.cat_pop > 0:
            previous_clip = window.get_clip()
            mask = pygame.Rect(bubble.left, 0, bubble.width, bubble.top + 2)
            window.set_clip(previous_clip.clip(mask))
            window.blit(self.cat_image, self._cat_rect(bubble))
            window.set_clip(previous_clip)

        pygame.draw.rect(window, (5, 16, 34), bubble, border_radius=5)
        pygame.draw.rect(window, (95, 233, 255), bubble, 2, border_radius=5)
        body = pygame.Rect(bubble.x + 14, bubble.y + 9, bubble.width - 28, 44)
        lines = self._wrapped_message()
        line_height = self.message_font.get_linesize()
        y = body.centery - len(lines) * line_height // 2
        for line in lines:
            self.message_text.text = line
            self.message_text.position = (body.left, y)
            self.message_text.draw(window)
            y += line_height

        pygame.draw.line(
            window, (28, 69, 87),
            (bubble.left + 14, bubble.bottom - 26),
            (bubble.right - 14, bubble.bottom - 26),
        )
        self.prompt_text.text = self.prompt
        self.prompt_text.position = (bubble.right - 14, bubble.bottom - 9)
        self.prompt_text.draw(window)
        if self.phase in self.LESSONS:
            number = tuple(self.LESSONS).index(self.phase) + 1
            self.step_text.text = f"{number} / {len(self.LESSONS)}"
            self.step_text.position = (bubble.left + 14, bubble.bottom - 9)
            self.step_text.draw(window)
