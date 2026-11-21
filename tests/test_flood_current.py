"""Dòng lũ v1.2: lịch, dịch chuyển, hướng và tạm dừng."""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import V11Session


class FloodCurrentTest(unittest.TestCase):
    def game(self, **fixture):
        tuning = load_contract()["tuning"]
        tuning["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                               "quan_decay_per_s": 0.25, "spoiled_below": 30}
        tuning["gather"]["current"] = {"interval_ticks": 3, "duration_ticks": 2,
                                       "warning_ticks": 1, "min_depth": 4, "speed": 3}
        return V11Session("gather", tuning, {"random_fish": False, "monsters": [],
                          "player": {"pos": [50, 5]}, **fixture}, 42, contract_version="1.2")

    def step(self, game, *buttons):
        return [row["name"] for row in game.step(InputState((0, 0), {}, set(buttons)))]

    def test_warning_active_ticks_and_pause(self):
        game = self.game(current_direction=-1)
        self.assertIsNone(game.snapshot()["current"])
        self.assertEqual(self.step(game), [])
        self.assertEqual(self.step(game), ["current_warning"])
        self.assertEqual(self.step(game, "pause"), ["paused"])
        self.assertIsNone(game.snapshot()["current"])
        self.assertEqual(self.step(game), [])
        self.assertEqual(self.step(game, "pause"), ["resumed", "current_started"])
        self.assertEqual(game.snapshot()["current"], {"direction": -1, "ticks_left": 2})
        self.assertAlmostEqual(game.sim.pos[0], 49.95)
        self.step(game)
        self.assertEqual(game.snapshot()["current"]["ticks_left"], 1)
        self.assertEqual(self.step(game), ["current_ended", "current_warning"])
        self.assertIsNone(game.snapshot()["current"])
        self.assertAlmostEqual(game.sim.pos[0], 49.9)

    def test_disabled_and_shallow_players_do_not_drift(self):
        disabled = self.game(random_current=False)
        shallow = self.game(player={"pos": [50, 2]}, current_direction=1)
        for _ in range(5):
            self.assertEqual(self.step(disabled), [])
            self.step(shallow)
        self.assertIsNone(disabled.snapshot()["current"])
        self.assertEqual([disabled.sim.pos[0], shallow.sim.pos[0]], [50, 50])
