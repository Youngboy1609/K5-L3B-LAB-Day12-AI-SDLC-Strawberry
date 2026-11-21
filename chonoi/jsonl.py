"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác).

Ngoại lệ: trường `fresh` của cá thể kho v1.2 xuất 5 chữ số, trùng độ chính xác
với file kho (xem chonoi.inventory.item_payload). Fraction (nếu lọt vào event)
được quy về số trước khi xuất.
"""

import json
from fractions import Fraction

_FRESH_DIGITS = 5
_DEFAULT_DIGITS = 3


def _clean(v, key=None):
    if isinstance(v, float):
        r = round(v, _FRESH_DIGITS if key == "fresh" else _DEFAULT_DIGITS)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, Fraction):
        return _clean(float(v), key)
    if isinstance(v, dict):
        return {k: _clean(x, k) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self._f = open(path, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self):
        self._f.close()
