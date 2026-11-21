import unittest
from pathlib import Path

from helpers import Workdir, events, read_jsonl, run_headless, write_json


class QuanCustomerScheduling(unittest.TestCase):
    def test_no_dish_event_occurs_at_first_phase_schedule(self):
        """Kho rỗng phát no_dish ở tick hẹn đầu tiên."""
        with Workdir() as w:
            out = w.path("quan.jsonl")
            scenario = write_json(w.path("scenario.json"), {
                "quan": {"stock": {}, "random_customers": True}
            })
            code, err = run_headless(
                "--mode", "quan", "--seed", "4", "--scenario", scenario,
                "--ticks", "120", "--snapshot-every", "120", "--out", out,
            )
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            no_dish = events(rows, "no_dish")
            self.assertEqual([event["tick"] for event in no_dish], [120])

    def test_random_customers_false_keeps_fixture_only(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {"stock": {}, "random_customers": False}
            })
            out = w.path("quan.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "4", "--scenario", scenario,
                                     "--ticks", "120", "--snapshot-every", "120", "--out", out)
            self.assertEqual(code, 0, err)
            self.assertEqual(events(read_jsonl(out)), [])

    def test_fixture_reserved_defaults_and_patience_starts_on_next_tick(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {
                    "stock": {"ca_loc": 1}, "random_customers": False,
                    "customers": [{"id": "C4", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "patience_ticks_left": 2}],
                }
            })
            out = w.path("quan.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "4", "--scenario", scenario,
                                     "--ticks", "1", "--snapshot-every", "1", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            initial, after_tick = [r for r in rows if r["type"] == "snapshot"]
            self.assertEqual(initial["customers"][0]["reserved"], {"ca_loc": 1})
            self.assertEqual(initial["stock"], {"ca_loc": 1})
            self.assertEqual(after_tick["customers"][0]["patience_ticks_left"], 1)

    def test_fixture_reservations_cannot_exceed_physical_stock(self):
        with Workdir() as w:
            scenario = write_json(w.path("scenario.json"), {
                "quan": {
                    "stock": {"bong_sung": 1}, "random_customers": False,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}],
                }
            })
            out = w.path("quan.jsonl")
            code, _ = run_headless("--mode", "quan", "--seed", "4", "--scenario", scenario,
                                   "--ticks", "0", "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(Path(out).exists())

    def test_payload_price_must_be_an_integer(self):
        with Workdir() as w:
            dish_id = "ca_loc_nuong_trui"
            scenario = write_json(w.path("scenario.json"), {"quan": {
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish_id,
                               "order_status": "assigned"}],
                "hand": {"order_id": "C1", "dish_id": dish_id, "base_price": 60.0},
            }})
            out = w.path("quan.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "4", "--scenario", scenario,
                                     "--ticks", "0", "--out", out)
            self.assertEqual(code, 2, err)
            self.assertFalse(Path(out).exists())


if __name__ == "__main__":
    unittest.main()
