"""Ghi JSONL tất định, giữ độ chính xác của fresh v1.2 và làm tròn số đo khác."""

import json
from decimal import Decimal, ROUND_CEILING, localcontext
from fractions import Fraction

_DEFAULT_DIGITS = 3
_ENCODER = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"))


def _fraction_literal(value: Fraction) -> str:
    denominator = value.denominator
    decimal_places = 0
    while denominator % 10 == 0:
        denominator //= 10
        decimal_places += 1
    # Mẫu số quyết định số chữ số cần để giữ nguyên thập phân hữu hạn.
    # Với số tuần hoàn, làm tròn lên để giá trị đúng ngưỡng sau các tick vẫn tươi.
    # Phần làm tròn nhỏ hơn khoảng cách 1 / (mẫu số * 240) tới ngưỡng mỗi tick.
    precision = max(17, decimal_places + denominator.bit_length() + 6)
    with localcontext(prec=precision, rounding=ROUND_CEILING):
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def _encode(value, key=None):
    if isinstance(value, dict):
        fields = (_object_key(k) + ":" + _encode(v, k) for k, v in value.items())
        return "{" + ",".join(fields) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_encode(v) for v in value) + "]"
    if isinstance(value, Fraction):
        if key == "fresh":
            return _fraction_literal(value)
        value = float(value)
    if isinstance(value, float):
        value = value if key == "fresh" else round(value, _DEFAULT_DIGITS)
        value = 0.0 if value == 0 else value  # tránh -0.0
    return _ENCODER.encode(value)


def _object_key(key):
    if key is None or isinstance(key, (int, float)):
        key = _ENCODER.encode(key)
    if not isinstance(key, str):
        raise TypeError(f"Unsupported JSON object key: {type(key).__name__}")
    return _ENCODER.encode(key)


def dumps(obj) -> str:
    return _encode(obj)


class JsonlWriter:
    def __init__(self, path: str):
        self._f = open(path, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self):
        self._f.close()
