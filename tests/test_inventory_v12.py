"""Test kho v1.2: file mảng cá thể {id, kind, fresh}.

Ghi theo phân công phase3/inventory-freshness (Hạnh):
- File hợp lệ: mảng cá thể, fresh 0/30/97.5/100, kho rỗng, thứ tự đầu vào giữ nguyên.
- Từ chối: file count ở v1.2, id trùng, id rỗng, kind lạ, bool, NaN/vô hạn, fresh ngoài miền.
- Backward-compat: chữ ký cũ (không contract_version) vẫn đọc/ghi file count v1.0/v1.1.
- Số hữu tỉ chính xác cho fresh và số hao; file và JSONL xuất fresh cùng độ chính xác.
"""

import json
import os
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from unittest import mock

from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inventory import (
    KINDS_P1,
    KINDS_P2,
    decay_items,
    ingredient_kinds,
    item_payload,
    new_item,
    read_inventory,
    validate_item_list,
    write_inventory,
)
from chonoi.jsonl import dumps

GATHER_HAO = Fraction(1, 120)  # 1 tick Gather theo smoke phút 20
QUAN_HAO = Fraction(1, 240)  # 1 tick Quán: bốn tick vẫn tươi, tick kế tiếp ươn


class BaseV12(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def path(self, name, obj):
        p = os.path.join(self.dir.name, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False))
        return p


class ValidItemFiles(BaseV12):
    def test_file_preserves_both_sides_of_spoil_threshold(self):
        literals = ("29.99999999999999999", "30.00000000000000001")
        p = self.path("threshold.json", '{"items":[' + ",".join(
            f'{{"id":"I{i}","kind":"ca_linh","fresh":{literal}}}'
            for i, literal in enumerate(literals, start=1)
        ) + "]}")
        items = read_inventory(p, contract_version="1.2")
        self.assertEqual([item["fresh"] for item in items], [Fraction(x) for x in literals])
        self.assertEqual([item["id"] for item in decay_items(items, 0, 30)], ["I1"])

    def test_roundtrip_preserves_which_quan_tick_spoils(self):
        boundary = Fraction("30.025")
        items = [{"id": "I1", "kind": "ca_linh", "fresh": boundary - Fraction("1e-20")},
                 {"id": "I2", "kind": "ca_linh", "fresh": boundary}]
        decay_items(items, GATHER_HAO, 30)
        p = os.path.join(self.dir.name, "threshold-roundtrip.json")
        write_inventory(p, items, contract_version="1.2")
        back = read_inventory(p, contract_version="1.2")
        for _ in range(3):
            self.assertEqual(decay_items(back, QUAN_HAO, 30), [])
        self.assertEqual([item["id"] for item in decay_items(back, QUAN_HAO, 30)], ["I1"])
        self.assertEqual([item["id"] for item in decay_items(back[1:], QUAN_HAO, 30)], ["I2"])

    def test_valid_list_keeps_order_and_exact_fresh(self):
        p = self.path("kho.json", {"items": [
            {"id": "I1", "kind": "ca_linh", "fresh": 0},
            {"id": "I2", "kind": "ca_loc", "fresh": 30},
            {"id": "I3", "kind": "ca_keo", "fresh": 97.5},
            {"id": "I4", "kind": "bong_sung", "fresh": 100},
        ]})
        items = read_inventory(p, KINDS_P2, contract_version="1.2")
        self.assertEqual([it["id"] for it in items], ["I1", "I2", "I3", "I4"])
        self.assertEqual([it["kind"] for it in items],
                         ["ca_linh", "ca_loc", "ca_keo", "bong_sung"])
        self.assertEqual([it["fresh"] for it in items],
                         [Fraction(0), Fraction(30), Fraction("97.5"), Fraction(100)])

    def test_empty_inventory_ok(self):
        p = self.path("rong.json", {"items": []})
        self.assertEqual(read_inventory(p, KINDS_P2, contract_version="1.2"), [])

    def test_fresh_boundaries_0_and_100_ok(self):
        p = self.path("bien.json", {"items": [
            {"id": "I1", "kind": "ca_linh", "fresh": 0},
            {"id": "I2", "kind": "ca_linh", "fresh": 100},
        ]})
        items = read_inventory(p, KINDS_P1, contract_version="1.2")
        self.assertEqual([it["fresh"] for it in items], [Fraction(0), Fraction(100)])

    def test_roundtrip_keeps_fresh_precision(self):
        # ca phân công: 30.025 -> một tick Gather -> ghi/đọc -> bốn tick Quán vẫn tươi
        items = [{"id": "I1", "kind": "ca_linh", "fresh": Fraction("30.025")}]
        decay_items(items, GATHER_HAO, 30)
        p = os.path.join(self.dir.name, "roundtrip.json")
        write_inventory(p, items, contract_version="1.2")
        back = read_inventory(p, KINDS_P1, contract_version="1.2")
        self.assertAlmostEqual(back[0]["fresh"], items[0]["fresh"], places=12)
        for _ in range(4):  # bốn tick Quán vẫn ở nhánh tươi
            self.assertEqual(decay_items(back, QUAN_HAO, 30), [])
        spoiled = decay_items(back, QUAN_HAO, 30)
        self.assertEqual([it["id"] for it in spoiled], ["I1"])  # tick Quán kế mới ươn


