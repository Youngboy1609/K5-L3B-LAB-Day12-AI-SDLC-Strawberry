"""Điểm vào headless: python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl

Mã thoát: 0 bình thường; 2 tham số/đầu vào sai (kiểm TRƯỚC khi ghi đầu ra); 1 lỗi chạy/ghi.
"""

import argparse
import os
import sys

from . import inventory as inventory_adapter
from .contract import effective_contract_version, load_contract
from .errors import BadInput
from .inputs import BUTTONS_V11, BUTTONS_V10, load_frames
from .inventory import KINDS_P2, ingredient_kinds, read_inventory
from .runner import run
from .scenario import load_scenario


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.headless")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])  # `day` có từ v1.1
    p.add_argument("--days", type=_int("days"))
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--ticks", required=True, type=_int("ticks"))
    p.add_argument("--out", required=True)
    p.add_argument("--scenario")
    p.add_argument("--inputs")
    p.add_argument("--inventory")
    p.add_argument("--inventory-out", dest="inventory_out")
    p.add_argument("--snapshot-every", dest="snapshot_every", type=_int("snapshot-every"), default=10)
    a = p.parse_args(argv)
    try:
        contract = load_contract()
        version = contract.get("contract_version", "1.0")
        runtime_version = effective_contract_version(version)
        if a.mode == "day" and runtime_version not in ("1.1", "1.2"):
            raise BadInput("--mode day chưa hỗ trợ ở contract v1.0 (có từ v1.1)")
        if a.mode == "day" and a.days is not None and not 1 <= a.days <= 5:
            raise BadInput("--days phải là số nguyên trong [1, 5]")
        if a.mode != "day" and a.days is not None:
            raise BadInput("--days chỉ dùng với --mode day")
        days = a.days or 1
        if a.ticks < 0:
            raise BadInput("--ticks phải >= 0")
        if a.snapshot_every <= 0:
            raise BadInput("--snapshot-every phải > 0")
        if a.mode == "day" and (a.inventory or a.inventory_out):
            raise BadInput("day không nhận cờ file kho --inventory/--inventory-out")
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        outs = [x for x in (a.out, a.inventory_out) if x]
        ins = [x for x in (a.scenario, a.inputs, a.inventory) if x]
        paths = [os.path.abspath(x) for x in outs + ins]
        if len(set(paths)) != len(paths):
            raise BadInput("các đường dẫn đầu vào/đầu ra phải khác nhau")
        if runtime_version == "1.2" and not hasattr(inventory_adapter, "validate_item_list"):
            raise BadInput("contract v1.2 cần adapter kho cá thể")
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning, runtime_version)
        frames = load_frames(a.inputs, buttons=BUTTONS_V11 if runtime_version in ("1.1", "1.2") else BUTTONS_V10,
                             allow_buy=(runtime_version in ("1.1", "1.2")))
        inventory = None
        if a.inventory:
            if runtime_version == "1.2":
                inventory = read_inventory(a.inventory, KINDS_P2, contract_version=runtime_version)
            else:
                inventory = read_inventory(a.inventory, ingredient_kinds(runtime_version))
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        run(a.mode, tuning, scenario, a.seed, frames, a.ticks, a.out, a.snapshot_every,
            inventory=inventory, inventory_out=a.inventory_out, contract_version=runtime_version, days=days)
    except BadInput as e:  # lỗi mức luật phát hiện lúc dựng sim
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
