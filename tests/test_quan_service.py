"""Kiểm bếp, phục vụ và đóng ca qua QuanSim.step() với preset Phase 1."""

import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim import quan_service as qs
from chonoi.sim.quan import QuanSim

TUNING = load_contract(os.path.join(os.path.dirname(__file__), "..", "game.contract.json"))["tuning"]
Q = TUNING["quan"]
STOVE = Q["stoves"][0]
TABLE = Q["tables"][0]
EAT = int(round(Q["eat_s"] * 60))


def make_sim(stock=None, customers=None, time_left=None, pos=None, tuning=TUNING):
    sc = {"stock": stock if stock is not None else {"bong_sung": 2, "ca_loc": 1},
          "customers": customers or [], "random_customers": False}
    if time_left is not None:
        sc["time_left_ticks"] = time_left
    if pos is not None:
        sc["player"] = {"pos": list(pos)}
    return QuanSim(tuning, sc, Streams(1), IdAllocator())


def customer(cid="C1", dish="goi_bong_sung", **kw):
    recipe = TUNING["menu"][dish]["recipe"]
    return dict({"id": cid, "table_id": TABLE["id"], "dish_id": dish, "order_tick": 0, "reserved": dict(recipe)}, **kw)


def tick(sim, interact=False):
    """Dùng đúng vòng tick chung của live và headless."""
    edges = {"interact"} if interact else set()
    ev = sim.step(InputState((0.0, 0.0), {}, edges))
    return [n for n, _ in ev], ev


def at(sim, obj):
    sim.pos = list(obj["pos"])


def cook_and_pick(sim):
    at(sim, STOVE)
    tick(sim, interact=True)
    for _ in range(sim.stoves[0]["cook_ticks_left"]):
        tick(sim)
    tick(sim, interact=True)
    assert sim.hand is not None


class Stove(unittest.TestCase):
    def test_stock_only_deducted_at_cook_start(self):
        sim = make_sim(customers=[customer()])
        self.assertEqual(sim.stock["bong_sung"], 2)
        at(sim, STOVE)
        names, ev = tick(sim, interact=True)
        self.assertEqual(names, ["cook_started"])
        self.assertNotIn("bong_sung", sim.stock)
        self.assertEqual(sim.stock["ca_loc"], 1)
        c = sim.customers[0]
        self.assertEqual((c["order_status"], c["reserved"]), ("assigned", {}))
        d = sim.stoves[0]["dish"]
        self.assertEqual(d, {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40})
        # bấm lại khi đang nấu: không trừ thêm
        tick(sim, interact=True)
        self.assertNotIn("bong_sung", sim.stock)

    def test_zero_quantity_in_fixture_reservation_does_not_touch_missing_stock(self):
        sim = make_sim(stock={"bong_sung": 2},
                       customers=[customer(reserved={"bong_sung": 2, "ca_loc": 0})])
        at(sim, STOVE)
        names, _ = tick(sim, interact=True)
        self.assertEqual(names, ["cook_started"])
        self.assertEqual(sim.stock, {})

    def test_cook_timer_ready_and_ready_ticks(self):
        sim = make_sim(customers=[customer()])
        at(sim, STOVE)
        tick(sim, interact=True)
        cook = int(round(TUNING["menu"]["goi_bong_sung"]["cook_s"] * 60))
        self.assertEqual(sim.stoves[0]["cook_ticks_left"], cook)
        for _ in range(cook - 1):
            self.assertEqual(tick(sim)[0], [])
        names, _ = tick(sim)
        self.assertEqual(names, ["dish_ready"])
        self.assertEqual((sim.stoves[0]["state"], sim.stoves[0]["ready_ticks"]), ("ready", 0))
        tick(sim)
        self.assertEqual(sim.stoves[0]["ready_ticks"], 1)

    def test_oldest_reserved_order_cooked_first(self):
        sim = make_sim(stock={"bong_sung": 2, "ca_loc": 1},
                       customers=[customer("C1", "goi_bong_sung", order_tick=50),
                                  dict(customer("C2", "ca_loc_nuong_trui", order_tick=10), table_id="T9")],
                       tuning={**TUNING, "quan": {**Q, "tables": [TABLE, {"id": "T9", "pos": [15, 9]}]}})
        at(sim, STOVE)
        _, ev = tick(sim, interact=True)
        self.assertEqual(ev[0][1]["order_id"], "C2")

    def test_pick_moves_dish_to_hand(self):
        sim = make_sim(customers=[customer()])
        cook_and_pick(sim)
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertEqual(sim.hand["order_id"], "C1")

    def test_pick_with_full_hand_does_nothing(self):
        sim = make_sim(customers=[customer()])
        at(sim, STOVE)
        tick(sim, interact=True)
        for _ in range(sim.stoves[0]["cook_ticks_left"]):
            tick(sim)
        other = {"order_id": "X9", "dish_id": "goi_bong_sung", "base_price": 40}
        sim.hand = dict(other)
        self.assertEqual(tick(sim, interact=True)[0], [])
        self.assertEqual((sim.hand, sim.stoves[0]["state"]), (other, "ready"))

    def test_two_stoves_tie_broken_by_id(self):
        sim = make_sim(customers=[customer()])
        sim.stoves = [dict(sim.stoves[0], id="B2", pos=[3, 8]), dict(sim.stoves[0], id="B10", pos=[1, 8])]
        sim.pos = [2, 8]
        self.assertEqual(qs._pick_target(sim)[1]["id"], "B2")