class RejectedItemFiles(BaseV12):
    def read_v12(self, name, obj, kinds=KINDS_P2, version="1.2"):
        return read_inventory(self.path(name, obj), kinds, contract_version=version)

    def test_count_file_rejected_in_v12(self):
        with self.assertRaises(BadInput):
            self.read_v12("count.json", {"items": {"ca_linh": 1}})

    def test_old_signature_rejects_item_array(self):
        with self.assertRaises(BadInput):
            self.read_v12("mang.json", {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}]},
                          version=None)

    def test_items_not_a_list(self):
        with self.assertRaises(BadInput):
            self.read_v12("saikieu.json", {"items": "khong-phai-mang"})

    def test_duplicate_ids(self):
        with self.assertRaises(BadInput):
            self.read_v12("trung.json", {"items": [
                {"id": "I1", "kind": "ca_linh", "fresh": 50},
                {"id": "I1", "kind": "ca_loc", "fresh": 60},
            ]})

    def test_empty_id(self):
        with self.assertRaises(BadInput):
            self.read_v12("rongid.json", {"items": [{"id": "", "kind": "ca_linh", "fresh": 50}]})

    def test_non_string_id(self):
        with self.assertRaises(BadInput):
            self.read_v12("idso.json", {"items": [{"id": 5, "kind": "ca_linh", "fresh": 50}]})

    def test_unknown_kind(self):
        with self.assertRaises(BadInput):
            self.read_v12("kindow.json", {"items": [{"id": "I1", "kind": "ca_basa", "fresh": 50}]})

    def test_bool_fresh(self):
        with self.assertRaises(BadInput):
            self.read_v12("bool.json", {"items": [{"id": "I1", "kind": "ca_linh", "fresh": True}]})

    def test_nan_and_infinite_fresh(self):
        with self.assertRaises(BadInput):
            self.read_v12("nan.json", '{"items":[{"id":"I1","kind":"ca_linh","fresh":NaN}]}')
        with self.assertRaises(BadInput):
            self.read_v12("inf.json", '{"items":[{"id":"I1","kind":"ca_linh","fresh":Infinity}]}')
        with self.assertRaises(BadInput):
            self.read_v12("inf2.json", '{"items":[{"id":"I1","kind":"ca_linh","fresh":-Infinity}]}')

    def test_fresh_out_of_range(self):
        for bad in (-0.5, 100.5, 101):
            with self.assertRaises(BadInput):
                self.read_v12("ngoaimien.json",
                              {"items": [{"id": "I1", "kind": "ca_linh", "fresh": bad}]})
        with self.assertRaises(BadInput):
            self.read_v12("ngoaimien.json",
                          '{"items":[{"id":"I1","kind":"ca_linh","fresh":100.00000000000000001}]}')

    def test_non_numeric_fresh(self):
        with self.assertRaises(BadInput):
            self.read_v12("chuoi.json", {"items": [{"id": "I1", "kind": "ca_linh", "fresh": "30"}]})

    def test_missing_or_extra_item_keys(self):
        with self.assertRaises(BadInput):
            self.read_v12("thieu.json", {"items": [{"id": "I1", "kind": "ca_linh"}]})
        with self.assertRaises(BadInput):
            self.read_v12("du.json", {"items": [
                {"id": "I1", "kind": "ca_linh", "fresh": 50, "price": 1000}]})

    def test_broken_top_level(self):
        with self.assertRaises(BadInput):
            self.read_v12("saigoc.json", [{"id": "I1"}])
        with self.assertRaises(BadInput):
            self.read_v12("thieugoc.json", {"kho": []})
        with self.assertRaises(BadInput):
            self.read_v12("dugoc.json", {"items": [], "extra": 1})

    def test_valid_file_after_rejections_still_reads(self):
        p = self.path("ok.json", {"items": [{"id": "I1", "kind": "ca_loc", "fresh": 75}]})
        self.assertEqual(len(read_inventory(p, KINDS_P1, contract_version="1.2")), 1)


