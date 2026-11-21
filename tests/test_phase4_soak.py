"""Soak v1.3 reuses the v1.2 Day simulation and its persistent state."""

from contextlib import redirect_stderr
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.runner import DaySession


def soak_contract():
    contract = load_contract()
    contract["contract_version"] = "1.3"
    contract["tuning"].setdefault("freshness", {"initial": 100, "gather_decay_per_s": 0.5,
                                               "quan_decay_per_s": 0.25, "spoiled_below": 30})
    return contract


class SoakTest(unittest.TestCase):
    def test_session_repeats_plans_and_keeps_day_state(self):
        tuning = soak_contract()["tuning"]
        scenario = {
            "day": {"money": 200, "earned": 300, "reputation": 4, "upgrades": {"oxygen": 1}},
            "gather": {"hold": [{"id": "I7", "kind": "ca_loc", "fresh": 100}],
                       "random_fish": False, "monsters": []},
            "quan": {"time_left_ticks": 1, "random_customers": False, "random_reservations": False},
        }
        session = DaySession(tuning, scenario, 7, 10, contract_version="1.2", repeat_day_plans=True)
        plans, closed = [], []
        for day in range(1, 11):
            opening = session.snapshot()
            self.assertEqual((opening["day"], opening["phase"]), (day, "gather"))
            self.assertEqual(opening["active_upgrades"], {"oxygen": 1, **({"hp": 1} if day > 5 else {})})
            plans.append(opening["day_plan"])
            session.step(InputState((0, 0), {}, {"interact"}))
            quan = session.snapshot()
            self.assertEqual(quan["phase"], "quan")
            self.assertEqual(quan["stock"][0]["id"], f"I{day + 6}")
            session.step(InputState((0, 0), {}, set()))
            self.assertEqual(session.snapshot()["phase"], "shop")
            actions = {"buy": "hp"} if day == 5 else {}
            rows = session.step(InputState((0, 0), {}, {"shop_done"}, actions))
            closed.extend(row["day"] for row in rows if row["name"] == "shop_end")
        self.assertEqual(plans[:5], plans[5:])
        self.assertEqual(closed, list(range(1, 11)))
        ending = session.end_row()
        self.assertEqual((ending["money"], ending["earned"], ending["reputation"], ending["score"]),
                         (80, 300, 4, 700))
        self.assertEqual(ending["reason"], "days_complete")

    def test_ten_day_report_repeats_gameplay(self):
        from chonoi.soak import main

        with tempfile.TemporaryDirectory() as folder, patch("chonoi.soak.load_contract", side_effect=soak_contract):
            path = Path(folder) / "soak.json"
            args = ["--seed", "7", "--days", "10", "--out", str(path)]
            self.assertEqual(main(args), 0)
            first = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(main(args), 0)
            second = json.loads(path.read_text(encoding="utf-8"))
            bad_args = ["--seed", "7", "--days", "0", "--out", str(path)]
            with redirect_stderr(StringIO()):
                self.assertEqual(main(bad_args), 2)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), second)

        self.assertEqual(set(first), {"days", "days_completed", "crashes", "results", "duration_s"})
        for report in (first, second):
            self.assertGreater(report.pop("duration_s"), 0)
        self.assertEqual(first, second)
        self.assertEqual((first["days"], first["days_completed"], first["crashes"]), (10, 10, 0))
        self.assertEqual([row["day"] for row in first["results"]], list(range(1, 11)))
        self.assertTrue(all(set(row) == {"day", "earned", "reputation", "score"} for row in first["results"]))
