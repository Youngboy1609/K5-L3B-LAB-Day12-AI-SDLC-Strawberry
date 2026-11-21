"""Cửa sổ chơi mode day (chonoi.live): chuyển pha gather → quan → shop, mua lỗi, shop_done kết thúc ngày, pause.

Manifest dự án còn v1.0 nên test tự thêm tuning.day tối thiểu (giống tests/test_phase2_day.py), chỉ để kiểm luồng.
"""

import json
import time
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from helpers import ROOT
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


if __name__ == "__main__":
    unittest.main()