class CompatCountFiles(BaseV12):
    def test_v11_count_file_still_reads_with_old_signature(self):
        p = self.path("cu.json", {"items": {"ca_linh": 3, "ca_loc": 0}})
        self.assertEqual(read_inventory(p), {"ca_linh": 3})
        self.assertEqual(read_inventory(p, KINDS_P2), {"ca_linh": 3})

    def test_v11_count_file_reads_with_explicit_v11(self):
        p = self.path("cu11.json", {"items": {"ca_linh": 2}})
        self.assertEqual(read_inventory(p, KINDS_P2, contract_version="1.1"), {"ca_linh": 2})

    def test_old_writer_still_writes_counts(self):
        p = os.path.join(self.dir.name, "ghi-cu.json")
        write_inventory(p, {"ca_loc": 2, "ca_linh": 0, "bong_sung": 1})
        with open(p, encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"items": {"bong_sung": 1, "ca_loc": 2}})

    def test_ingredient_kinds_covers_v12(self):
        self.assertEqual(ingredient_kinds("1.2"), KINDS_P2)
        self.assertEqual(ingredient_kinds("1.1"), KINDS_P2)
        self.assertEqual(ingredient_kinds("1.0"), KINDS_P1)


class ValidateItemList(BaseV12):
    def test_keeps_input_order_with_exact_fractions(self):
        raw = [{"id": "I2", "kind": "ca_linh", "fresh": 30.025},
               {"id": "I1", "kind": "ca_linh", "fresh": 0}]
        out = validate_item_list(raw, KINDS_P1)
        self.assertEqual([it["id"] for it in out], ["I2", "I1"])
        self.assertEqual(out[0]["fresh"], Fraction("30.025"))

    def test_empty_ok(self):
        self.assertEqual(validate_item_list([], KINDS_P1), [])


class NewItemTests(BaseV12):
    def test_allocates_ids_in_sequence(self):
        alloc = IdAllocator()
        a = new_item(alloc, "ca_linh", 100)
        b = new_item(alloc, "ca_loc", 97.5)
        self.assertEqual(a["id"], "I1")
        self.assertEqual(b["id"], "I2")
        self.assertEqual(a["kind"], "ca_linh")
        self.assertEqual(a["fresh"], Fraction(100))
        self.assertEqual(b["fresh"], Fraction("97.5"))

    def test_reserve_for_fixture_continues_allocation(self):
        alloc = IdAllocator()
        alloc.reserve("I5")
        item = new_item(alloc, "ca_keo", 90)
        self.assertEqual(item["id"], "I6")


class DecayItems(BaseV12):
    def test_fresh_30_spoils_after_one_gather_tick(self):
        items = [{"id": "I1", "kind": "ca_linh", "fresh": Fraction(30)}]
        spoiled = decay_items(items, GATHER_HAO, 30)
        self.assertEqual([it["id"] for it in spoiled], ["I1"])
        self.assertEqual(items[0]["fresh"], Fraction(3599, 120))

    def test_fresh_100_after_one_gather_tick_not_spoiled(self):
        items = [{"id": "I1", "kind": "ca_linh", "fresh": Fraction(100)}]
        spoiled = decay_items(items, GATHER_HAO, 30)
        self.assertEqual(spoiled, [])
        self.assertEqual(items[0]["fresh"], Fraction(11999, 120))

    def test_exact_threshold_is_not_spoiled(self):
        # 30.025 - 4*(1/240) == 30 đúng: chỉ khi xuống DƯỚI ngưỡng mới ươn
        items = [{"id": "I1", "kind": "ca_linh", "fresh": Fraction("30.025")}]
        decay_items(items, GATHER_HAO, 30)
        self.assertEqual(items[0]["fresh"], Fraction(1801, 60))
        for _ in range(4):
            spoiled = decay_items(items, QUAN_HAO, 30)
            self.assertEqual(spoiled, [])
        self.assertEqual(items[0]["fresh"], Fraction(30))
        spoiled = decay_items(items, QUAN_HAO, 30)
        self.assertEqual([it["id"] for it in spoiled], ["I1"])

    def test_decimal_floats_stay_on_the_fresh_branch(self):
        # bên gọi có thể đưa float: 30.025 -> 4 tick Quán vẫn tươi, tick kế ươn
        items = [{"id": "I1", "kind": "ca_linh", "fresh": 30.025}]
        decay_items(items, 1 / 120, 30)
        for _ in range(4):
            self.assertEqual(decay_items(items, 1 / 240, 30), [])
        self.assertEqual([it["id"] for it in decay_items(items, 1 / 240, 30)], ["I1"])

    def test_returned_spoiled_sorted_by_id(self):
        items = [{"id": "I10", "kind": "ca_linh", "fresh": 29},
                 {"id": "I2", "kind": "ca_loc", "fresh": 29}]
        spoiled = decay_items(items, Fraction(1, 240), 30)
        self.assertEqual([it["id"] for it in spoiled], ["I2", "I10"])

    def test_zero_amount_no_op(self):
        items = [{"id": "I1", "kind": "ca_linh", "fresh": 30}]
        self.assertEqual(decay_items(items, 0, 30), [])
        self.assertEqual(items[0]["fresh"], 30)


