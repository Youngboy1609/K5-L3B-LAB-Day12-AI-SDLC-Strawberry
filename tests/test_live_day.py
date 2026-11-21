"""Cửa sổ chơi mode day (chonoi.live): chuyển pha gather → quan → shop, mua lỗi, shop_done kết thúc ngày, pause.

Manifest dự án còn v1.0 nên test tự thêm tuning.day tối thiểu (giống tests/test_phase2_day.py), chỉ để kiểm luồng.
"""

from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from io import StringIO
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer, main
from helpers import ROOT, Workdir, write_json
from test_live import _get, _post

FIXTURE = json.loads((Path(ROOT) / "docs/proof/phase-2/fixtures/p2-day-smoke.json").read_text(encoding="utf-8"))


def _tuning():
    tuning = load_contract()["tuning"]
    tuning.setdefault("day", {"day_plans": {"1": {"dishes": {"ca_loc_nuong_trui": 1}}},
                              "shop_ticks": 600, "upgrades": {}})
    return tuning


class LiveDayTest(unittest.TestCase):
    def _wait(self, base, pred, secs=3):
        deadline = time.time() + secs
        while time.time() < deadline:
            st = json.loads(_get(base + "/state")[1])
            if pred(st):
                return st
            time.sleep(0.02)
        self.fail("hết giờ chờ trạng thái mong đợi, cuối cùng: " + json.dumps({k: st.get(k) for k in ("phase", "finished", "reason", "paused")}))

    def test_day_flow_buy_and_shop_done(self):
        server = LiveServer(LiveGame("day", _tuning(), FIXTURE, 42, days=1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            self.assertEqual(_post(base + "/input", {"pause": True}), 200)
            st = json.loads(_get(base + "/state")[1])
            self.assertEqual((st["mode"], st["phase"], st["day"]), ("day", "gather", 1))
            self.assertIn("day_meta", st)
            self.assertEqual([e["name"] for e in st["events"]][:3], ["day_start", "day_plan", "phase_start"])
            _post(base + "/input", {"interact": True})      # cập bến ngay: hết buổi sáng
            _post(base + "/input", {"pause": False})
            _post(base + "/input", {"interact": False})
            st = self._wait(base, lambda s: s["phase"] == "shop")
            self.assertIn("quan_end", [e["name"] for e in st["events"]])
            self.assertEqual(_post(base + "/input", {"buy": 3}), 400)
            self.assertEqual(_post(base + "/input", {"buy": "khong_co"}), 200)
            st = self._wait(base, lambda s: any(e["name"] == "buy_failed" for e in s["events"]))
            failed = [e for e in st["events"] if e["name"] == "buy_failed"][-1]
            self.assertEqual(failed["data"], {"buy": "khong_co", "reason": "unsupported"})
            _post(base + "/input", {"shop_done": True})
            _post(base + "/input", {"shop_done": False})
            st = self._wait(base, lambda s: s["finished"])
            self.assertEqual(st["reason"], "days_complete")
            self.assertEqual(st["days_completed"], 1)
        finally:
            server.stop()


    def test_evening_snapshot_lists_only_planned_dishes_supported_by_unreserved_stock(self):
        tuning = _tuning()
        dishes = {"goi_bong_sung": 1, "ca_loc_nuong_trui": 1, "lau_ca_linh_dien_dien": 1}
        tuning["day"]["day_plans"]["1"] = {"dishes": dishes}
        scenario = {
            "gather": {"player": {"pos": tuning["gather"]["dock_pos"]},
                       "hold": ["bong_sung", "bong_sung", "ca_loc"], "random_fish": False},
            "quan": {"customers": [{"id": "C1", "table_id": tuning["quan"]["tables"][0]["id"],
                                    "dish_id": "goi_bong_sung"}]},
        }
        game = LiveGame("day", tuning, scenario, 42)
        game.set_input({"interact": True})
        game._tick_once()
        state = json.loads(game.state_json())
        self.assertEqual(state["phase"], "quan")
        self.assertEqual(state["stock"], {"bong_sung": 2, "ca_loc": 1})
        self.assertEqual(state["cookable_dishes"], ["ca_loc_nuong_trui"])

    def test_live_quan_inventory_uses_contract_version(self):
        stock = {"ca_keo": 1, "keo_neo": 2}
        contract = load_contract()
        contract["contract_version"] = "1.0"
        with Workdir() as w:
            inventory = write_json(w.path("kho.json"), {"items": stock})
            args = ["--mode", "quan", "--inventory", inventory, "--port", "0"]
            with patch("chonoi.live.load_contract", return_value=contract), patch("chonoi.live.LiveServer") as server:
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch("chonoi.live.time.sleep", side_effect=KeyboardInterrupt):
                    self.assertEqual(main(args), 2)
                    server.assert_not_called()
                    contract["contract_version"] = "1.1"
                    self.assertEqual(main(args), 0)
                    game = server.call_args.args[0]
                    self.assertEqual(json.loads(game.state_json())["stock"], stock)


    def test_day_report_keeps_reputation_delta_and_dishes_after_shop(self):
        tuning = _tuning()
        table = tuning["quan"]["tables"][0]
        dish = {"order_id": "C1", "dish_id": "goi_bong_sung",
                "base_price": tuning["menu"]["goi_bong_sung"]["price"]}
        scenario = {
            "gather": {"player": {"pos": tuning["gather"]["dock_pos"]}},
            "quan": {"player": {"pos": table["pos"]}, "time_left_ticks": 2, "hand": dish,
                     "customers": [{"id": "C1", "table_id": table["id"],
                                    "dish_id": dish["dish_id"], "order_status": "assigned"}]},
        }
        game = LiveGame("day", tuning, scenario, 42)
        game.set_input({"interact": True})
        game._tick_once()
        game.set_input({"interact": False})
        game._tick_once()
        game.set_input({"interact": True})
        game._tick_once()
        state = json.loads(game.state_json())
        self.assertEqual(state["phase"], "shop")
        self.assertAlmostEqual(state["shift_reputation_delta"], tuning["quan"]["tip_reputation"])
        self.assertEqual(state["served_dishes"], {dish["dish_id"]: 1})

        game.set_input({"shop_done": True})
        game._tick_once()
        state = json.loads(game.state_json())
        self.assertTrue(state["finished"])
        self.assertEqual(state["served_dishes"], {dish["dish_id"]: 1})
        game.restart()
        self.assertEqual(json.loads(game.state_json())["served_dishes"], {})


class LiveFreshnessSnapshotTest(unittest.TestCase):
    """Phase 3: Day dùng đúng schema và HUD giữ đúng nhánh ở ngưỡng ươn."""

    def test_day_v12_keeps_spoil_boundary_in_browser_snapshot(self):
        tuning = _tuning()
        tuning["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                               "quan_decay_per_s": 0.25, "spoiled_below": 30}
        hold = [{"id": "I1", "kind": "ca_linh", "fresh": Fraction("29.99999999999999999")},
                {"id": "I2", "kind": "ca_linh", "fresh": 30}]
        game = LiveGame("day", tuning, {"gather": {"hold": hold}}, 42,
                        contract_version="1.2", freshness=tuning["freshness"])
        snapshot = json.loads(game.state_json())
        self.assertEqual(game.session.sim.contract_version, "1.2")
        self.assertLess(snapshot["hold"][0]["fresh"], 30)
        self.assertEqual(snapshot["hold"][1]["fresh"], 30)

    def test_snapshot_reports_schema_and_threshold(self):
        tuning = load_contract()["tuning"]
        freshness = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
        game = LiveGame("gather", tuning, {}, 1, contract_version="1.1", freshness=freshness)
        snap = json.loads(game.state_json())
        self.assertEqual(snap["contract_version"], "1.1")
        self.assertEqual(snap["freshness"]["spoiled_below"], 30)
        self.assertNotIn("freshness", json.loads(LiveGame("gather", tuning, {}, 1).state_json()))

    def test_fraction_fresh_is_exported_for_display_only(self):
        from chonoi.live import _json_default
        out = json.loads(json.dumps({"hold": [{"id": "I1", "kind": "ca_linh", "fresh": Fraction(11999, 120)},
                                              {"id": "I2", "kind": "ca_linh", "fresh": Fraction(6001, 200)},
                                              {"id": "I3", "kind": "ca_linh", "fresh": Fraction(0)}]},
                                    default=_json_default))
        self.assertEqual([i["fresh"] for i in out["hold"]], [float(Fraction(11999, 120)), 30.005, 0.0])
        with self.assertRaises(TypeError):
            json.dumps({"x": object()}, default=_json_default)


if __name__ == "__main__":
    unittest.main()
