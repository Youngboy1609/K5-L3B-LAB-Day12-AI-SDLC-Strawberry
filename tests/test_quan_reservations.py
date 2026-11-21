import copy
import os
import unittest
from fractions import Fraction

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from chonoi.sim.quan_reservations import build_reservations

BASE = load_contract(os.path.join(os.path.dirname(__file__), "..", "game.contract.json"))["tuning"]
IDLE = InputState((0.0, 0.0), {}, set())
PRESS = InputState((0.0, 0.0), {"interact": True}, {"interact"})


def item(ident, kind="ca_loc", fresh=100):
    return {"id": ident, "kind": kind, "fresh": Fraction(str(fresh))}


def tuning():
    result = copy.deepcopy(BASE)
    result["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                           "quan_decay_per_s": 0.25, "spoiled_below": 30}
    result["reservations"] = {"count": 2, "table_hold_s": 30,
                              "price_multiplier": 1.5, "failed_reputation_delta": -1}
    return result


def make_sim(rows, stock=None, customers=None, **scenario_fields):
    t = tuning()
    random_customers = scenario_fields.pop("random_customers", False)
    scenario = {"stock": stock or [], "customers": customers or [], "random_customers": random_customers,
                "reservations": rows, **scenario_fields}
    return QuanSim(t, scenario, Streams(7), IdAllocator(), contract_version="1.2")


def events_named(events, name):
    return [data for event, data in events if event == name]


class ReservationSchedule(unittest.TestCase):
    def test_build_is_seeded_and_uses_unique_tables_with_initial_hold_state(self):
        t = tuning()
        scenario = {"quan": {"random_reservations": True}}
        a = build_reservations(t, scenario, Streams(7), ["ca_loc_nuong_trui"])
        b = build_reservations(t, scenario, Streams(7), ["ca_loc_nuong_trui"])
        self.assertEqual(a, b)
        self.assertEqual([row["id"] for row in a], ["R1", "R2"])
        self.assertEqual(len({row["table_id"] for row in a}), 2)
        self.assertEqual([row["state"] for row in a], [
            "holding" if row["arrival_tick"] <= 1800 else "scheduled" for row in a])

    def test_announcement_is_exposed_only_when_quan_owns_schedule(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1000}
        generated = make_sim([row], [item("I1")])
        injected = QuanSim(tuning(), {"stock": [item("I1")], "random_customers": False},
                           Streams(7), IdAllocator(), contract_version="1.2", reservations=[row])
        self.assertEqual(generated.initial_events[0][0], "reservation_announced")
        self.assertEqual(injected.initial_events, [])

    def test_reservation_arrival_emits_before_customer_and_holds_stock_ids(self):
        sim = make_sim([{"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                         "arrival_tick": 1}], [item("I1")])
        events = sim.step(IDLE)
        self.assertEqual([name for name, _ in events if name in ("reservation_arrived", "customer_arrived")],
                         ["reservation_arrived", "customer_arrived"])
        self.assertEqual(sim.reservations[0]["state"], "waiting")
        customer = sim.customers[0]
        self.assertEqual((customer["reservation_id"], customer["reserved"]), ("R1", ["I1"]))
        self.assertEqual(sim.snapshot()["tables"][0]["reservation_id"], "R1")
        self.assertEqual(sim.snapshot()["customers"][0]["reservation_id"], "R1")

    def test_table_hold_blocks_new_ordinary_customer(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1000}
        sim = make_sim([row], [item("I1"), item("I2")], random_customers=True)
        sim.t["first_customer_tick"] = 1
        events = sim.step(IDLE)
        self.assertEqual([customer["table_id"] for customer in sim.customers], ["T2"])
        self.assertEqual(sim.reservations[0]["state"], "holding")
        self.assertEqual(events_named(events, "customer_arrived")[0]["table_id"], "T2")

    def test_table_hold_begins_at_arrival_minus_configured_hold(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 2000}
        sim = make_sim([row], [item("I1")])
        self.assertEqual(sim.reservations[0]["state"], "scheduled")
        sim.phase_tick = 199
        sim.step(IDLE)
        self.assertEqual(sim.reservations[0]["state"], "holding")
        self.assertEqual(sim.snapshot()["tables"][0]["reservation_id"], "R1")

    def test_occupied_table_fails_and_penalizes_once(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "reserved": ["I1"]}
        sim = make_sim([row], [item("I1"), item("I2")], [customer])
        events = sim.step(IDLE)
        self.assertEqual(events_named(events, "reservation_failed")[0]["reason"], "occupied")
        self.assertEqual(sim.reservations[0]["state"], "failed")
        self.assertEqual(sim.reputation, BASE["quan"]["reputation_initial"] - 1)

    def test_stock_failure_releases_hold_with_one_failure_event(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}
        sim = make_sim([row])
        events = sim.step(IDLE)
        self.assertEqual(events_named(events, "reservation_failed")[0]["reason"], "stock")
        self.assertEqual(sim.reservations[0]["state"], "failed")
        self.assertEqual(sim.reputation, BASE["quan"]["reputation_initial"] - 1)

    def test_closing_fails_unarrived_orders(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1000}
        sim = make_sim([row], [item("I1")], time_left_ticks=1)
        events = sim.step(IDLE)
        self.assertEqual(events_named(events, "reservation_failed")[0]["reason"], "closing")
        self.assertEqual(sim.reservations[0]["state"], "failed")
        self.assertEqual(sim.reputation, BASE["quan"]["reputation_initial"] - 1)

    def test_closing_failures_order_waiting_and_future_reservations_by_id(self):
        rows = [
            {"id": "R2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 2},
            {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1000},
        ]
        waiting = {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui",
                   "reserved": ["I2"], "reservation_id": "R2"}
        sim = make_sim(rows, [item("I1"), item("I2")], [waiting], time_left_ticks=1)
        events = sim.step(IDLE)
        self.assertEqual([event["id"] for event in events_named(events, "reservation_failed")], ["R1", "R2"])

    def test_reservation_patience_failure_uses_one_penalty_and_replaces_customer_left(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}
        sim = make_sim([row], [item("I1")])
        sim.step(IDLE)
        sim.customers[0]["patience_ticks_left"] = 1
        events = sim.step(IDLE)
        self.assertEqual(events_named(events, "reservation_failed")[0]["reason"], "patience")
        self.assertEqual(events_named(events, "customer_left"), [])
        self.assertEqual(sim.reservations[0]["state"], "failed")
        self.assertEqual(sim.reputation, BASE["quan"]["reputation_initial"] - 1)

    def test_reserved_price_multiplier_and_success_events(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}
        sim = make_sim([row], [item("I1")])
        sim.step(IDLE)
        sim.pos = list(sim.stoves[0]["pos"])
        sim.step(PRESS)
        for _ in range(sim.stoves[0]["cook_ticks_left"]):
            sim.step(IDLE)
        sim.step(PRESS)
        sim.pos = list(sim.tables[0]["pos"])
        events = sim.step(PRESS)
        # Freshness has crossed an integer price boundary before cooking, then the multiplier floors once.
        self.assertEqual(events_named(events, "served")[0]["base_price"], 88)
        self.assertEqual([name for name, _ in events if name in ("served", "reservation_served")],
                         ["served", "reservation_served"])
        self.assertEqual(sim.reservations[0]["state"], "served")

    def test_burnt_reserved_dish_fails_before_reservation_failure(self):
        row = {"id": "R1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "arrival_tick": 1}
        sim = make_sim([row], [item("I1")])
        sim.step(IDLE)
        sim.t["burn_s"] = 0
        sim.pos = list(sim.stoves[0]["pos"])
        sim.step(PRESS)
        for _ in range(sim.stoves[0]["cook_ticks_left"]):
            sim.step(IDLE)
        events = sim.step(IDLE)
        self.assertEqual([name for name, _ in events if name in ("dish_burnt", "reservation_failed")],
                         ["dish_burnt", "reservation_failed"])
        self.assertEqual(events_named(events, "dish_burnt")[0]["order_status"], "failed")
        self.assertEqual(events_named(events, "reservation_failed")[0]["reason"], "burnt")
        self.assertEqual(sim.reservations[0]["state"], "failed")


if __name__ == "__main__":
    unittest.main()
