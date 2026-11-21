"""File kho v1.0/v1.1 (Contract G): {"items": {id: số nguyên >= 0}}.
File kho v1.2: {"items": [{"id": str, "kind": str, "fresh": số 0..100}, ...]}.

v1.2 giữ fresh ở dạng Fraction (số hữu tỉ chính xác) để tính luật; số đã làm
tròn khi xuất chỉ để hiển thị (item_payload làm tròn 5 chữ số) — không dùng
số đã xuất để tính luật.

Đọc: từ chối sai schema / id lạ / số âm / fresh ngoài miền (BadInput -> mã 2).
Chữ ký cũ (không truyền contract_version) vẫn đọc file count v1.0/v1.1.
Ghi: qua file tạm cùng thư mục rồi thay thế đúng một lần, byte-ổn-định;
khi lỗi ghi, file đích giữ nguyên.
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

NODE_KINDS_P1 = ("bong_dien_dien", "bong_sung")
NODE_KINDS_P2 = (*NODE_KINDS_P1, "keo_neo")
KINDS_P1 = ("ca_loc", "ca_linh", *NODE_KINDS_P1)
KINDS_P2 = (*KINDS_P1, "ca_keo", "keo_neo")

ITEM_KEYS_V12 = frozenset(("id", "kind", "fresh"))
FRESH_EXPORT_DIGITS = 5  # file kho và JSONL xuất fresh cùng độ chính xác này


def _to_fraction(value, what):
    """Số hữu tỉ chính xác: Fraction nguyên vẹn; float quy về thập phân gọi ra."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise BadInput(f"{what} phải là số, nhận: {value!r}")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BadInput(f"{what} phải hữu hạn, nhận: {value!r}")
        # limit_denominator bỏ nhiễu biểu diễn: 0.004166666666666667 -> 1/240
        # để ca biên (bốn tick Quán vẫn tươi, tick kế ươn) đúng như kế hoạch.
        return Fraction(str(value)).limit_denominator(10 ** 9)
    return Fraction(value)


def ingredient_kinds(contract_version):
    return KINDS_P2 if contract_version in ("1.1", "1.2") else KINDS_P1


def validate_items(items, kinds=KINDS_P1):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def validate_item_list(raw, kinds=KINDS_P1) -> list:
    """Kho v1.2: mảng cá thể, giữ thứ tự đầu vào, fresh chính xác (Fraction)."""
    if not isinstance(raw, list):
        raise BadInput("kho v1.2 phải là mảng cá thể")
    out = []
    seen = set()
    for pos, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise BadInput(f"cá thể thứ {pos} phải là object")
        if set(entry.keys()) != ITEM_KEYS_V12:
            raise BadInput(f"cá thể thứ {pos} phải có đúng khóa id, kind, fresh")
        ident = entry["id"]
        if not isinstance(ident, str) or not ident:
            raise BadInput(f"id cá thể phải là chuỗi khác rỗng (vị trí {pos})")
        if ident in seen:
            raise BadInput(f"id cá thể trùng: {ident}")
        seen.add(ident)
        if entry["kind"] not in kinds:
            raise BadInput(f"nguyên liệu lạ: {entry['kind']}")
        fresh = _to_fraction(entry["fresh"], f"fresh của {ident}")
        if fresh < 0 or fresh > 100:
            raise BadInput(f"fresh ngoài miền 0..100 cho {ident}: {entry['fresh']!r}")
        out.append({"id": ident, "kind": entry["kind"], "fresh": fresh})
    return out


def read_inventory(path: str, kinds=KINDS_P1, *, contract_version=None):
    """v1.2 -> list cá thể; mặc định (không version) -> dict đếm như v1.0/v1.1."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}") from e
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    if contract_version == "1.2":
        return validate_item_list(data["items"], kinds)
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def new_item(allocator, kind, fresh) -> dict:
    """Cấp id qua ids.new(\"I\"); fresh quy về Fraction chính xác."""
    return {"id": allocator.new("I"), "kind": kind,
            "fresh": _to_fraction(fresh, f"fresh của {kind}")}


def decay_items(items: list, amount, spoiled_below) -> list:
    """Hao fresh các cá thể đầu bước; trả các cá thể vừa xuống dưới ngưỡng (theo ID).

    Hao fresh từng cá thể tại chỗ (mutate mảng đầu vào). Xuống DƯỚI ngưỡng
    (fresh < spoiled_below) mới ươn: đúng bằng ngưỡng thì chưa. Bên gọi xóa
    cá thể đã ươn khỏi kho và phát `spoiled {item_id, kind, location}`.
    amount < 0 bị từ chối (không hồi độ tươi).
    """
    amt = _to_fraction(amount, "số hao fresh")
    below = _to_fraction(spoiled_below, "ngưỡng ươn")
    if amt < 0:
        raise BadInput(f"số hao fresh phải không âm, nhận: {amount!r}")
    for item in items:
        item["fresh"] -= amt
    spoiled = [item for item in items if item["fresh"] < below]
    return sort_by_id(spoiled)


def item_payload(item: dict) -> dict:
    """Projection dùng chung file kho và JSONL: fresh xuất 5 chữ số."""
    r = round(float(item["fresh"]), FRESH_EXPORT_DIGITS)
    return {"id": item["id"], "kind": item["kind"], "fresh": 0.0 if r == 0 else r}


def write_inventory(path: str, items, *, contract_version=None):
    """v1.2: items là list cá thể, ghi sắp theo ID (I2 trước I10).
    Mặc định: items là dict đếm như v1.0/v1.1, bỏ mục bằng 0."""
    if contract_version == "1.2":
        body_items = [item_payload(i) for i in sort_by_id(list(items))]
    else:
        body_items = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": body_items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
