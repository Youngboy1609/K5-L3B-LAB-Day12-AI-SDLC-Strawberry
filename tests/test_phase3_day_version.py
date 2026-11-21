"""Focused regression coverage for the v1.2 manifest/scenario boundary."""

from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.scenario import _validate_id_references, _validate_quan_payload, load_scenario
from chonoi.sim.day import DaySim


class Phase3VersionBoundary(unittest.TestCase):
    def test_manifest_freshness_is_normalized_into_tuning(self):
        manifest = load_contract()
        manifest["contract_version"] = "1.2"
        manifest["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5,
                                 "quan_decay_per_s": 0.25, "spoiled_below": 30}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            loaded = load_contract(path)
        self.assertEqual(loaded["tuning"]["freshness"], manifest["freshness"])

    def test_manifest_rejects_nonfinite_freshness(self):
        manifest = load_contract()
        manifest["contract_version"] = "1.2"
        manifest["freshness"] = {"initial": 100, "gather_decay_per_s": float("nan"),
                                 "quan_decay_per_s": 0.25, "spoiled_below": 30}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contract.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(BadInput):
                load_contract(path)

    def test_v12_scenario_uses_adapter_validation_and_preserves_decimal_fresh(self):
        tuning = deepcopy(load_contract()["tuning"])
        raw = {"gather": {"hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30.025}],
                          "monsters": []}}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scenario.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            seen = []

            def validate_item_list(items, kinds):
                seen.extend(items)
                return items

            with patch("chonoi.inventory.validate_item_list", validate_item_list, create=True):
                scenario = load_scenario(path, "gather", tuning, "1.2")
        self.assertEqual(scenario["hold"][0]["fresh"], Decimal("30.025"))
        self.assertIsInstance(seen[0]["fresh"], Fraction)
        self.assertEqual(seen[0]["fresh"], Fraction("30.025"))

    def test_v12_reserved_ids_are_unique_nonempty_references(self):
        _validate_id_references("reserved", ["I1", "I2"])
        for refs in (["I1", "I1"], ["I1", ""], {"ca_linh": 1}):
            with self.subTest(refs=refs), self.assertRaises(BadInput):
                _validate_id_references("reserved", refs)

    def test_v12_cooked_payload_price_accepts_discount_within_menu_ceiling(self):
        menu = {"dish": {"price": 85}}
        _validate_quan_payload("hand", {"order_id": "C1", "dish_id": "dish", "base_price": 50}, menu, "1.2")
        for price in (86, -1, True):
            with self.subTest(price=price), self.assertRaises(BadInput):
                _validate_quan_payload("hand", {"order_id": "C1", "dish_id": "dish", "base_price": price}, menu, "1.2")


    def test_later_days_reissue_ids_and_preserve_initial_freshness(self):
        sample = {"id": "I4", "kind": "ca_linh", "fresh": Decimal("30.025")}
        fixture = {"gather": {"hold": [sample]}}
        initial_states = []

        def gather(tuning, scenario, streams, ids, *, day, contract_version):
            self.assertEqual(contract_version, "1.2")
            initial_states.append(deepcopy(scenario["hold"]))
            scenario["hold"][0]["fresh"] -= Decimal("0.01")
            ids.new("I")
            return SimpleNamespace()

        def new_item(ids, kind, fresh):
            return {"id": ids.new("I"), "kind": kind, "fresh": fresh}

        with patch("chonoi.sim.day.GatherSim", side_effect=gather):
            with patch("chonoi.inventory.new_item", new_item, create=True):
                sim = DaySim(load_contract()["tuning"], fixture, 42, days=2, contract_version="1.2")
                sim.day = 2
                sim._build_day()

        self.assertEqual(initial_states[0][0]["id"], "I4")
        self.assertEqual(initial_states[1][0]["id"], "I6")
        self.assertEqual(sample["fresh"], Decimal("30.025"))
        self.assertEqual(initial_states[1][0]["fresh"], sample["fresh"])


if __name__ == "__main__":
    unittest.main()
