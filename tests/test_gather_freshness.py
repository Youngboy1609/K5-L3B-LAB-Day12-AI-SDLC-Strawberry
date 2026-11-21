"""Phase 3 gather rules at the simulation boundary."""

import json
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.inventory import write_inventory
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim


def item(ident, fresh=100):
    return {"id": ident, "kind": "ca_linh", "fresh": fresh}


class GatherFreshness(unittest.TestCase):
    def build(self, **fixture):
        tuning = load_contract()["tuning"]
        scenario = {"monsters": [], "random_fish": False, **fixture}
        return GatherSim(tuning, scenario, Streams(42), IdAllocator(), contract_version="1.2",
                         freshness={"initial": 100, "gather_decay_per_s": 0.5, "spoiled_below": 30})

    def step(self, sim, *buttons):
        return sim.step(InputState((0, 0), {}, set(buttons)))

    def test_decay_after_regrowth_before_harvest_and_only_one_spoil_event(self):
        sim = self.build(hold=[item("I10", 30), item("I2", 30), item("I1", 0)],
                         player={"pos": [50, 0]}, nodes=[
                             {"id": "N1", "kind": "bong_sung", "pos": [50, 0], "regrow_ticks": 1},
                         ])
        events = self.step(sim, "interact")
        self.assertEqual([name for name, _ in events], ["node_regrown", "spoiled", "spoiled", "gather"])
        self.assertEqual([data["item_id"] for _, data in events[1:3]], ["I2", "I10"])
        self.assertEqual([entry["id"] for entry in sim.hold], ["I10", "I2", "I1", "I11"])
        self.assertEqual(sim.hold[0]["fresh"], 30 - Fraction(1, 120))
        self.assertEqual(sim.hold[2]["fresh"], 0)
        self.assertEqual(sim.hold[-1]["fresh"], 100)
        self.assertEqual(self.step(sim), [])
        self.assertEqual(sim.hold[-1]["fresh"], 100 - Fraction(1, 120))

    def test_final_tick_catch_assigns_an_id_per_fish_and_exports_file_payload(self):
        sim = self.build(hold=[item("I10"), item("I2")], time_left_ticks=1,
                         player={"pos": [50, 5]},
                         fish=[{"id": "F1", "kind": "ca_linh", "pos": [50, 5]}])
        caught, end = self.step(sim, "catch")
        count = sim.t["fish_yield"]["ca_linh"]
        self.assertEqual(caught[0], "fish_caught")
        self.assertEqual([i["id"] for i in sim.hold[2:]], [f"I{i}" for i in range(11, 11 + count)])
        self.assertTrue(all(i["fresh"] == 100 for i in sim.hold[2:]))
        self.assertEqual(end[1]["reason"], "time")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            write_inventory(path, sim.inventory_items(), contract_version="1.2")
            self.assertEqual(end[1]["inventory"], json.loads(path.read_text(encoding="utf-8")))

    def test_hit_and_faint_drop_in_lifo_order_including_spoiled_items(self):
        sim = self.build(hold=[item("I7"), item("I2"), item("I5", 10)],
                         player={"pos": [60, 24], "hp": 1}, monsters=[{"id": "M1"}])
        hit, faint, end = self.step(sim)
        self.assertEqual([hit[0], faint[0], end[0]], ["monster_hit", "faint", "gather_end"])
        self.assertEqual([i["id"] for i in hit[1]["lost"]], ["I5"])
        self.assertEqual([i["id"] for i in faint[1]["lost"]], ["I2", "I7"])
        self.assertEqual(end[1]["inventory"], {"items": []})
        self.assertEqual(sim.inventory_items(), [])
