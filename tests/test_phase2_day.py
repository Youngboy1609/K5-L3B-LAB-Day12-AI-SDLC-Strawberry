"""AC-P2-02: smoke chuyển pha theo docs/plan/phase-2-tasks.md."""
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.headless import main

from helpers import ROOT, Workdir, events, read_jsonl, run_headless, snapshots

FIXTURES = Path(ROOT) / "docs/proof/phase-2/fixtures"


def run_day_smoke(*args):
    contract = load_contract()
    if contract["contract_version"] == "1.1":
        return run_headless(*args)
    # Dữ liệu chỉ để kiểm luồng khi manifest dự án vẫn là v1.0.
    # Chạy parser và runtime thật. Khi có preset chuẩn, CLI dùng preset trực tiếp.
    contract["contract_version"] = "1.1"
    contract["tuning"]["day"] = {
        "day_plans": {"1": {"dishes": {"ca_loc_nuong_trui": 1}}},
        "shop_ticks": 600,
        "upgrades": {},
    }
    errors = StringIO()
    with patch("chonoi.headless.load_contract", return_value=contract), redirect_stderr(errors):
        code = main(args)
    return code, errors.getvalue()


class DaySmoke(unittest.TestCase):
    def test_three_tick_day_handoff(self):
        with Workdir() as w:
            out = w.path("day.jsonl")
            code, err = run_day_smoke(
                "--mode", "day", "--seed", "42", "--days", "1",
                "--scenario", str(FIXTURES / "p2-day-smoke.json"),
                "--inputs", str(FIXTURES / "p2-day-inputs.json"),
                "--ticks", "3", "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            initial = [e for e in events(rows) if e["tick"] == 0]
            self.assertEqual([e["name"] for e in initial],
                             ["day_start", "day_plan", "phase_start"])
            self.assertEqual(initial[-1]["phase"], "gather")
            ss = {s["tick"]: s for s in snapshots(rows)}
            for tick, phase in ((0, "gather"), (1, "quan"), (2, "shop")):
                self.assertEqual(ss[tick]["phase"], phase)
                self.assertEqual(ss[tick]["phase_tick"], 0)
            for name, tick, phase in (("gather_end", 1, "gather"),
                                      ("quan_end", 2, "quan")):
                ended = events(rows, name)
                self.assertEqual(len(ended), 1)
                self.assertEqual((ended[0]["tick"], ended[0]["phase"]), (tick, phase))
            self.assertEqual(sum(r["type"] == "end" for r in rows), 1)
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["ticks"], 3)
            self.assertEqual(rows[-1]["days_completed"], 1)
            self.assertEqual(rows[-1]["reason"], "days_complete")


if __name__ == "__main__":
    unittest.main()
