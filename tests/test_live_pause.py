"""Pause ở cửa sổ chơi (chonoi.live): {"pause": true} làm sim ngừng bước tick, false chạy tiếp, restart bỏ pause."""

import json
import time
import unittest

from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer
from test_live import _get, _post


class LivePauseTest(unittest.TestCase):
    def test_pause_freezes_ticks_and_restart_clears_it(self):
        tuning = load_contract()["tuning"]
        server = LiveServer(LiveGame("gather", tuning, {}, 1), port=0)
        server.start()
        try:
            base = f"http://127.0.0.1:{server.port}"
            state = lambda: json.loads(_get(base + "/state")[1])
            self.assertFalse(state()["paused"])
            self.assertEqual(_post(base + "/input", {"pause": "yes"}), 400)
            self.assertEqual(_post(base + "/input", {"pause": True}), 200)
            time.sleep(0.05)
            t1 = state()["tick"]
            time.sleep(0.3)
            st = state()
            self.assertTrue(st["paused"])
            self.assertEqual(st["tick"], t1, "đang pause thì tick phải đứng yên")
            self.assertEqual(_post(base + "/input", {"pause": False}), 200)
            time.sleep(0.3)
            self.assertGreater(state()["tick"], t1, "bỏ pause thì sim chạy tiếp")
            _post(base + "/input", {"pause": True})
            self.assertEqual(_post(base + "/restart", {}), 200)
            self.assertFalse(state()["paused"], "restart phải bỏ pause")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
