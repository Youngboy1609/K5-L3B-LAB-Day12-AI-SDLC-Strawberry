"""Kiểm chuyển đổi hợp đồng kho và luật cá khi nối Phase 2."""
from contextlib import redirect_stderr
from io import StringIO
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.headless import main
from helpers import Workdir, events, frames, read_jsonl, snapshots, write_json


class Phase2Fish(unittest.TestCase):
    def setUp(self):
        self.work = self.enterContext(Workdir())
        self.contract = load_contract()
        self.contract["contract_version"] = "1.1"
        self.gather = self.contract["tuning"]["gather"]
        self.gather["fish_yield"]["ca_keo"] = 1
        self.gather["fish_motion"] = {
            "ca_keo": {"speed_m_per_s": 6}, "ca_loc": {"speed_m_per_s": 6},
        }
        self.gather["fish_spawn"] = {
            "interval_s": 1 / 60, "kinds": ["ca_keo"], "area": {"x": [30, 30], "d": [5, 5]}, "max": 8,
        }
        self.fish = {"id": "F7", "kind": "ca_keo", "pos": [20, 5], "age_ticks": 12}

    def run_mode(self, mode, scenario, *, ticks=0, inputs=None, extra=(), expect=0, diagnostic=None):
        path = write_json(self.work.path("scenario.json"), {mode: scenario} if mode != "day" else scenario)
        output = self.work.path("output.jsonl")
        contract_path = write_json(self.work.path("contract.json"), self.contract)
        args = ["--mode", mode, "--seed", "42", "--ticks", str(ticks), "--snapshot-every", "1",
                "--scenario", path, "--out", output, *extra]
        if inputs is not None:
            args += ["--inputs", write_json(self.work.path("inputs.json"), inputs)]
        errors = StringIO()
        with patch("chonoi.headless.load_contract", side_effect=lambda: load_contract(contract_path)):
            with redirect_stderr(errors):
                self.assertEqual(main(args), expect, errors.getvalue())
        if diagnostic:
            self.assertIn(diagnostic, errors.getvalue())
        return read_jsonl(output) if expect == 0 else []

    def test_v1_inventory_rejects_new_ingredients(self):
        self.contract["contract_version"] = "1.0"
        self.gather["nodes"] = [node for node in self.gather["nodes"] if node["kind"] != "keo_neo"]
        self.run_mode("quan", {"stock": {"ca_keo": 1}}, expect=2, diagnostic="nguyên liệu lạ: ca_keo")
        stock_file = write_json(self.work.path("inventory.json"), {"items": {"keo_neo": 2}})
        self.run_mode("quan", {}, extra=["--inventory", stock_file], expect=2, diagnostic="nguyên liệu lạ: keo_neo")

    def test_v11_quan_reads_new_ingredients_from_file(self):
        stock = {"ca_keo": 1, "keo_neo": 2}
        stock_file = write_json(self.work.path("inventory.json"), {"items": stock})
        rows = self.run_mode("quan", {}, extra=["--inventory", stock_file])
        self.assertEqual(snapshots(rows)[0]["stock"], stock)

    def test_stationary_fixture_preserves_age_and_disables_spawning(self):
        fish = dict(self.fish, kind="ca_loc")
        rows = self.run_mode("gather", {"fish": [fish], "random_fish": False}, ticks=2)
        for snap in snapshots(rows):
            self.assertEqual(len(snap["fish"]), 1)
            self.assertEqual(snap["fish"][0]["age_ticks"], 12)
            self.assertEqual(snap["fish"][0]["pos"], fish["pos"])
        self.assertEqual(events(rows, "fish_spawned"), [])

    def test_moving_fixture_ages_and_spawned_school_starts_at_zero(self):
        rows = self.run_mode("gather", {"fish": [self.fish]}, ticks=1)
        ss = snapshots(rows)
        self.assertEqual(ss[0]["fish"][0]["age_ticks"], 12)
        self.assertAlmostEqual(ss[1]["fish"][0]["pos"][0], 20.1)
        self.assertEqual(ss[1]["fish"][0]["age_ticks"], 13)
        self.assertEqual(ss[1]["fish"][1]["age_ticks"], 0)
        self.assertEqual([row["data"]["fish_id"] for row in events(rows, "fish_spawned")], ["F8"])

    def test_final_tick_catches_but_does_not_spawn(self):
        scenario = {"fish": [self.fish], "player": {"pos": [20, 5]}, "time_left_ticks": 1}
        rows = self.run_mode("gather", scenario, ticks=1, inputs=frames({"tick": 0, "catch": True}))
        self.assertEqual([row["name"] for row in events(rows)], ["fish_caught", "gather_end"])
        self.assertEqual(events(rows)[-1]["data"]["inventory"]["items"], {"ca_keo": 1})

    def test_day_hands_off_new_ingredients_and_validates_reservation(self):
        tuning = self.contract["tuning"]
        if not any(node["kind"] == "keo_neo" for node in self.gather["nodes"]):
            self.gather["nodes"].append({"id": "N5", "kind": "keo_neo", "pos": [24, 0]})
        stock = {"ca_keo": 1, "keo_neo": 1}
        tuning["menu"]["ca_keo_test"] = {"recipe": stock, "price": 40, "cook_s": 4}
        tuning["day"] = {"day_plans": {"1": {"dishes": {"ca_keo_test": 1}}}, "shop_ticks": 600,
                         "upgrades": {}}
        fixture = {
            "gather": {"hold": list(stock), "random_fish": False},
            "quan": {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_keo_test", "reserved": stock}]},
        }
        rows = self.run_mode("day", fixture, ticks=1, inputs=frames({"tick": 0, "interact": True}))
        snap = snapshots(rows)[-1]
        self.assertEqual(snap["phase"], "quan")
        self.assertEqual(snap["stock"], stock)
        self.assertEqual(snap["customers"][0]["reserved"], stock)
