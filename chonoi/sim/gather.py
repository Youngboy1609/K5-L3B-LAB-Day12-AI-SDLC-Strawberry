"""Buổi sáng — Lặn & Hái (`gather`).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Mỗi tick chạy bộ đếm, nút mọc lại, di chuyển và sinh tồn, rồi mới xét cập bến,
hái, bắt cá và hết giờ. Khi ngất, đồ rơi theo thứ tự nhặt mới nhất trước và giỏ
rỗng trước khi kết thúc lượt. Runner ghi file kho khi lượt kết thúc.
"""

import math
from fractions import Fraction

from ..ids import sort_by_id
from ..inventory import (decay_items, hold_to_items, ingredient_kinds,
                         item_payload, new_item, validate_item_list)
from .gather_actions import advance_nodes, try_catch, try_harvest
from .gather_fish import advance_fish as move_fish, maybe_spawn_fish
from .gather_monsters import DEFAULT_RULES, advance_monsters, build_monsters
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, *, day=None, advance_fish=move_fish,
                 contract_version="1.1", freshness=None):
        t = tuning["gather"]
        self.t = t
        self.item_hold = contract_version == "1.2"
        self.phase2 = day is not None or self.item_hold
        self.tick_hz = tuning["tick_hz"]
        self.advance_fish = advance_fish
        self._fish_spawn_allowed = scenario.get("random_fish", True)
        self.monster_rules = t.get("monster_rules", DEFAULT_RULES)
        self.monsters = build_monsters(self.monster_rules, scenario, day or 1, t["bounds"]) if self.phase2 else []
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        if self.item_hold:
            rules = tuning["freshness"] if freshness is None else freshness
            self.initial_fresh = rules["initial"]
            self.spoiled_below = Fraction(str(rules["spoiled_below"]))
            self.fresh_decay = Fraction(str(rules["gather_decay_per_s"])) / self.tick_hz
            self.hold = validate_item_list(self.hold, ingredient_kinds(contract_version))
            for item in self.hold:
                ids.reserve(item["id"])
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif self._fish_spawn_allowed:
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        self.fish = [{"id": f["id"], "pos": [float(c) for c in f["pos"]], "kind": f["kind"],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        if self.phase2:
            for fish, source in zip(self.fish, src_fish):
                fish["age_ticks"] = source.get("age_ticks", 0)
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict | list:
        if self.item_hold:
            return [dict(item) for item in self.hold]
        return hold_to_items(self.hold)

    def add_to_hold(self, kind, count):
        if self.item_hold:
            self.hold.extend(new_item(self.ids, kind, self.initial_fresh) for _ in range(count))
        else:
            self.hold.extend([kind] * count)

    def hold_payload(self, items):
        return [item_payload(item) for item in items] if self.item_hold else items

    def _decay_hold(self, events):
        fresh_ids = {item["id"] for item in self.hold if item["fresh"] >= self.spoiled_below}
        spoiled = decay_items(self.hold, self.fresh_decay, self.spoiled_below)
        for item in self.hold:
            item["fresh"] = max(Fraction(0), item["fresh"])
        for item in spoiled:
            if item["id"] in fresh_ids:
                events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": "hold"}))

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold_payload(self.hold), "hold_count": len(self.hold),
            **({"monsters": [dict(m) for m in self.monsters]} if self.phase2 else {}),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [dict(f) for f in sort_by_id(self.fish)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        advance_nodes(self, events)
        if self.item_hold:
            self._decay_hold(events)
        # 2. bơi, chặn mép và sinh tồn
        was_at_surface = self._at_surface()
        self._move(inp)
        self._update_survival(was_at_surface, events)
        if not self.done:
            advance_monsters(self, events)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                try_harvest(self, events)
        # 4. bắt cá
        if inp.pressed("catch"):
            try_catch(self, events)
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        elif self.phase2 and self._fish_spawn_allowed:
            if self.advance_fish is not None:
                self.advance_fish(self, events)
            maybe_spawn_fish(self, events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _update_survival(self, was_at_surface, events):
        at_surface = self._at_surface()
        if at_surface != was_at_surface:
            name = "surface" if at_surface else "dive"
            events.append((name, {"pos": self.pos.copy()}))

        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks > 0:
                return
            events.append(("oxygen_empty", {}))

        # Tick vừa cạn oxy cũng là tick đầu tiên tính ngạt.
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < self.t["choke_interval_ticks"]:
            return

        self.zero_oxy_ticks = 0
        self.hp -= 1
        events.append(("choke", {"hp": self.hp}))
        if self.hp == 0:
            self._faint(events)

    def _faint(self, events):
        lost = self.hold[::-1]
        self.hold.clear()
        events.append(("faint", {"lost": self.hold_payload(lost)}))
        self._finish("fainted", events)

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        items = self.inventory_items()
        if self.item_hold:
            items = self.hold_payload(sort_by_id(items))
        events.append(("gather_end", {"reason": reason, "inventory": {"items": items}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
