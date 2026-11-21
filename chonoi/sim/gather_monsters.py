"""Cá Sấu trong pha gather. Các khoảng cách dùng mét."""

import json
import math
from pathlib import Path

from ..errors import BadInput
from ..ids import sort_by_id


with Path(__file__).with_suffix(".json").open(encoding="utf-8") as source:
    DEFAULT_RULES = json.load(source)


def _valid_position(pos, bounds):
    return (isinstance(pos, list) and len(pos) == 2
            and all(type(n) in (int, float) and math.isfinite(n) for n in pos)
            and all(lo <= n <= hi for n, (lo, hi) in zip(pos, bounds)))


def build_monsters(rules, scenario, day, bounds):
    routes = {route["id"]: route for route in rules["routes"]}
    fixtures = scenario.get("monsters", [
        {"id": ident} for ident, route in routes.items() if day >= route["from_day"]
    ])
    if not isinstance(fixtures, list):
        raise BadInput("monsters phải là mảng")
    lo = max(bounds["d"][0], rules["depth"][0])
    hi = min(bounds["d"][1], rules["depth"][1])
    habitat = (bounds["x"], [lo, hi])
    monsters = []
    seen = set()
    for item in fixtures:
        ident = item.get("id") if isinstance(item, dict) else None
        if not isinstance(ident, str) or not ident or ident in seen:
            raise BadInput("monsters cần ID duy nhất khác rỗng")
        seen.add(ident)
        route = routes.get(ident, {})
        kind = item.get("kind", "crocodile")
        waypoints = item.get("waypoints", route.get("points"))
        if (not isinstance(kind, str) or not kind
                or not isinstance(waypoints, list) or len(waypoints) != 2
                or not all(_valid_position(point, habitat) for point in waypoints)):
            raise BadInput(f"monsters.{ident}: kind hoặc waypoints không hợp lệ")
        pos = item.get("pos", waypoints[0])
        state = item.get("state", "patrol")
        target_idx = item.get("target_idx", 1)
        remaining = item.get("state_ticks_left", 0)
        direction = item.get("recoil_dir")
        timed = state in ("recoil", "stunned")
        if (not _valid_position(pos, habitat) or state not in ("patrol", "chase", "recoil", "stunned")
                or type(target_idx) is not int or target_idx not in (0, 1)
                or type(remaining) is not int or remaining < (1 if timed else 0)
                or (not timed and remaining != 0)):
            raise BadInput(f"monsters.{ident}: vị trí, trạng thái hoặc timer không hợp lệ")
        if state == "recoil":
            if (not _valid_position(direction, ([-1, 1], [-1, 1]))
                    or not math.isclose(math.hypot(*direction), 1, abs_tol=1e-6)):
                raise BadInput(f"monsters.{ident}: recoil_dir phải là vector đơn vị")
        elif direction is not None:
            raise BadInput(f"monsters.{ident}: recoil_dir chỉ dùng trong recoil")
        monsters.append(dict(id=ident, kind=kind, pos=list(pos), waypoints=waypoints, target_idx=target_idx,
                             state=state, state_ticks_left=remaining, recoil_dir=direction))
    return sort_by_id(monsters)


def advance_monsters(sim, events):
    rules = sim.monster_rules
    shallow, deep = rules["depth"]
    left, right = sim.t["bounds"]["x"]
    bottom, top = sim.t["bounds"]["d"]
    deep = min(deep, top)
    closest = None
    best = math.inf
    for m in sim.monsters:
        x, d = m["pos"]
        if m["state"] in ("recoil", "stunned"):
            if m["state"] == "recoil":
                step = rules["recoil_distance"] / rules["recoil_ticks"]
                dx, dd = m["recoil_dir"]
                x += dx * step
                d += dd * step
            m["state_ticks_left"] -= 1
            if m["state_ticks_left"] == 0:
                m["state"] = "patrol"
                m["recoil_dir"] = None
            m["pos"] = [min(right, max(left, x)), min(deep, max(shallow, bottom, d))]
            continue
        else:
            distance = math.dist(m["pos"], sim.pos)
            radius = rules["escape_radius"] if m["state"] == "chase" else rules["detect_radius"]
            chase = sim.pos[1] >= shallow and distance <= radius
            m["state"] = "chase" if chase else "patrol"
            goal = sim.pos if chase else m["waypoints"][m["target_idx"]]
            distance = math.dist(m["pos"], goal)
            step = rules[m["state"] + "_speed"] / sim.tick_hz
            if distance <= step:
                x, d = goal
                if not chase:
                    m["target_idx"] = 1 - m["target_idx"]
            else:
                x += (goal[0] - x) * step / distance
                d += (goal[1] - d) * step / distance
        m["pos"] = [min(right, max(left, x)), min(deep, max(shallow, bottom, d))]
        distance = math.dist(m["pos"], sim.pos)
        if sim.pos[1] >= shallow and distance <= rules["hit_radius"] and distance < best:
            closest, best = m, distance

    if closest is None or sim.invuln_ticks:
        return
    direction = (1, 0)
    if best:
        direction = tuple((a - b) / best for a, b in zip(closest["pos"], sim.pos))
    closest["state"] = "recoil"
    closest["recoil_dir"] = list(direction)
    closest["state_ticks_left"] = rules["recoil_ticks"]
    sim.invuln_ticks = rules["invuln_ticks"]
    sim.hp = max(0, sim.hp - rules["damage"])
    lost = [sim.hold.pop() for _ in range(len(sim.hold) // 2)]
    events.append(("monster_hit", {"monster_id": closest["id"], "hp": sim.hp,
                                   "lost": sim.hold_payload(lost)}))
    if sim.hp == 0:
        sim._faint(events)