class Target(unittest.TestCase):
    def test_stove_wins_tie_and_edge_counts(self):
        sim = make_sim(customers=[customer()])
        sim.tables[0]["pos"] = [STOVE["pos"][0] + 2 * Q["interact_radius"], STOVE["pos"][1]]
        sim.pos = [STOVE["pos"][0] + Q["interact_radius"], STOVE["pos"][1]]  # đúng mép cả hai
        self.assertEqual(qs._pick_target(sim)[0], "stove")

    def test_out_of_radius_does_nothing(self):
        sim = make_sim(customers=[customer()])
        sim.pos = [STOVE["pos"][0] + Q["interact_radius"] + 0.01, STOVE["pos"][1]]
        self.assertEqual(tick(sim, interact=True)[0], [])


class Serve(unittest.TestCase):
    def test_wrong_order_rejected(self):
        sim = make_sim(customers=[customer()])
        sim.hand = {"order_id": "X9", "dish_id": "goi_bong_sung", "base_price": 40}
        at(sim, TABLE)
        self.assertEqual(tick(sim, interact=True)[0], [])
        self.assertIsNotNone(sim.hand)

    def test_serve_on_tick_patience_hits_zero_no_tip(self):
        sim = make_sim(customers=[customer()])
        cook_and_pick(sim)
        sim.customers[0]["patience_ticks_left"] = 1
        at(sim, TABLE)
        names, ev = tick(sim, interact=True)
        self.assertEqual(names, ["served"])
        self.assertEqual(ev[0][1], {
            "order_id": sim.customers[0]["id"], "table_id": TABLE["id"], "dish_id": "goi_bong_sung",
            "patience_ticks_left": 0, "base_price": 40, "tip": 0,
        })
        self.assertEqual(sim.customers[0]["state"], "eating")
        self.assertIsNone(sim.hand)

    def test_eat_then_pay_with_tip_and_reputation(self):
        sim = make_sim(customers=[customer()])
        cook_and_pick(sim)
        at(sim, TABLE)
        _, ev = tick(sim, interact=True)
        tip = int(40 * Q["tip_rate"])
        self.assertEqual(ev[0][1]["tip"], tip)
        for _ in range(EAT - 1):
            self.assertEqual(tick(sim)[0], [])
        names, ev = tick(sim)
        self.assertEqual(names, ["paid"])
        self.assertEqual(ev[0][1], {
            "order_id": "C1", "table_id": TABLE["id"], "base_price": 40, "tip": tip,
            "amount": 40 + tip, "reason": "finished_eating",
        })
        self.assertEqual((sim.money, sim.earned, sim.shift_earned), (40 + tip,) * 3)
        self.assertAlmostEqual(sim.reputation, Q["reputation_initial"] + Q["tip_reputation"])
        self.assertEqual(sim.customers, [])

    def test_fractional_tip_is_floored(self):
        sim = make_sim(customers=[customer()], tuning={**TUNING, "quan": {**Q, "tip_rate": 0.29}})
        cook_and_pick(sim)
        at(sim, TABLE)
        _, events = tick(sim, interact=True)
        self.assertEqual(events[0][1]["tip"], 11)

    def test_reputation_clamped_at_max(self):
        sim = make_sim(customers=[customer()])
        sim.reputation = Q["reputation_max"]
        cook_and_pick(sim)
        at(sim, TABLE)
        tick(sim, interact=True)
        for _ in range(EAT):
            tick(sim)
        self.assertEqual(sim.reputation, Q["reputation_max"])


    def test_serving_keeps_price_from_cook_start(self):
        sim = make_sim(customers=[customer()])
        cook_and_pick(sim)
        self.assertEqual(sim.hand["base_price"], TUNING["menu"]["goi_bong_sung"]["price"])
        at(sim, TABLE)
        _, ev = tick(sim, interact=True)
        self.assertEqual(ev[0][1]["base_price"], TUNING["menu"]["goi_bong_sung"]["price"])

    def test_reputation_does_not_drift(self):
        sim = make_sim()
        for d in (-0.5, -0.5, -0.5, 0.2, 0.2, -0.5, 0.2, 0.2, 0.2):
            sim.reputation = qs._clamp_rep(sim, sim.reputation + d)
        self.assertEqual(sim.reputation, 2.0)