class ItemPayloadAndJsonl(BaseV12):
    def test_file_and_jsonl_preserve_numeric_literal_near_threshold(self):
        fresh = Decimal("29.99999999999999999")
        item = {"id": "I1", "kind": "ca_linh", "fresh": Fraction(fresh)}
        p = os.path.join(self.dir.name, "exact.json")
        write_inventory(p, [item], contract_version="1.2")
        with open(p, encoding="utf-8") as f:
            stored = json.load(f, parse_float=Decimal)
        line = json.loads(dumps({"items": [item_payload(item)]}), parse_float=Decimal)
        self.assertEqual(stored["items"][0]["fresh"], fresh)
        self.assertEqual(line, stored)

    def test_payload_keeps_exact_freshness(self):
        p = item_payload({"id": "I1", "kind": "ca_linh", "fresh": Fraction(11999, 120)})
        self.assertEqual(p, {"id": "I1", "kind": "ca_linh", "fresh": Fraction(11999, 120)})
        p0 = item_payload({"id": "I2", "kind": "ca_loc", "fresh": Fraction(30)})
        self.assertEqual(p0["fresh"], 30.0)

    def test_file_and_jsonl_export_same_fresh_precision(self):
        item = {"id": "I1", "kind": "ca_linh", "fresh": Fraction(11999, 120)}
        p = os.path.join(self.dir.name, "same.json")
        write_inventory(p, [item], contract_version="1.2")
        with open(p, encoding="utf-8") as f:
            file_fresh = json.load(f, parse_float=Decimal)["items"][0]["fresh"]
        line = json.loads(dumps({"data": {"inventory": {"items": [item_payload(item)]}}}),
                          parse_float=Decimal)
        self.assertEqual(line["data"]["inventory"]["items"][0]["fresh"], file_fresh)

    def test_jsonl_keeps_other_floats_at_three_digits(self):
        self.assertEqual(dumps({"x": 1.23456, "fresh": 99.99167}),
                         '{"x":1.235,"fresh":99.99167}')

    def test_jsonl_accepts_fraction_fresh(self):
        fresh = Fraction(11999, 120)
        line = json.loads(dumps({"fresh": fresh}), parse_float=Decimal)
        self.assertAlmostEqual(Fraction(line["fresh"]), fresh, places=12)


class WriteInventoryV12(BaseV12):
    def test_sorts_I2_before_I10(self):
        p = os.path.join(self.dir.name, "sap.json")
        items = [{"id": "I10", "kind": "ca_linh", "fresh": 50},
                 {"id": "I2", "kind": "ca_loc", "fresh": 60}]
        write_inventory(p, items, contract_version="1.2")
        with open(p, encoding="utf-8") as f:
            got = json.load(f)["items"]
        self.assertEqual([it["id"] for it in got], ["I2", "I10"])

    def test_keeps_target_file_on_write_failure(self):
        p = os.path.join(self.dir.name, "loi.json")
        write_inventory(p, [{"id": "I1", "kind": "ca_linh", "fresh": 100}],
                        contract_version="1.2")
        with open(p, encoding="utf-8") as f:
            before = f.read()
        with mock.patch("chonoi.inventory.os.replace", side_effect=OSError("đĩa đầy")):
            with self.assertRaises(OSError):
                write_inventory(p, [{"id": "I1", "kind": "ca_linh", "fresh": 10}],
                                contract_version="1.2")
        with open(p, encoding="utf-8") as f:
            self.assertEqual(f.read(), before)
        leftovers = [n for n in os.listdir(self.dir.name) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
