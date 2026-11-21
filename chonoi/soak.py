"""Chạy soak nhiều Ngày với cùng phiên headless và ghi thống kê lúc Shop đóng."""

import argparse
import json
import math
import sys
from time import perf_counter

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import DaySession


IDLE = InputState((0, 0), {}, set())
INTERACT = InputState((0, 0), {"interact": True}, {"interact"})


def _bot_input(sim):
    # Hái một lượt rồi cập bến để ca soak thật sự bàn giao cá thể mỗi Ngày.
    if sim.phase != "gather":
        return IDLE
    gather = sim.phase_sim
    if gather.hold:
        target, radius = gather.t["dock_pos"], gather.t["dock_radius"]
    else:
        target, radius = gather.nodes[0]["pos"], gather.t["interact_radius"]
    dx, depth = (goal - actual for goal, actual in zip(target, gather.pos))
    distance = math.hypot(dx, depth)
    if distance <= radius / 2:
        return INTERACT
    return InputState((dx / distance, depth / distance), {}, set())


def run_soak(tuning, seed, days):
    started = perf_counter()
    session = DaySession(tuning, {}, seed, days, contract_version="1.2", repeat_day_plans=True)
    tick_hz = tuning["tick_hz"]
    phase_ticks = sum(round(tuning[phase]["duration_s"] * tick_hz) for phase in ("gather", "quan"))
    limit = days * (phase_ticks + session.sim.shop_duration)
    results = []
    crashes = 0
    try:
        while not session.done and session.tick < limit:
            for row in session.step(_bot_input(session.sim)):
                if row["name"] == "shop_end":
                    state = session.end_row()
                    results.append({"day": row["day"], "earned": state["earned"],
                                    "reputation": state["reputation"], "score": state["score"]})
    except Exception as error:
        print(f"soak dừng ở Ngày {session.sim.day}, tick {session.tick}: {error}", file=sys.stderr)
        crashes = 1
    return {"days": days, "days_completed": len(results), "crashes": crashes, "results": results,
            "duration_s": perf_counter() - started}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.days < 1:
            raise BadInput("--days phải là số nguyên dương")
        contract = load_contract()
        if contract.get("contract_version") not in ("1.2", "1.3"):
            raise BadInput("soak cần schema kho cá thể v1.2 trở lên")
        report = run_soak(contract["tuning"], args.seed, args.days)
        with open(args.out, "w", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False, indent=2)
            output.write("\n")
    except BadInput as error:
        print(f"đầu vào sai: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"lỗi ghi báo cáo soak: {error}", file=sys.stderr)
        return 1
    return 0 if report["days_completed"] == args.days and report["crashes"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
