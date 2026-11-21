"""AC-P1-01/02: kiểm luật gather qua headless, không phụ thuộc lớp Python.

Các ca này là tiêu chí bàn giao; thất bại khi gameplay còn TODO là lỗi thật,
không đánh dấu skip/expectedFailure. Chưa kiểm payload event đang chờ P1-01.
"""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("game.contract.json", encoding="utf-8") as f:
            cls.tuning = json.load(f)["tuning"]
        cls.g = cls.tuning["gather"]
        cls.hz = cls.tuning["tick_hz"]

    def run_case(self, block, ticks=1, inputs=()):
        with Workdir() as w:
            scenario = {"nodes": [], "fish": [], "player": {"pos": [50, 5]}}
            scenario.update(block)
            out, inv = w.path("out.jsonl"), w.path("inventory.json")
            code, err = run_headless(
                "--mode", "gather", "--seed", "1", "--ticks", str(ticks),
                "--scenario", write_json(w.path("scenario.json"), {"gather": scenario}),
                "--inputs", write_json(w.path("inputs.json"), frames(*inputs)),
                "--snapshot-every", "1", "--inventory-out", inv, "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            # Chỉ đọc kho khi game thật sự kết thúc, không nhầm tick_limit.
            inventory = None
            if rows[-1]["state"] == "finished":
                with open(inv, encoding="utf-8") as f:
                    inventory = json.load(f)
            return rows, inventory

    def test_underwater_consumes_one_oxygen_per_tick(self):
        rows, _ = self.run_case({"player": {"pos": [50, 5], "oxygen_ticks": 10}}, ticks=3)
        self.assertEqual(snapshots(rows)[-1]["player"]["oxygen_ticks"], 7)

    def test_surface_refills_oxygen_and_clamps_at_max(self):
        maximum = round(self.g["oxygen_max_s"] * self.hz)
        for initial in (0, maximum - 1):
            with self.subTest(initial=initial):
                rows, _ = self.run_case({"player": {"pos": [50, 0], "oxygen_ticks": initial}})
                self.assertEqual(snapshots(rows)[-1]["player"]["oxygen_ticks"],
                                 min(maximum, initial + self.g["oxygen_refill_per_tick"]))

    def test_choke_occurs_after_full_interval_including_empty_tick(self):
        interval = self.g["choke_interval_ticks"]
        rows, _ = self.run_case({"player": {"pos": [50, 5], "oxygen_ticks": 1}}, ticks=interval)
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(by_tick[interval - 1]["player"]["hp"], self.g["hp_max"])
        self.assertEqual(by_tick[interval]["player"]["hp"], self.g["hp_max"] - 1)
        self.assertEqual([e["tick"] for e in events(rows, "oxygen_empty")], [1])
        self.assertEqual([e["tick"] for e in events(rows, "choke")], [interval])

    def test_faint_discards_hold_and_exports_empty_inventory(self):
        rows, inventory = self.run_case({
            "player": {"pos": [50, 5], "hp": 1, "oxygen_ticks": 0},
            "hold": ["ca_loc", "bong_sung"],
        }, ticks=self.g["choke_interval_ticks"])
        self.assertEqual(rows[-1]["reason"], "fainted")
        self.assertEqual(snapshots(rows)[-1]["hold"], [])
        self.assertEqual(inventory, {"items": {}})
        self.assertEqual(len(events(rows, "faint")), 1)
        self.assertEqual(len(events(rows, "gather_end")), 1)

    def test_regrown_node_can_be_harvested_in_same_tick(self):
        rows, _ = self.run_case({
            "player": {"pos": [50, 0]},
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0], "regrow_ticks": 1}],
        }, inputs=({"tick": 0, "interact": True},))
        final = snapshots(rows)[-1]
        self.assertEqual(final["hold"], ["bong_sung"] * self.g["node_yield"])
        self.assertEqual(final["nodes"][0]["regrow_ticks"], round(self.g["regrow_s"] * self.hz))
        self.assertEqual([e["name"] for e in events(rows)], ["node_regrown", "gather"])

    def test_full_hold_preserves_ready_node(self):
        hold = ["ca_loc"] * self.g["hold_capacity"]
        rows, _ = self.run_case({
            "player": {"pos": [50, 0]}, "hold": hold,
            "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [50, 0]}],
        }, inputs=({"tick": 0, "interact": True},))
        final = snapshots(rows)[-1]
        self.assertEqual(final["hold"], hold)
        self.assertTrue(final["nodes"][0]["ready"])
        self.assertEqual(len(events(rows, "hold_full")), 1)
        self.assertEqual(events(rows, "gather"), [])

    def test_insufficient_capacity_preserves_entire_fish_school(self):
        kind = max(self.g["fish_yield"], key=self.g["fish_yield"].get)
        remaining = self.g["fish_yield"][kind] - 1
        hold = ["bong_sung"] * (self.g["hold_capacity"] - remaining)
        rows, _ = self.run_case({
            "hold": hold, "fish": [{"id": "F1", "kind": kind, "pos": [50, 5]}],
        }, inputs=({"tick": 0, "catch": True},))
        final = snapshots(rows)[-1]
        self.assertEqual(final["hold"], hold)
        self.assertEqual([f["id"] for f in final["fish"]], ["F1"])
        self.assertEqual(final["player"]["catch_cd_ticks"], 0)
        self.assertEqual(len(events(rows, "hold_full")), 1)

    def test_catch_on_last_tick_is_in_exported_inventory(self):
        kind = "ca_linh"
        rows, inventory = self.run_case({
            "time_left_ticks": 1,
            "fish": [{"id": "F1", "kind": kind, "pos": [50, 5]}],
        }, inputs=({"tick": 0, "catch": True},))
        self.assertEqual(rows[-1]["reason"], "time")
        self.assertEqual(inventory, {"items": {kind: self.g["fish_yield"][kind]}})
        self.assertEqual(snapshots(rows)[-1]["fish"], [])
        self.assertEqual([e["name"] for e in events(rows)], ["fish_caught", "gather_end"])


if __name__ == "__main__":
    unittest.main()
