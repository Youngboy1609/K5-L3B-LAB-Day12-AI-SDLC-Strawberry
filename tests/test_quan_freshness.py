import copy
import os
import unittest
from fractions import Fraction

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim

BASE = load_contract(os.path.join(os.path.dirname(__file__), "..", "game.contract.json"))["tuning"]
IDLE = InputState((0.0, 0.0), {}, set())
PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})


def sim_for(stock, customers=(), **kwargs):
    tuning = copy.deepcopy(BASE)
    tuning["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                            "quan_decay_per_s": 0.25, "spoiled_below": 30}
    scenario = {"stock": stock, "customers": list(customers), "random_customers": False}
    return QuanSim(tuning, scenario, Streams(3), IdAllocator(), contract_version="1.2", **kwargs)


def item(ident, kind="bong_sung", fresh=100):
    return {"id": ident, "kind": kind, "fresh": Fraction(str(fresh))}


def customer(reserved, dish="goi_bong_sung", **kwargs):
    return {"id": "C1", "table_id": "T1", "dish_id": dish, "order_tick": 0,
            "reserved": reserved, **kwargs}


class QuanFreshness(unittest.TestCase):
    def test_stock_decays_emits_spoiled_once_and_remains_physical(self):
        sim = sim_for([item("I2", fresh=30), item("I1", fresh=30.02)])
        first = sim.step(IDLE)
        self.assertEqual([(n, d) for n, d in first if n == "spoiled"], [
            ("spoiled", {"item_id": "I2", "kind": "bong_sung", "location": "stock"})])
        self.assertEqual([x["id"] for x in sim.stock], ["I2", "I1"])
        self.assertEqual(list(sim.available_stock()), ["I1"])
        second = sim.step(IDLE)
        self.assertEqual([n for n, _ in second if n == "spoiled"], [])

    def test_held_spoiled_item_is_replaced_by_freshest_then_id(self):
        sim = sim_for([item("I1", fresh=30), item("I3", fresh=80), item("I2", fresh=80)],
                      [customer(["I1", "I3"])])
        events = sim.step(IDLE)
        self.assertEqual([d for n, d in events if n == "spoiled"], [
            {"item_id": "I1", "kind": "bong_sung", "location": "stock"}])
        self.assertEqual([d for n, d in events if n == "spoiled"], sorted(
            [d for n, d in events if n == "spoiled"], key=lambda d: d["item_id"]))
        self.assertEqual(sim.customers[0]["reserved"], ["I2", "I3"])
        self.assertEqual([x["id"] for x in sim.snapshot()["stock"]], ["I1", "I2", "I3"])

    def test_insufficient_replacement_releases_reservation_and_marks_unfulfillable(self):
        sim = sim_for([item("I1", fresh=30), item("I2", fresh=80)],
                      [customer(["I1", "I2"])])
        events = sim.step(IDLE)
        self.assertEqual(sim.customers[0]["order_status"], "unfulfillable")
        self.assertEqual(sim.customers[0]["reserved"], [])
        failed = [(n, d) for n, d in events if n == "order_unfulfillable"]
        self.assertEqual(failed, [("order_unfulfillable", {
            "customer_id": "C1", "table_id": "T1", "reason": "stock"})])

    def test_cook_price_uses_exact_post_decay_freshness_and_item_payloads(self):
        stock = [item("I2", "bong_sung", 50.01), item("I1", "bong_sung", 60.01)]
        sim = sim_for(stock, [customer(["I1", "I2"])])
        sim.pos = list(sim.stoves[0]["pos"])
        events = sim.step(PRESS)
        cooked = next(data for name, data in events if name == "cook_started")
        decay = Fraction(1, 240)
        actual = [Fraction("60.01") - decay, Fraction("50.01") - decay]
        expected_price = (sim.menu["goi_bong_sung"]["price"] * sum(actual) / 200).__floor__()
        self.assertEqual(cooked["base_price"], expected_price)
        self.assertEqual(sim.stoves[0]["dish"]["base_price"], expected_price)
        self.assertEqual(cooked["items"], [
            {"id": "I1", "kind": "bong_sung", "fresh": actual[0]},
            {"id": "I2", "kind": "bong_sung", "fresh": actual[1]},
        ])

    def test_v12_rejects_missing_or_shared_reserved_ids(self):
        stock = [item("I1"), item("I2")]
        with self.assertRaises(BadInput):
            sim_for(stock, [customer(["unknown", "I2"])])
        second = dict(customer(["I1", "I2"]), id="C2", table_id="T2")
        with self.assertRaises(BadInput):
            sim_for(stock, [customer(["I1", "I2"]), second])

    def test_missing_reservations_allocate_by_order_then_freshness_and_id(self):
        first = customer([], order_tick=5)
        first.pop("reserved")
        second = dict(customer([], order_tick=1), id="C2", table_id="T2")
        second.pop("reserved")
        customers = [first, second]
        stock = [item("I4", fresh=80), item("I2", fresh=90),
                 item("I3", fresh=90), item("I1", fresh=70)]
        sim = sim_for(stock, customers)
        self.assertEqual(sim.customers[1]["reserved"], ["I2", "I3"])
        self.assertEqual(sim.customers[0]["reserved"], ["I4", "I1"])


if __name__ == "__main__":
    unittest.main()
