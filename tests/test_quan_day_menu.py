"""Phase 2 lát 4 (quan): menu theo kế hoạch Ngày, nhiều bếp/bàn, stats bàn giao, báo cáo cuối ca.

Bố trí 2 bếp / 4 bàn / 6 món là fixture riêng để kiểm luật, độc lập với preset trong manifest.
"""

import copy
import os
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

BASE = load_contract(os.path.join(os.path.dirname(__file__), "..", "game.contract.json"))["tuning"]


def tuning_p2():
    t = copy.deepcopy(BASE)
    q = t["quan"]
    q["stoves"] = [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}]
    q["tables"] = [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [12, 2]},
                   {"id": "T3", "pos": [9, 6]}, {"id": "T4", "pos": [12, 6]}]
    t["menu"] = {name: t["menu"][name] for name in ("ca_loc_nuong_trui", "goi_bong_sung")}
    t["menu"].update({
        "canh_chua_ca_keo": {"recipe": {"ca_keo": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 80},
        "keo_neo_nuong": {"recipe": {"keo_neo": 1}, "cook_s": 5, "price": 50},
        "lau_ca_keo": {"recipe": {"ca_keo": 2}, "cook_s": 9, "price": 100},
    })
    t["menu"]["ca_linh_kho"] = {"recipe": {"ca_linh": 2}, "cook_s": 6, "price": 70}
    return t


def sim_for(scenario=None, **kw):
    return QuanSim(tuning_p2(), scenario or {}, Streams(7), IdAllocator(), **kw)


IDLE = InputState((0.0, 0.0), {}, set())
PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})


def run_until_end(sim, presses=()):
    names = []
    while not sim.done:
        names += [n for n, _ in sim.step(PRESS if sim.phase_tick in presses else IDLE)]
    return names


class DayMenu(unittest.TestCase):
    def test_standalone_uses_full_menu(self):
        sim = sim_for({"stock": {}})
        self.assertEqual(sim.dish_ids, sorted(tuning_p2()["menu"]))
        self.assertEqual(len(sim.dish_ids), 6)

    def test_plan_filters_before_stock(self):
        # đủ kho cho mọi món nhưng kế hoạch chỉ có goi_bong_sung -> mọi khách gọi đúng món đó
        stock = {"bong_sung": 20, "ca_loc": 20, "ca_linh": 20, "bong_dien_dien": 20}  # ca_keo/keo_neo chờ inventory v1.1 (Hạnh)
        sim = sim_for({"stock": stock}, dish_ids=["goi_bong_sung"])
        while len(sim.customers) < 4:
            sim.step(IDLE)
        self.assertEqual({c["dish_id"] for c in sim.customers}, {"goi_bong_sung"})
        self.assertEqual([c["table_id"] for c in sim.customers], ["T1", "T2", "T3", "T4"])

    def test_plan_dish_without_stock_gives_no_dish(self):
        sim = sim_for({"stock": {"ca_loc": 5}}, dish_ids=["goi_bong_sung"])
        names = []
        for _ in range(int(sim.t["first_customer_tick"])):
            names += [n for n, _ in sim.step(IDLE)]
        self.assertEqual(names, ["no_dish"], "ca_loc có trong kho nhưng không thuộc kế hoạch")

    def test_plan_with_unknown_dish_rejected(self):
        with self.assertRaises(BadInput):
            sim_for({"stock": {}}, dish_ids=["pho_bo"])

    def test_fixture_customer_outside_plan_rejected(self):
        sc = {"stock": {"ca_loc": 1}, "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
        with self.assertRaises(BadInput):
            sim_for(sc, dish_ids=["goi_bong_sung"])

    def test_snapshot_lists_tonight_menu(self):
        sim = sim_for({"stock": {}}, dish_ids=["keo_neo_nuong", "goi_bong_sung"])
        self.assertEqual(sim.snapshot()["menu"], ["goi_bong_sung", "keo_neo_nuong"])


class SharedStock(unittest.TestCase):
    def test_reservations_share_physical_stock_and_cook_oldest(self):
        sc = {"stock": {"bong_sung": 4, "ca_loc": 1}, "random_customers": False,
              "customers": [
                  {"id": "C1", "table_id": "T3", "dish_id": "goi_bong_sung", "order_tick": 5},
                  {"id": "C2", "table_id": "T1", "dish_id": "goi_bong_sung", "order_tick": 5},
                  {"id": "C3", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 2},
              ]}
        sim = sim_for(sc)
        self.assertEqual({k: v for k, v in sim.available_stock().items() if v}, {})
        sim.pos = list(sim.stoves[0]["pos"])
        ev = sim.step(PRESS)
        self.assertEqual([d["order_id"] for n, d in ev if n == "cook_started"], ["C3"])
        sim.pos = list(sim.stoves[1]["pos"])
        sim.step(IDLE)
        ev = sim.step(PRESS)
        self.assertEqual([d["order_id"] for n, d in ev if n == "cook_started"], ["C2"], "hòa order_tick -> bàn T1")
        self.assertEqual(sim.stock, {"bong_sung": 2})
        self.assertEqual([c["order_status"] for c in sim.customers], ["reserved", "assigned", "assigned"])

    def test_overbooked_fixture_rejected(self):
        sc = {"stock": {"bong_sung": 3}, "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"},
                            {"id": "C2", "table_id": "T2", "dish_id": "goi_bong_sung"}]}
        with self.assertRaises(BadInput):
            sim_for(sc)


