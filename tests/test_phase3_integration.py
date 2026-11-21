"""QA v1.2: CLI thật trên bản sao tạm; không đổi manifest đang tích hợp.

Các kỳ vọng lấy từ docs/plan/phase-3.md. Không skip khi runtime chưa hỗ trợ.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

from helpers import ROOT, events, frames, read_jsonl, snapshots, write_json

FIXTURES = Path(ROOT) / "docs/proof/phase-3/fixtures"


def item(i="I1", kind="ca_linh", fresh=100):
    return {"id": i, "kind": kind, "fresh": fresh}


class FreshnessIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="chonoi-p3-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(Path(ROOT) / "chonoi", self.root / "chonoi",
                        ignore=shutil.ignore_patterns("__pycache__"))
        self.contract = json.loads((FIXTURES / "contract-v1.1.json").read_text())
        self.contract["contract_version"] = "1.2"
        # Preset đề xuất trong kế hoạch; chưa sửa contract khóa của nhóm.
        self.contract["freshness"] = dict(initial=100, gather_decay_per_s=0.5,
                                         quan_decay_per_s=0.25, spoiled_below=30)
        self.save("game.contract.json", self.contract)

    def save(self, name, data):
        return write_json(str(self.root / name), data)

    def run_cli(self, mode, scenario=None, controls=None, ticks=1, out="out.jsonl", extra=()):
        args = [sys.executable, "-m", "chonoi.headless", "--mode", mode,
                "--seed", "42", "--ticks", str(ticks), "--snapshot-every", "1",
                "--out", str(self.root / out)]
        if scenario is not None:
            args += ["--scenario", self.save("scenario.json", scenario)]
        if controls is not None:
            args += ["--inputs", self.save("inputs.json", frames(*controls))]
        env = dict(os.environ, PYTHONPATH=str(self.root))
        result = subprocess.run([*args, *extra], cwd=self.root, env=env,
                                capture_output=True, text=True, timeout=30)
        return result.returncode, result.stderr

    def ok(self, *args, **kwargs):
        code, err = self.run_cli(*args, **kwargs)
        self.assertEqual(code, 0, err)
        return read_jsonl(self.root / kwargs.get("out", "out.jsonl"))

    def gather(self, hold=None, **kwargs):
        return {"gather": dict(hold=hold if hold is not None else [item()],
                               random_fish=False, monsters=[], **kwargs)}

    def test_file_handoff_preserves_identity_and_unrounded_freshness(self):
        rows = self.ok("gather", self.gather(), [{"tick": 0, "interact": True}],
                       extra=("--inventory-out", str(self.root / "inventory.json")))
        stock = json.loads((self.root / "inventory.json").read_text())["items"]
        self.assertEqual(len(stock), 1)
        self.assertEqual((stock[0]["id"], stock[0]["kind"]), ("I1", "ca_linh"))
        self.assertAlmostEqual(stock[0]["fresh"], float(Fraction(100) - Fraction(1, 120)), places=10)
        self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"]["items"], stock)
        quan = self.ok("quan", ticks=0, extra=("--inventory", str(self.root / "inventory.json")))
        self.assertEqual(snapshots(quan)[0]["stock"], stock)

    def test_spoiled_crossing_once_sorted_by_id(self):
        rows = self.ok("gather", self.gather([item("I2", fresh=30), item("I1", fresh=30)]), ticks=2)
        spoiled = events(rows, "spoiled")
        self.assertEqual([(e["tick"], e["data"]) for e in spoiled], [
            (1, {"item_id": i, "kind": "ca_linh", "location": "hold"}) for i in ("I1", "I2")])

    def test_exact_threshold_still_fresh_at_tick_zero(self):
        rows = self.ok("gather", self.gather([item(fresh=30)]), ticks=0)
        self.assertEqual(snapshots(rows)[0]["hold"], [item(fresh=30)])
        self.assertEqual(events(rows, "spoiled"), [])

    def test_invalid_inventory_rejected_without_replacing_output(self):
        # Positive control prevents a loader rejecting all v1.2 from passing this test.
        good = self.save("inventory.json", {"items": [item()]})
        self.ok("quan", ticks=0, extra=("--inventory", good))
        bad = [{"ca_linh": 1}, [item(), item()], [item("")],
               [item(kind="unknown")], [item(fresh=True)], [item(fresh=-1)],
               [item(fresh=101)], [dict(item(), unexpected=1)]]
        for value in bad:
            with self.subTest(value=value):
                self.save("inventory.json", {"items": value})
                target = self.root / "out.jsonl"
                target.write_bytes(b"existing-output\n")
                code, err = self.run_cli("quan", ticks=0, extra=("--inventory", good))
                self.assertEqual(code, 2, err)
                self.assertTrue(err)
                self.assertEqual(target.read_bytes(), b"existing-output\n")

    def test_inventory_can_exceed_basket_capacity(self):
        count = self.contract["tuning"]["gather"]["hold_capacity"] + 1
        stock = [item(f"I{i}") for i in range(1, count + 1)]
        path = self.save("inventory.json", {"items": stock})
        rows = self.ok("quan", ticks=0, extra=("--inventory", path))
        self.assertEqual(len(snapshots(rows)[0]["stock"]), count)

    def test_unfinished_gather_preserves_inventory_destination(self):
        path = self.root / "inventory.json"
        path.write_bytes(b"existing-inventory\n")
        self.ok("gather", self.gather(), ticks=1, extra=("--inventory-out", str(path)))
        self.assertEqual(path.read_bytes(), b"existing-inventory\n")

    def test_faint_exports_empty_array_and_lifo_loss(self):
        hold = [item(f"I{i}") for i in range(1, 5)]
        scenario = self.gather(hold, player={"pos": [60, 24], "hp": 1})
        scenario["gather"]["monsters"] = [{"id": "M1"}]
        rows = self.ok("gather", scenario, extra=("--inventory-out", str(self.root / "inventory.json")))
        self.assertEqual([x["id"] for x in events(rows, "monster_hit")[0]["data"]["lost"]], ["I4", "I3"])
        self.assertEqual(json.loads((self.root / "inventory.json").read_text()), {"items": []})

    def test_day_handoff_shop_freezes_and_day_two_renews_ids(self):
        scenario = self.gather()
        scenario["quan"] = {"time_left_ticks": 1, "random_customers": False, "customers": []}
        controls = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                    {"tick": 4, "shop_done": True}]
        rows = self.ok("day", scenario, controls, ticks=5, extra=("--days", "2"))
        ss = {s["tick"]: s for s in snapshots(rows)}
        ended = events(rows, "gather_end")[0]
        start = next(e for e in events(rows, "phase_start") if e["phase"] == "quan")
        self.assertEqual(ended["tick"], start["tick"])
        self.assertEqual((ss[1]["phase"], ss[1]["phase_tick"]), ("quan", 0))
        self.assertEqual(ss[1]["stock"], ended["data"]["inventory"]["items"])
        self.assertEqual(ss[2]["stock"], ss[3]["stock"])
        self.assertEqual(ss[3]["stock"], ss[4]["stock"])
        self.assertEqual((ss[5]["day"], ss[5]["phase"]), (2, "gather"))
        new = ss[5]["hold"][0]
        self.assertNotEqual(new["id"], "I1")
        self.assertEqual((new["kind"], new["fresh"]), ("ca_linh", 100))

    def test_price_floor_after_decay_and_items_sorted(self):
        tuning = self.contract["tuning"]
        dish = "ca_keo_kho_keo_neo"
        hz = tuning["tick_hz"]
        decay = Fraction(str(self.contract["freshness"]["quan_decay_per_s"])) / hz
        for a, b in ((60, 59.99), (60, 60)):
            with self.subTest(a=a, b=b):
                stock = [item("I2", "keo_neo", float(Fraction(str(b)) + decay)),
                         item("I1", "ca_keo", float(Fraction(str(a)) + decay))]
                scenario = {"quan": {"stock": stock, "random_customers": False,
                    "player": {"pos": tuning["quan"]["stoves"][0]["pos"]},
                    "customers": [{"id": "C1", "table_id": tuning["quan"]["tables"][0]["id"],
                                   "dish_id": dish, "order_tick": 0, "reserved": ["I1", "I2"]}]}}
                rows = self.ok("quan", scenario, [{"tick": 0, "interact": True}])
                cooked = events(rows, "cook_started")[0]["data"]
                # Calculate from the actual JSON fixture decimals, not rounded display values.
                total = sum((Fraction(str(x["fresh"])) - decay for x in stock), Fraction())
                expected = (tuning["menu"][dish]["price"] * total / 200).__floor__()
                self.assertEqual(cooked["base_price"], expected)
                self.assertEqual([x["id"] for x in cooked["items"]], ["I1", "I2"])

    def test_day_renews_explicit_reserved_ids_with_fixture_inventory(self):
        scenario = self.gather([item(kind="ca_loc")])
        scenario["day"] = {"day_plan": {"dishes": {"ca_loc_nuong_trui": 1}}}
        scenario["quan"] = {"time_left_ticks": 1, "random_customers": False, "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]}
        controls = [{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                    {"tick": 2, "shop_done": True},
                    {"tick": 3, "shop_done": False, "interact": True}]
        rows = self.ok("day", scenario, controls, ticks=4, extra=("--days", "2"))
        opens = [s for s in snapshots(rows) if s["phase"] == "quan"]
        self.assertEqual([(s["day"], s["phase_tick"]) for s in opens], [(1, 0), (2, 0)])
        self.assertEqual([s["customers"][0]["reserved"] for s in opens], [["I1"], ["I2"]])
        self.assertEqual([s["stock"][0]["id"] for s in opens], ["I1", "I2"])

    def test_reserved_ids_cannot_be_shared_and_day_output_is_atomic(self):
        scenario = self.gather([item(kind="ca_loc")])
        tables = self.contract["tuning"]["quan"]["tables"]
        scenario["quan"] = {"random_customers": False, "customers": [
            {"id": f"C{i + 1}", "table_id": tables[i]["id"],
             "dish_id": "ca_loc_nuong_trui", "order_tick": 0, "reserved": ["I1"]}
            for i in range(2)]}
        # First prove that a valid Day handoff works with the same payload shape.
        valid = json.loads(json.dumps(scenario))
        valid["quan"]["customers"].pop()
        self.ok("day", valid, [{"tick": 0, "interact": True}])
        target = self.root / "out.jsonl"
        target.write_bytes(b"existing-day\n")
        code, err = self.run_cli("day", scenario, [{"tick": 0, "interact": True}])
        self.assertEqual(code, 2, err)
        self.assertTrue(err)
        self.assertEqual(target.read_bytes(), b"existing-day\n")

    def test_decimal_just_above_threshold_not_rounded_to_spoiled(self):
        # A finite decimal just above 30 + 1/120 remains fresh after one step.
        rows = self.ok("gather", self.gather([item(fresh=30.008333333334)]))
        self.assertEqual(events(rows, "spoiled"), [])
        self.assertGreater(snapshots(rows)[-1]["hold"][0]["fresh"], 30)

    def test_standalone_outputs_deterministic(self):
        for mode in ("gather", "quan"):
            with self.subTest(mode=mode):
                scenario = self.gather([item(fresh=30)]) if mode == "gather" else {
                    "quan": {"stock": [item(fresh=30)], "random_customers": False}}
                for out in ("first.jsonl", "second.jsonl"):
                    self.ok(mode, scenario, ticks=3, out=out)
                self.assertEqual((self.root / "first.jsonl").read_bytes(),
                                 (self.root / "second.jsonl").read_bytes())

    def test_published_manifest_announces_same_reservations_in_gather_and_quan(self):
        contract = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["contract_version"], "1.2")
        self.assertEqual(set(contract["extensions"]), {"flood_current", "reservations"})
        self.save("game.contract.json", contract)
        rows = self.ok("day", self.gather(random_current=False), [{"tick": 0, "interact": True}])
        initial = [event for event in events(rows) if event["tick"] == 0]
        self.assertEqual([event["name"] for event in initial],
                         ["day_start", "day_plan", "phase_start",
                          "reservation_announced", "reservation_announced"])
        gather, quan = snapshots(rows)
        orders = gather["reservations"]
        self.assertEqual([row["id"] for row in orders], ["R1", "R2"])
        self.assertEqual(len({row["table_id"] for row in orders}), 2)
        self.assertTrue(all(1800 <= row["arrival_tick"] <= 10799 for row in orders))
        self.assertTrue(all(row["dish_id"] in gather["day_plan"]["dishes"] for row in orders))
        self.assertEqual([{k: v for k, v in r.items() if k != "state"} for r in orders],
                         [{k: v for k, v in r.items() if k != "state"} for r in quan["reservations"]])

    def test_reservations_fixture_can_disable_random_and_rejects_shared_table(self):
        self.contract["reservations"] = {"count": 2, "table_hold_s": 30, "price_multiplier": 1.5,
                                         "failed_reputation_delta": -1}
        self.save("game.contract.json", self.contract)
        table = self.contract["tuning"]["quan"]["tables"][0]["id"]
        dish = next(iter(self.contract["tuning"]["menu"]))
        row = {"id": "R1", "table_id": table, "dish_id": dish, "arrival_tick": 1800}
        rows = self.ok("quan", {"quan": {"random_reservations": False, "reservations": [row]}}, ticks=0)
        self.assertEqual([event["data"]["id"] for event in events(rows, "reservation_announced")], ["R1"])
        self.assertEqual(snapshots(rows)[0]["reservations"][0]["state"], "holding")
        code, err = self.run_cli("quan", {"quan": {"reservations": [row, dict(row, id="R2")]}}, ticks=0)
        self.assertEqual(code, 2, err)


if __name__ == "__main__":
    unittest.main()
