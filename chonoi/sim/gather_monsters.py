"""Cá Sấu trong pha gather. Các khoảng cách dùng mét."""

import json
import math
from pathlib import Path

from ..errors import BadInput
from ..ids import sort_by_id


with Path(__file__).with_suffix(".json").open(encoding="utf-8") as source:
    DEFAULT_RULES = json.load(source)


def build_monsters(rules, scenario, day, bounds):
    routes = {r["id"]: r for r in rules["routes"]}
    fixtures = scenario.get("monsters", [
        {"id": key} for key, route in routes.items() if day >= route["from_day"]
    ])
    monsters = []
    seen = set()
    if not isinstance(fixtures, list):
        raise BadInput("monsters phải là mảng")
    for item in fixtures:
        key = item.get("id") if isinstance(item, dict) else None
        if not isinstance(key, str) or key not in routes or key in seen:
            raise BadInput("monsters có ID lạ hoặc trùng")
        seen.add(key)
        pos = item.get("pos", routes[key]["points"][0])
        state = item.get("state", "patrol")
        if (state not in ("patrol", "chase") or not isinstance(pos, list) or len(pos) != 2
                or not all(type(n) in (int, float) for n in pos)
                or not bounds["x"][0] <= pos[0] <= bounds["x"][1]
                or not rules["depth"][0] <= pos[1] <= rules["depth"][1]):
            raise BadInput("monsters có pos hoặc state không hợp lệ")
        monsters.append(dict(id=key, pos=list(pos), state=state, points=routes[key]["points"],
                             target=1, recoil_ticks=0, direction=(0, 0)))
    return sort_by_id(monsters)


def advance_monsters(sim, events):
    rules = sim.monster_rules
    shallow, deep = rules["depth"]
    left, right = sim.t["bounds"]["x"]
    closest = None
    best = math.inf
    for m in sim.monsters:
        x, d = m["pos"]
        if m["recoil_ticks"]:
            step = rules["recoil_distance"] / rules["recoil_ticks"]
            dx, dd = m["direction"]
            x += dx * step
            d += dd * step
            m["recoil_ticks"] -= 1
        else:
            distance = math.dist(m["pos"], sim.pos)
            radius = rules["escape_radius"] if m["state"] == "chase" else rules["detect_radius"]
            chase = sim.pos[1] >= shallow and distance <= radius
            m["state"] = "chase" if chase else "patrol"
            goal = sim.pos if chase else m["points"][m["target"]]
            distance = math.dist(m["pos"], goal)
            step = rules[m["state"] + "_speed"] / sim.tick_hz
            if distance <= step:
                x, d = goal
                if not chase:
                    m["target"] = 1 - m["target"]
            else:
                x += (goal[0] - x) * step / distance
                d += (goal[1] - d) * step / distance
        m["pos"] = [min(right, max(left, x)), min(deep, max(shallow, d))]
        distance = math.dist(m["pos"], sim.pos)
        if distance <= rules["hit_radius"] and distance < best:
            closest, best = m, distance

    if closest is None or sim.invuln_ticks:
        return
    direction = (1, 0)
    if best:
        direction = tuple((a - b) / best for a, b in zip(closest["pos"], sim.pos))
    closest["direction"] = direction
    closest["recoil_ticks"] = rules["recoil_ticks"]
    sim.invuln_ticks = rules["invuln_ticks"]
    sim.hp = max(0, sim.hp - rules["damage"])
    lost = [sim.hold.pop() for _ in range(len(sim.hold) // 2)]
    events.append(("hit", {"monster_id": closest["id"], "hp": sim.hp, "lost": lost}))
    if sim.hp == 0:
        sim._faint(events)