class Handover(unittest.TestCase):
    def test_start_stats_carried_and_shift_earned_resets(self):
        sim = sim_for({"stock": {}}, start={"money": 150, "earned": 300, "reputation": 4.2})
        self.assertEqual((sim.money, sim.earned, sim.reputation, sim.shift_earned), (150, 300, 4.2, 0))

    def test_money_above_earned_rejected(self):
        with self.assertRaises(BadInput):
            sim_for({"stock": {}}, start={"money": 10, "earned": 5})

    def test_shift_report_on_quan_end_once(self):
        sc = {"stock": {"bong_sung": 2}, "random_customers": False, "time_left_ticks": 2000,
              "customers": [
                  {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"},
                  {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": {},
                   "order_status": "unfulfillable", "patience_ticks_left": 5},
                  {"id": "C3", "table_id": "T3", "dish_id": "keo_neo_nuong", "reserved": {},
                   "order_status": "unfulfillable"},
              ]}
        sim = sim_for(sc, start={"money": 100, "earned": 100})
        sim.pos = list(sim.stoves[0]["pos"])
        cook = int(round(sim.menu["goi_bong_sung"]["cook_s"] * 60))
        ev = []
        ev += sim.step(PRESS)
        for _ in range(cook):
            ev += sim.step(IDLE)
        ev += sim.step(PRESS)                       # bưng
        sim.pos = list(sim.tables[0]["pos"])
        ev += sim.step(IDLE)
        ev += sim.step(PRESS)                       # giao, còn nhiều kiên nhẫn -> có boa
        while not sim.done:
            ev += sim.step(IDLE)
        ends = [d for n, d in ev if n == "quan_end"]
        self.assertEqual(len(ends), 1)
        price = sim.menu["goi_bong_sung"]["price"]
        tip = int(price * sim.t["tip_rate"])
        self.assertEqual({k: ends[0][k] for k in ("served", "paid", "left", "left_closing", "tips")},
                         {"served": 1, "paid": 1, "left": 1, "left_closing": 1, "tips": tip})
        self.assertEqual(ends[0]["shift_earned"], price + tip)
        self.assertEqual((ends[0]["money"], ends[0]["earned"]), (100 + price + tip,) * 2)
        self.assertEqual(sim.snapshot()["shift"]["served"], 1)


    def test_bad_start_rejected(self):
        hi = BASE["quan"]["reputation_max"]
        for start in ({"money": "5", "earned": "9"}, {"money": 1.5, "earned": 2}, {"money": True, "earned": 1},
                      {"reputation": hi + 1}, {"reputation": "x"}, {"reputation": True}):
            with self.subTest(start=start), self.assertRaises(BadInput):
                sim_for({"stock": {}}, start=start)

    def test_dish_ids_must_be_list(self):
        with self.assertRaises(BadInput):
            sim_for({"stock": {}}, dish_ids="goi_bong_sung")

    def test_fixture_eating_customer_counts_as_served(self):
        sc = {"stock": {}, "random_customers": False, "time_left_ticks": 1,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                             "order_status": "served", "reserved": {}, "eat_ticks_left": 50,
                             "base_price": BASE["menu"]["goi_bong_sung"]["price"], "tip": 0}]}
        sim = sim_for(sc, start={"money": 0, "earned": 0})
        end = [d for n, d in sim.step(IDLE) if n == "quan_end"][0]
        self.assertEqual((end["served"], end["paid"]), (1, 1))


class StandaloneV10Format(unittest.TestCase):
    def test_standalone_adds_no_new_keys(self):
        sim = sim_for({"stock": {}, "time_left_ticks": 1})
        snap = sim.snapshot()
        self.assertNotIn("menu", snap)
        self.assertNotIn("shift", snap)
        end = [d for n, d in sim.step(IDLE) if n == "quan_end"][0]
        self.assertEqual(set(end), {"reason", "money", "earned", "shift_earned", "reputation"})


if __name__ == "__main__":
    unittest.main()