class Leave(unittest.TestCase):
    def test_waiting_customer_leaves_dish_discarded_no_refund(self):
        sim = make_sim(customers=[customer()])
        at(sim, STOVE)
        tick(sim, interact=True)
        sim.customers[0]["patience_ticks_left"] = 1
        names, _ = tick(sim)
        self.assertEqual(names, ["customer_left", "dish_discarded"])
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertNotIn("bong_sung", sim.stock, "không hoàn nguyên liệu đã nấu")
        self.assertAlmostEqual(sim.reputation, Q["reputation_initial"] + Q["left_reputation_delta"])

    def test_reserved_customer_leaves_stock_untouched(self):
        sim = make_sim(customers=[customer(patience_ticks_left=1)])
        names, _ = tick(sim)
        self.assertEqual(names, ["customer_left"])
        self.assertEqual(sim.stock, {"bong_sung": 2, "ca_loc": 1})

    def test_dish_in_hand_discarded_when_customer_leaves(self):
        sim = make_sim(customers=[customer()])
        cook_and_pick(sim)
        sim.customers[0]["patience_ticks_left"] = 1
        names, _ = tick(sim)
        self.assertEqual(names, ["customer_left", "dish_discarded"])
        self.assertIsNone(sim.hand)

    def test_reputation_clamped_at_min(self):
        sim = make_sim(customers=[customer(patience_ticks_left=1)])
        sim.reputation = Q["reputation_min"]
        tick(sim)
        self.assertEqual(sim.reputation, Q["reputation_min"])


class Close(unittest.TestCase):
    def test_close_with_eating_customer_pays_and_ends(self):
        sim = make_sim(customers=[customer()], time_left=10_000)
        cook_and_pick(sim)
        at(sim, TABLE)
        tick(sim, interact=True)
        sim.time_left_ticks = 1
        names, ev = tick(sim)
        self.assertEqual(names, ["paid", "quan_end"])
        self.assertEqual(ev[0][1]["reason"], "closing")
        self.assertTrue(sim.done)
        self.assertEqual(sim.customers, [])

    def test_serve_on_last_tick_then_close(self):
        sim = make_sim(customers=[customer()], time_left=10_000)
        cook_and_pick(sim)
        at(sim, TABLE)
        sim.time_left_ticks = 1
        names, _ = tick(sim, interact=True)
        self.assertEqual(names, ["served", "paid", "quan_end"])

    def test_close_discards_dish_still_on_stove(self):
        sim = make_sim(customers=[customer()], time_left=10_000)
        at(sim, STOVE)
        tick(sim, interact=True)
        sim.time_left_ticks = 1
        names, _ = tick(sim)
        self.assertEqual(names, ["customer_left", "dish_discarded", "quan_end"])
        self.assertEqual(sim.stoves[0]["state"], "idle")

    def test_close_waiting_customer_no_penalty(self):
        sim = make_sim(customers=[customer(patience_ticks_left=1)], time_left=1)
        names, events = tick(sim)
        self.assertEqual(names, ["customer_left", "quan_end"])
        self.assertEqual(events[0][1]["reason"], "closing")
        self.assertEqual(sim.reputation, Q["reputation_initial"])


if __name__ == "__main__":
    unittest.main()
