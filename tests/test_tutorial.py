"""Check tutorial input gates, dialogue layout, and navigation."""

import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.screen.types.map_selection import MapSelection
from program_files.screen.types.tutorial import Tutorial
from program_files.ui.text_object import get_font


class TutorialTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        get_font.cache_clear()
        pygame.quit()

    def setUp(self):
        self.app = App()
        self.app.get_map_selection()
        selection = self.app.current_screen
        selection.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1,
            pos=selection.tutorial_button.rect.center,
        ))
        self.tutorial = self.app.current_screen
        self.assertIsInstance(self.tutorial, Tutorial)
        self.tutorial.update(self.tutorial.ENTER_DURATION)

    def key(self, key):
        self.tutorial.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def click(self, pos):
        self.tutorial.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=pos,
        ))

    def finish_intro(self):
        for _ in Tutorial.INTRO_LINES:
            self.key(pygame.K_n)
        self.tutorial.update(0.4)
        self.assertEqual(self.tutorial.phase, Tutorial.CHOOSE_TOWER)

    def place_tower(self):
        self.finish_intro()
        self.click(self.tutorial.tower_selection_rects[0].center)
        self.key(pygame.K_q)
        self.click(self.tutorial.tower_selection_rects[0].center)
        self.click(self.tutorial.tower_slots[0].rect.center)
        self.assertEqual(self.tutorial.phase, Tutorial.INSPECT_TOWER)

    def reach_start_lesson(self):
        self.place_tower()
        self.click(self.tutorial.towers[0].rect.center)
        self.click((350, 300))
        self.assertEqual(self.tutorial.phase, Tutorial.STATS)
        self.key(pygame.K_n)
        self.assertEqual(self.tutorial.phase, Tutorial.START_WAVE)

    def assert_waves_locked(self):
        for key in (pygame.K_SPACE, pygame.K_s, pygame.K_p):
            self.key(key)
        self.tutorial.start_wave()
        self.tutorial.skip_wave()
        self.assertFalse(self.tutorial.wave_state.active)
        self.assertFalse(self.tutorial.paused)
        self.assertEqual(self.tutorial.wave_state.round, 1)
        self.assertEqual(self.tutorial.enemy_state.spawn_queue, [])
        self.assertEqual(self.tutorial.enemy_state.enemies, [])

    def test_message_slides_up_before_intro_input_is_enabled(self):
        tutorial = Tutorial(self.app)
        self.app.change_screen(tutorial)
        self.tutorial = tutorial
        self.assertEqual(tutorial.phase, Tutorial.ENTERING)
        self.assertGreaterEqual(
            tutorial.message_rect().top, self.app.DISPLAY_HEIGHT)
        self.key(pygame.K_n)
        self.click((300, 175))
        tutorial.update(tutorial.ENTER_DURATION / 2)
        self.assertGreater(tutorial.message_rect().top,
                           tutorial.message_box.top)
        self.assertLess(tutorial.message_rect().top, self.app.DISPLAY_HEIGHT)
        tutorial.draw(self.app.window)
        self.key(pygame.K_n)
        self.assertEqual(tutorial.intro_index, 0)
        tutorial.update(tutorial.ENTER_DURATION / 2)
        self.assertEqual(tutorial.phase, Tutorial.INTRO)
        self.assertEqual(tutorial.message_rect(), tutorial.message_box)
        self.assertEqual(tutorial.guide_text, "Oh mreow!!!")
        self.key(pygame.K_n)
        self.assertEqual(tutorial.intro_index, 1)

    def test_required_actions_cannot_be_bypassed(self):
        self.assert_waves_locked()
        self.finish_intro()
        self.assert_waves_locked()
        self.key(pygame.K_n)
        self.click(self.tutorial.wave_ready_rect.center)
        self.assertEqual(self.tutorial.phase, Tutorial.CHOOSE_TOWER)

        self.click(self.tutorial.tower_selection_rects[0].center)
        self.assertEqual(self.tutorial.phase, Tutorial.CANCEL_PLACEMENT)
        self.click(self.tutorial.tower_slots[0].rect.center)
        self.assertEqual(self.tutorial.towers, [])
        self.assert_waves_locked()
        self.key(pygame.K_q)
        self.assertEqual(self.tutorial.phase, Tutorial.RESELECT_TOWER)
        self.assertIsNone(self.tutorial.selected_tower_type)

        self.click(self.tutorial.tower_selection_rects[0].center)
        self.assertEqual(self.tutorial.phase, Tutorial.PLACE_TOWER)
        self.assert_waves_locked()
        self.click(self.tutorial.tower_slots[0].rect.center)
        self.assertEqual(self.tutorial.phase, Tutorial.INSPECT_TOWER)
        self.assert_waves_locked()
        self.key(pygame.K_n)
        self.assertEqual(self.tutorial.phase, Tutorial.INSPECT_TOWER)

        self.click(self.tutorial.towers[0].rect.center)
        self.assertEqual(self.tutorial.phase, Tutorial.CLOSE_SIDEBAR)
        self.assert_waves_locked()
        # Closing the sidebar must not sell or upgrade the tower.
        self.click(self.tutorial.sell_button.rect.center)
        self.assertEqual(len(self.tutorial.towers), 1)
        self.assertIsNone(self.tutorial.sidebar_tower)
        self.assertEqual(self.tutorial.phase, Tutorial.STATS)
        self.assert_waves_locked()
        self.click(self.tutorial.wave_ready_rect.center)
        self.assertEqual(self.tutorial.phase, Tutorial.START_WAVE)
        self.assertFalse(self.tutorial.wave_state.active)

    def test_cancel_during_placement_returns_to_selection(self):
        self.finish_intro()
        self.click(self.tutorial.tower_selection_rects[0].center)
        self.key(pygame.K_q)
        self.click(self.tutorial.tower_selection_rects[0].center)
        self.key(pygame.K_q)
        self.assertEqual(self.tutorial.phase, Tutorial.RESELECT_TOWER)
        self.assertIsNone(self.tutorial.selected_tower_type)
        self.assertEqual(self.tutorial.towers, [])

    def test_skipping_starts_wave_two_and_keeps_wave_one_active(self):
        self.reach_start_lesson()
        tutorial = self.tutorial
        self.click(tutorial.wave_ready_rect.center)
        self.assertEqual(tutorial.phase, Tutorial.WATCH_WAVE)
        self.assertEqual(len(tutorial.enemy_state.enemies), 1)
        first_enemy = tutorial.enemy_state.enemies[0]
        tutorial.update(tutorial.SKIP_PROMPT_DELAY + 0.01)
        self.assertEqual(tutorial.phase, Tutorial.SKIP_WAVE)
        self.assertTrue(tutorial.can_skip_wave)

        self.click(tutorial.skip_wave_rect.center)
        self.assertEqual(tutorial.wave_state.round, 2)
        self.assertEqual(tutorial.phase, Tutorial.WAVES)
        self.assertIn(1, tutorial.wave_state.active_waves)
        self.assertIn(2, tutorial.wave_state.active_waves)
        self.assertIn(first_enemy, tutorial.enemy_state.enemies)

    def test_side_panel_hides_back_button_and_click_does_not_leave_tutorial(self):
        self.place_tower()
        tower = self.tutorial.towers[0]
        self.click(tower.rect.center)
        self.assertIs(self.tutorial.sidebar_tower, tower)
        with patch.object(self.tutorial.back_button, "draw") as draw_back:
            self.tutorial.draw(self.app.window)
            draw_back.assert_not_called()

        self.click(self.tutorial.back_button.rect.center)
        self.assertIsNone(self.tutorial.sidebar_tower)
        self.assertEqual(self.tutorial.phase, Tutorial.STATS)
        self.assertIs(self.app.current_screen, self.tutorial)

    def test_space_and_s_advance_only_their_own_lessons(self):
        self.reach_start_lesson()
        self.key(pygame.K_s)
        self.assertEqual(self.tutorial.phase, Tutorial.START_WAVE)
        self.key(pygame.K_SPACE)
        self.assertEqual(self.tutorial.phase, Tutorial.WATCH_WAVE)
        self.tutorial.update(self.tutorial.SKIP_PROMPT_DELAY)
        self.assertEqual(self.tutorial.phase, Tutorial.SKIP_WAVE)
        self.key(pygame.K_SPACE)
        self.assertEqual(self.tutorial.wave_state.round, 1)
        self.key(pygame.K_s)
        self.assertEqual(self.tutorial.phase, Tutorial.WAVES)
        self.assertEqual(self.tutorial.wave_state.round, 2)

    def test_skip_prompt_and_s_wait_until_the_delay(self):
        self.reach_start_lesson()
        self.key(pygame.K_SPACE)
        tutorial = self.tutorial
        self.assertEqual(tutorial.phase, Tutorial.WATCH_WAVE)
        self.assertFalse(tutorial.can_skip_wave)
        self.key(pygame.K_s)
        self.key(pygame.K_n)
        self.click(tutorial.skip_wave_rect.center)
        tutorial.skip_wave()
        self.assertEqual(tutorial.wave_state.round, 1)
        tutorial.update(tutorial.SKIP_PROMPT_DELAY - 0.1)
        self.assertEqual(tutorial.phase, Tutorial.WATCH_WAVE)
        with patch.object(tutorial, "draw_skip_wave") as skip_prompt:
            tutorial.draw(self.app.window)
            skip_prompt.assert_not_called()
        tutorial.update(0.11)
        self.assertEqual(tutorial.phase, Tutorial.SKIP_WAVE)
        self.assertTrue(tutorial.can_skip_wave)
        with patch.object(tutorial, "draw_skip_wave") as skip_prompt:
            tutorial.draw(self.app.window)
            skip_prompt.assert_called_once()

    def test_back_works_from_all_phases_with_or_without_a_parent(self):
        phases = (Tutorial.ENTERING, Tutorial.INTRO, Tutorial.INTRO_OUT,
                  *Tutorial.LESSONS,
                  Tutorial.GOOD_LUCK, Tutorial.FAILED, Tutorial.EXITING)
        for root in (True, False):
            for phase in phases:
                with self.subTest(root=root, phase=phase):
                    tutorial = Tutorial(self.app)
                    tutorial.phase = phase
                    if root:
                        self.app.change_screen(tutorial)
                    else:
                        self.app.get_map_selection()
                        self.app.push_screen(tutorial)
                    tutorial.handle_event(pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, button=1,
                        pos=tutorial.back_button.rect.center,
                    ))
                    self.assertIs(self.app.current_screen, tutorial)
                    tutorial.update(tutorial.EXIT_DURATION)
                    self.assertIsInstance(
                        self.app.current_screen, MapSelection)
                    self.assertEqual(len(self.app.screen_stack), 1)

    def test_escape_does_not_leave_tutorial(self):
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.tutorial.phase, Tutorial.INTRO)
        self.assertIs(self.app.current_screen, self.tutorial)

    def test_cat_stays_perched_across_sentences_and_drops_before_lessons(self):
        tutorial = self.tutorial
        self.assertEqual(tutorial.cat_pop, 0)
        self.key(pygame.K_n)
        tutorial.update(0.4)
        self.assertEqual(tutorial.cat_pop, 1)
        bubble = tutorial.message_rect()
        self.assertEqual(tutorial.cat_rect(bubble).bottom, bubble.top + 8)
        self.key(pygame.K_n)
        self.assertEqual(tutorial.cat_pop, 1)
        tutorial.update(0.1)
        bubble = tutorial.message_rect()
        self.assertLess(bubble.top, tutorial.message_box.top)
        self.assertEqual(tutorial.cat_rect(bubble).bottom, bubble.top + 8)
        for _ in range(4):
            self.key(pygame.K_n)
        self.assertEqual(tutorial.phase, Tutorial.INTRO_OUT)
        tutorial.update(0.1)
        self.assertGreater(tutorial.cat_pop, 0)
        self.assertLess(tutorial.cat_pop, 1)
        tutorial.update(0.2)
        self.assertEqual(tutorial.cat_pop, 0)
        self.assertEqual(tutorial.phase, Tutorial.CHOOSE_TOWER)

    def test_messages_fit_and_do_not_cover_the_active_controls(self):
        tutorial = self.tutorial
        self.assertEqual(tutorial.CONTINUE_PROMPT, "PRESS [N] OR CLICK")
        messages = list(tutorial.LESSONS.values()) + [
            (text, tutorial.CONTINUE_PROMPT)
            for text in (*tutorial.INTRO_LINES, *tutorial.OUTRO_LINES)
        ]
        for message, prompt in messages:
            with self.subTest(message=message):
                tutorial.guide_text = message
                lines = tutorial.wrapped_message()
                self.assertLessEqual(
                    len(lines) * tutorial.message_font.get_linesize(), 44
                )
                prompt_font = get_font(
                    tutorial.prompt_text.font,
                    tutorial.prompt_text.font_size,
                )
                self.assertLess(
                    prompt_font.size(prompt)[0],
                    tutorial.message_box.width - 28,
                )
        for target in (
            tutorial.wave_ready_rect, tutorial.skip_wave_rect,
            tutorial.back_button.rect, *tutorial.tower_selection_rects,
            *(slot.rect for slot in tutorial.tower_slots),
        ):
            self.assertFalse(tutorial.message_box.colliderect(target))
        # The HUD PNG is 197px wide, but its visible bar ends at 173px.
        self.assertEqual(tutorial.health_power_highlight,
                         pygame.Rect(8, 13, 177, 32))


if __name__ == "__main__":
    unittest.main()
