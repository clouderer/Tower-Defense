"""Buy and upgrade towers through the gameplay interface."""


# @generated fully ChatGPT 6.1 Sol: Tests


import pygame

from program_files.screen.types.gameplay.gameplay import Gameplay
from .simulate_balance import TowerShop


class UiTowerShop(TowerShop):
    """Follow a build strategy using the normal gameplay controls."""

    def __init__(
        self,
        game,
        strategy,
        max_towers,
        starter_firewalls=1,
        record_action=None,
    ):
        """Store the strategy and an optional purchase recorder."""
        super().__init__(game, strategy, max_towers, starter_firewalls)
        self.record_action = record_action

    def check_gameplay(self):
        """Require this game to be active, unpaused, and unfinished."""
        game = self.game
        if (
            not isinstance(game, Gameplay)
            or getattr(game.app, "current_screen", None) is not game
        ):
            raise RuntimeError("The active screen must be this game.")
        if game.paused or game.game_over or game.wave_state.won:
            raise RuntimeError("The game must be unpaused and unfinished.")
        if game.health <= 0:
            raise RuntimeError("Purchases require a living player.")

    def send_event(self, event):
        """Send an in-process input event to the active game screen."""
        self.check_gameplay()
        self.game.app.current_screen.handle_event(event)

    def click(self, position):
        """Move the interface pointer and send a complete left click."""
        self.send_event(pygame.event.Event(
            pygame.MOUSEMOTION, pos=position, rel=(0, 0), buttons=(0, 0, 0),
        ))
        self.send_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, pos=position, button=1,
        ))
        self.send_event(pygame.event.Event(
            pygame.MOUSEBUTTONUP, pos=position, button=1,
        ))

    def prepare_input(self):
        """Cancel placement and close any open tower sidebar."""
        self.send_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_q, mod=0, unicode="q",
        ))
        self.click((590, 180))
        if (
            self.game.selected_tower_type is not None
            or self.game.sidebar_tower is not None
        ):
            raise RuntimeError("The tower controls did not close correctly.")

    def place_tower(self, tower_type, slot):
        """Select a tower from its menu and click its slot."""
        self.check_gameplay()
        game = self.game
        if tower_type not in game.TOWER_SELECTION:
            raise RuntimeError("The tower is missing from the selection menu.")
        if not any(item is slot for item in game.tower_slots):
            raise RuntimeError("This slot does not belong to the map.")
        if slot.occupied or game.money < tower_type.COST:
            raise RuntimeError("The selected tower cannot be placed here.")

        self.prepare_input()
        previous_towers = tuple(game.towers)
        previous_money = game.money
        cost = tower_type.COST
        menu_index = game.TOWER_SELECTION.index(tower_type)
        self.click(game.tower_selection_rects[menu_index].center)
        if game.selected_tower_type is not tower_type:
            raise RuntimeError("The menu did not select the right tower.")
        self.click(slot.rect.center)

        if len(game.towers) != len(previous_towers) + 1:
            raise RuntimeError("The slot click did not place one new tower.")
        tower = game.towers[-1]
        if (
            tuple(game.towers[:-1]) != previous_towers
            or type(tower) is not tower_type
            or tower.tower_slot is not slot
            or not slot.occupied
            or game.selected_tower_type is not None
            or game.money != previous_money - cost
        ):
            raise RuntimeError("The tower placement changed unexpected state.")
        self.record_purchase("build", tower, cost)

    def upgrade_tower(self, tower):
        """Open the sidebar and click the tower's upgrade button."""
        self.check_gameplay()
        game = self.game
        if not any(item is tower for item in game.towers):
            raise RuntimeError("This tower does not belong to the game.")
        cost = tower.next_upgrade_cost
        if cost is None or game.money < cost:
            raise RuntimeError("The selected tower cannot be upgraded.")

        self.prepare_input()
        previous_level = tower.level
        previous_money = game.money
        previous_cost = tower.total_cost
        self.click(tower.rect.center)
        if (
            game.sidebar_tower is not tower
            or game.sidebar_tower_idx != game.towers.index(tower)
        ):
            raise RuntimeError("The sidebar selected the wrong tower.")
        self.click(game.upgrade_button.rect.center)
        if (
            tower.level != previous_level + 1
            or game.money != previous_money - cost
            or tower.total_cost != previous_cost + cost
        ):
            raise RuntimeError("The upgrade changed unexpected state.")
        self.click((590, 180))
        if game.sidebar_tower is not None:
            raise RuntimeError("The sidebar did not close after upgrading.")
        self.record_purchase("upgrade", tower, cost)

    def record_purchase(self, action, tower, cost):
        """Record the purchase after its interface checks succeed."""
        if self.record_action is not None:
            self.record_action({
                "action": action,
                "tower_type": type(tower).__name__,
                "level": tower.level,
                "slot_x": tower.tower_slot.rect.x,
                "slot_y": tower.tower_slot.rect.y,
                "cost": cost,
                "money": self.game.money,
            })
