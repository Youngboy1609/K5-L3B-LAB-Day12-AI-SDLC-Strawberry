"""Regression cho ngưỡng chạm, recoil và tương thích gather v1.0."""
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


class GatherMonsters(unittest.TestCase):
    def gather(self, depth, monster, *, day=1, hp=3):
        scenario = {
            "player": {"pos": [60, depth], "hp": hp},
            "hold": ["ca_loc", "bong_sung", "ca_linh", "ca_loc"],
            "monsters": [monster],
            "random_fish": False,
        }
        return GatherSim(load_contract()["tuning"], scenario, Streams(42), IdAllocator(), day=day)

    def step(self, sim):
        return sim.step(InputState((0, 0), {}, set()))

    def test_contact_requires_minimum_player_depth(self):
        sim = self.gather(9.5, {"id": "M1", "pos": [60, 10]})
        self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.hp, 3)

    def test_contact_emits_hit_and_faints_with_empty_inventory(self):
        sim = self.gather(24, {"id": "M1"}, hp=1)
        rows = self.step(sim)
        self.assertEqual([name for name, _ in rows], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(rows[0][1], {"monster_id": "M1", "hp": 0, "lost": ["ca_loc", "ca_linh"]})
        self.assertEqual(rows[-1][1]["inventory"], {"items": {}})

    def test_fixture_recoil_cannot_hit_even_on_last_step(self):
        sim = self.gather(24, {"id": "M1", "state": "recoil", "state_ticks_left": 1, "recoil_dir": [1, 0]})
        self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.monsters[0]["state"], "patrol")
        self.assertAlmostEqual(sim.monsters[0]["pos"][0], 60 + 2 / 60)
        self.assertEqual(self.step(sim)[0][0], "monster_hit")

    def test_phase1_has_no_monster_field_or_hit(self):
        sim = self.gather(24, {"id": "M1"}, day=None)
        self.assertNotIn("monsters", sim.snapshot())
        self.assertEqual(self.step(sim), [])
