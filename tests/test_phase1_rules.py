"""AC-P1-01/02: kiểm luật gather qua headless, không phụ thuộc lớp Python.

Các ca này là tiêu chí bàn giao; thất bại khi gameplay còn TODO là lỗi thật,
không đánh dấu skip/expectedFailure. Chưa kiểm payload event đang chờ P1-01.
"""

import json
import math
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

    def test_caught_school_cannot_be_caught_again_after_cooldown(self):
        cooldown = round(self.g["catch_cooldown_s"] * self.hz)
        rows, _ = self.run_case({
            "fish": [{"id": "F1", "kind": "ca_linh", "pos": [50, 5]}],
        }, ticks=cooldown + 1, inputs=(
            {"tick": 0, "catch": True}, {"tick": 1, "catch": False},
            {"tick": cooldown, "catch": True},
        ))
        self.assertEqual([e["tick"] for e in events(rows, "fish_caught")], [1])
        self.assertEqual(snapshots(rows)[1]["fish"], [])
        self.assertEqual(snapshots(rows)[-1]["hold"], ["ca_linh"] * self.g["fish_yield"]["ca_linh"])

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


class QuanRules(unittest.TestCase):
    """AC-P1-01/02: sinh khách thật để tránh tự đặt schema đơn hàng chưa chốt."""

    @classmethod
    def setUpClass(cls):
        with open("game.contract.json", encoding="utf-8") as f:
            cls.tuning = json.load(f)["tuning"]
        cls.q = cls.tuning["quan"]
        cls.hz = cls.tuning["tick_hz"]
        cls.dish_id = "ca_loc_nuong_trui"
        cls.dish = cls.tuning["menu"][cls.dish_id]
        cls.stock = dict(cls.dish["recipe"])
        cls.arrival = cls.q["first_customer_tick"]
        cls.cook_ticks = round(cls.dish["cook_s"] * cls.hz)

    def run_case(self, ticks, inputs=(), overrides=None):
        with Workdir() as w:
            block = {"stock": self.stock, "random_customers": True,
                     "player": {"pos": self.q["stoves"][0]["pos"]}}
            block.update(overrides or {})
            out = w.path("out.jsonl")
            code, err = run_headless(
                "--mode", "quan", "--seed", "7", "--ticks", str(ticks),
                "--scenario", write_json(w.path("scenario.json"), {"quan": block}),
                "--inputs", write_json(w.path("inputs.json"), frames(*inputs)),
                "--snapshot-every", "1", "--out", out,
            )
            self.assertEqual(code, 0, err)
            with open(out, "rb") as f:
                raw = f.read()
            return read_jsonl(out), raw

    def test_first_customer_arrives_on_schedule_without_consuming_stock(self):
        rows, _ = self.run_case(self.arrival)
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(by_tick[self.arrival - 1]["customers"], [])
        customers = by_tick[self.arrival]["customers"]
        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0]["dish_id"], self.dish_id)
        self.assertEqual(customers[0]["reserved"], self.stock)
        self.assertEqual(by_tick[self.arrival]["stock"], self.stock)

    def test_empty_stock_emits_no_dish_only_at_arrival(self):
        rows, _ = self.run_case(self.arrival + 1, overrides={"stock": {}})
        self.assertEqual(snapshots(rows)[-1]["customers"], [])
        self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [self.arrival])

    def test_random_customers_false_disables_arrivals(self):
        rows, _ = self.run_case(self.arrival + 1, overrides={"random_customers": False})
        self.assertTrue(all(not s["customers"] for s in snapshots(rows)))
        self.assertEqual(events(rows, "no_dish"), [])

    def test_cooking_consumes_reserved_stock_once_when_button_is_held(self):
        rows, _ = self.run_case(self.arrival + 3,
                                inputs=({"tick": self.arrival, "interact": True},))
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(by_tick[self.arrival]["stock"], self.stock)
        final = by_tick[self.arrival + 3]
        self.assertEqual(final["stock"], {})
        self.assertEqual(final["stoves"][0]["state"], "cooking")
        self.assertEqual(final["customers"][0]["reserved"], {})
        self.assertEqual([e["tick"] for e in events(rows, "cook_started")], [self.arrival + 1])

    def test_dish_becomes_ready_after_configured_cook_duration(self):
        ready_tick = self.arrival + 1 + self.cook_ticks
        rows, _ = self.run_case(ready_tick,
                                inputs=({"tick": self.arrival, "interact": True},))
        by_tick = {s["tick"]: s for s in snapshots(rows)}
        self.assertEqual(by_tick[ready_tick - 1]["stoves"][0]["state"], "cooking")
        self.assertEqual(by_tick[ready_tick]["stoves"][0]["state"], "ready")
        self.assertEqual([e["tick"] for e in events(rows, "dish_ready")], [ready_tick])

    def pickup_inputs(self):
        ready_tick = self.arrival + 1 + self.cook_ticks
        return ready_tick, [
            {"tick": self.arrival, "interact": True},
            {"tick": self.arrival + 1, "interact": False},
            {"tick": ready_tick, "interact": True},
        ]

    def test_ready_dish_moves_to_empty_hand(self):
        ready_tick, inputs = self.pickup_inputs()
        rows, _ = self.run_case(ready_tick + 1, inputs=inputs)
        final = snapshots(rows)[-1]
        self.assertIsNotNone(final["hand"])
        self.assertEqual(final["hand"]["dish_id"], self.dish_id)
        self.assertEqual(final["stoves"][0]["state"], "idle")
        self.assertIsNone(final["stoves"][0]["dish"])
        self.assertEqual(final["stock"], {})
        self.assertEqual(len(events(rows, "dish_picked")), 1)

    def test_waiting_customer_leaves_and_releases_reservation_without_consumption(self):
        deadline = self.arrival + round(self.q["patience_s"] * self.hz)
        rows, _ = self.run_case(deadline)
        final = snapshots(rows)[-1]
        first = next(s for s in snapshots(rows) if s["tick"] == self.arrival)["customers"]
        self.assertEqual(len(first), 1)
        self.assertNotIn(first[0]["id"], [c["id"] for c in final["customers"]])
        # Lịch sinh khách có thể trùng tick khách cũ rời bàn. Khách mới được
        # phép giữ lại nguyên liệu vừa giải phóng, nhưng không trừ tồn vật lý.
        self.assertEqual(final["stock"], self.stock)
        expected = max(self.q["reputation_min"],
                       self.q["reputation_initial"] + self.q["left_reputation_delta"])
        self.assertAlmostEqual(final["reputation"], expected)
        self.assertEqual(final["earned"], 0)
        self.assertEqual([e["tick"] for e in events(rows, "customer_left")], [deadline])

    def test_served_customer_finishes_meal_and_pays(self):
        ready_tick, inputs = self.pickup_inputs()
        tick = ready_tick + 1
        # Đi từng trục từ bếp tới bàn. Tăng và giảm tốc đối xứng nên quãng
        # đường tổng bằng số tick giữ hướng * speed / hz, sai số < 1 tick.
        stove, table = self.q["stoves"][0]["pos"], self.q["tables"][0]["pos"]
        for axis in (0, 1):
            delta = table[axis] - stove[axis]
            if not delta:
                continue
            move = [0, 0]
            move[axis] = 1 if delta > 0 else -1
            inputs.append({"tick": tick, "move": move, "interact": False})
            tick += round(abs(delta) * self.hz / self.q["walk_speed"])
            inputs.append({"tick": tick, "move": [0, 0]})
            tick += self.q["ramp_max_ticks"]
        inputs.append({"tick": tick, "interact": True})
        paid_tick = tick + 1 + round(self.q["eat_s"] * self.hz)
        rows, _ = self.run_case(paid_tick, inputs=inputs)
        self.assertEqual(len(events(rows, "served")), 1)
        self.assertEqual([e["tick"] for e in events(rows, "paid")], [paid_tick])
        final = snapshots(rows)[-1]
        self.assertIsNone(final["hand"])
        self.assertEqual(final["customers"], [])
        # Chốt boa theo kiên nhẫn còn lại SAU khi giảm tick giao món.
        patience = round(self.q["patience_s"] * self.hz)
        remaining = patience - (tick + 1 - self.arrival)
        tipped = remaining / patience >= self.q["tip_min_patience_ratio"]
        price = self.dish["price"]
        expected = price + (math.floor(price * self.q["tip_rate"]) if tipped else 0)
        self.assertAlmostEqual(final["money"], expected)
        self.assertAlmostEqual(final["earned"], expected)
        reputation = self.q["reputation_initial"] + (self.q["tip_reputation"] if tipped else 0)
        self.assertAlmostEqual(final["reputation"], min(self.q["reputation_max"], reputation))

    def test_same_seed_and_cooking_inputs_produce_identical_bytes(self):
        ready_tick, inputs = self.pickup_inputs()
        first, raw_first = self.run_case(ready_tick + 1, inputs=inputs)
        second, raw_second = self.run_case(ready_tick + 1, inputs=inputs)
        self.assertEqual(raw_first, raw_second)
        # Không cho một lượt chạy chưa có gameplay được tính là bằng chứng
        # tất định của vòng nấu/bưng.
        self.assertEqual(len(events(first, "dish_picked")), 1)
        self.assertEqual(len(events(second, "dish_picked")), 1)


if __name__ == "__main__":
    unittest.main()
