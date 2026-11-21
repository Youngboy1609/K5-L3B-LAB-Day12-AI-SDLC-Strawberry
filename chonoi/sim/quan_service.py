"""Buổi tối — lát 4: bếp, bưng, phục vụ, tiền, uy tín, đóng ca (PRD-0 mục F).

Chủ file: Nguyễn Ngọc Quang (`shoxieje`). Nghĩa nối ba hàm vào `QuanSim.step()` theo thứ tự đã chốt
(docs/plan/phase-1-tasks.md):

    time_left -1, giảm kiên nhẫn khách chờ, giảm eat_ticks khách đang ăn   (Nghĩa)
    advance_stoves(sim, events)                                              (lát 4)
    _move(inp)
    if inp.pressed("interact"): interact(sim, events)                        (lát 4)
    settle_customers(sim, events)   # thu tiền, khách bỏ đi, dọn món, quan_end (lát 4)
    sinh khách cuối tick nếu not sim.done                                    (Nghĩa)

Thứ tự này cho phép giao món đúng tick kiên nhẫn về 0 hoặc tick hết ca.

Hợp đồng dữ liệu với lát 3 (khách). Một khách = một đơn:
    id, table_id, dish_id
    order_status     "reserved" | "assigned" | "served" | "unfulfillable"
    state            "waiting" | "eating"
    reserved         {kind: n}, chỉ khác rỗng khi order_status == "reserved"
    order_tick       tick gọi món (chọn đơn reserved cũ nhất, hòa thì theo id bàn)
    patience_ticks_left, eat_ticks_left, base_price, tip
Payload món ở bếp và trên tay: {"order_id", "dish_id", "base_price"}. order_id là id khách.
Giá lấy từ menu khi bắt đầu nấu. settle_customers phát quan_end (một lần) sau khi dọn ca, kèm báo cáo
ca `sim.shift` (chỉ mode `day`): served, paid, left (hết kiên nhẫn), left_closing (rời lúc đóng ca), tips.

Số liệu chỉ đọc từ tuning (`sim.t`, `sim.menu`); không dùng ngẫu nhiên.
"""

import math
from fractions import Fraction

from ..ids import id_key, sort_by_id
from ..inventory import item_payload

TICK_HZ = 60


def _ticks(seconds) -> int:
    return int(round(seconds * TICK_HZ))


def _clamp_rep(sim, value):
    # Làm tròn để cộng dồn 0.2/-0.5 không trôi số thực (2.0 thành 1.9999… làm floor() mất 100 điểm).
    return round(min(sim.t["reputation_max"], max(sim.t["reputation_min"], value)), 9)


def _dish_payload(d) -> dict:
    return {"order_id": d["order_id"], "dish_id": d["dish_id"]}


# ---------------------------------------------------------------------------------------------
# Bếp
# ---------------------------------------------------------------------------------------------

def advance_stoves(sim, events):
    """Giảm timer nấu; món đã `ready` từ đầu tick tăng ready_ticks; món vừa chín -> `ready` + dish_ready."""
    for s in sim.stoves:  # sim.stoves đã sort theo id
        if s["state"] == "ready":
            s["ready_ticks"] += 1
        elif s["state"] == "cooking":
            s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)
            if s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", {"stove_id": s["id"], **_dish_payload(s["dish"])}))
    # burn_s = null ở preset v1.0 -> không có món cháy trong Phase 1.


# ---------------------------------------------------------------------------------------------
# Tương tác
# ---------------------------------------------------------------------------------------------

def _pick_target(sim):
    """Một đối tượng trong bán kính (tính cả mép): khoảng cách nhỏ nhất, bếp trước bàn, rồi id."""
    px, pz = sim.pos
    r = sim.t["interact_radius"]
    best = None
    for kind_rank, kind, objs in ((0, "stove", sim.stoves), (1, "table", sim.tables)):
        for o in objs:
            d = math.hypot(o["pos"][0] - px, o["pos"][1] - pz)
            if d <= r:
                key = (d, kind_rank, id_key(o["id"]))
                if best is None or key < best[0]:
                    best = (key, kind, o)
    return (best[1], best[2]) if best else (None, None)


def interact(sim, events):
    """Tối đa MỘT hành động mỗi cạnh lên `interact`. Đối tượng không có việc gì -> bỏ qua."""
    kind, obj = _pick_target(sim)
    if kind == "stove":
        _interact_stove(sim, obj, events)
    elif kind == "table":
        _interact_table(sim, obj, events)


def _oldest_reserved(sim):
    waiting = [c for c in sim.customers if c["order_status"] == "reserved"]
    if not waiting:
        return None
    return min(waiting, key=lambda c: (c["order_tick"], id_key(c["table_id"])))


def _interact_stove(sim, s, events):
    if s["state"] == "idle":
        c = _oldest_reserved(sim)
        if c is None:
            return
        # Tồn vật lý CHỈ đổi ở đây: trừ đúng phần giữ, một lần.
        reserved = c["reserved"]
        c["order_status"] = "assigned"
        dish = sim.menu[c["dish_id"]]
        if sim.item_stock:
            by_id = sim.stock_by_id
            items = [by_id[ident] for ident in reserved]
            sim.stock[:] = [item for item in sim.stock if item["id"] not in set(reserved)]
            c["reserved"] = []
            price = (dish["price"] * sum((item["fresh"] for item in items), Fraction()) /
                     (100 * len(items))).__floor__()
            payload_items = [item_payload(item) for item in sorted(items, key=lambda item: (item["kind"], id_key(item["id"]))) ]
        else:
            for k, n in reserved.items():
                sim.stock[k] -= n
                assert sim.stock[k] >= 0, f"phần giữ {k} vượt tồn — fixture phải bị chặn mã 2"
                if sim.stock[k] == 0:
                    sim.stock.pop(k)
            c["reserved"] = {}
            items = [kind for kind in sorted(reserved) for _ in range(reserved[kind])]
            price = dish["price"]
            payload_items = items
        s["dish"] = {"order_id": c["id"], "dish_id": c["dish_id"], "base_price": price}
        s["state"] = "cooking"
        s["cook_ticks_left"] = _ticks(dish["cook_s"])
        s["ready_ticks"] = 0
        data = {"stove_id": s["id"], "customer_id": c["id"], **_dish_payload(s["dish"]), "items": payload_items,
                "cook_ticks": s["cook_ticks_left"]}
        if sim.item_stock:
            data["base_price"] = price
        events.append(("cook_started", data))
    elif s["state"] == "ready":
        if sim.hand is not None:  # tay chứa đúng một món (carry_limit = 1 ở v1.0)
            return
        sim.hand = s["dish"]
        s["dish"] = None
        s["state"] = "idle"
        s["cook_ticks_left"] = 0
        s["ready_ticks"] = 0
        events.append(("dish_picked", {"stove_id": s["id"], **_dish_payload(sim.hand)}))
    # cooking: chưa xong, không làm gì.


def _interact_table(sim, tb, events):
    c = next((c for c in sim.customers if c["table_id"] == tb["id"]), None)
    if c is None or sim.hand is None or c.get("state", "waiting") != "waiting":
        return
    if sim.hand["order_id"] != c["id"]:  # bàn chỉ nhận đúng đơn của mình
        return
    patience_total = _ticks(sim.t["patience_s"])
    left = c["patience_ticks_left"]
    price = sim.hand["base_price"]
    tip = 0
    if patience_total > 0 and left / patience_total >= sim.t["tip_min_patience_ratio"]:
        tip = math.floor(price * sim.t["tip_rate"])
    c["state"] = "eating"
    c["order_status"] = "served"
    c["eat_ticks_left"] = _ticks(sim.t["eat_s"])
    c["base_price"] = price
    c["tip"] = tip
    sim.shift["served"] += 1
    dish = sim.hand
    sim.hand = None
    events.append(("served", {"order_id": dish["order_id"], "table_id": tb["id"], "dish_id": dish["dish_id"],
                              "patience_ticks_left": left, "base_price": price, "tip": tip}))


# ---------------------------------------------------------------------------------------------
# Thu tiền, khách bỏ đi, đóng ca
# ---------------------------------------------------------------------------------------------

def _pay(sim, c, events, reason):
    amount = c["base_price"] + c["tip"]
    sim.money += amount
    sim.earned += amount
    sim.shift_earned += amount
    sim.shift["paid"] += 1
    sim.shift["tips"] += c["tip"]
    if c["tip"] > 0:
        sim.reputation = _clamp_rep(sim, sim.reputation + sim.t["tip_reputation"])
    events.append(("paid", {"order_id": c["id"], "table_id": c["table_id"], "base_price": c["base_price"],
                            "tip": c["tip"], "amount": amount, "reason": reason}))


def _discard_order_dishes(sim, order_id, events):
    """Dọn món thuộc đơn ở bếp hoặc trên tay. Không hoàn nguyên liệu đã nấu."""
    for s in sim.stoves:
        if s["dish"] is not None and s["dish"]["order_id"] == order_id:
            events.append(("dish_discarded", {"where": s["id"], **_dish_payload(s["dish"])}))
            s.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)
    if sim.hand is not None and sim.hand["order_id"] == order_id:
        events.append(("dish_discarded", {"where": "hand", **_dish_payload(sim.hand)}))
        sim.hand = None


def _remove(sim, c, events):
    c["reserved"] = [] if sim.item_stock else {}  # nhả phần giữ thô (tồn vật lý không đổi)
    _discard_order_dishes(sim, c["id"], events)
    sim.customers.remove(c)


def settle_customers(sim, events):
    """Sau interact: khách ăn xong trả tiền, khách chờ hết kiên nhẫn bỏ đi; hết ca thì đóng quán."""
    closing = sim.time_left_ticks == 0
    for c in sort_by_id(sim.customers, key=lambda customer: customer["table_id"]):
        if c["state"] == "eating":
            if c["eat_ticks_left"] > 0 and not closing:
                continue
            _pay(sim, c, events, "finished_eating" if c["eat_ticks_left"] == 0 else "closing")
        else:
            if c["patience_ticks_left"] > 0 and not closing:
                continue
            sim.shift["left_closing" if closing else "left"] += 1
            if not closing:
                sim.reputation = _clamp_rep(sim, sim.reputation + sim.t["left_reputation_delta"])
            events.append(("customer_left", {"customer_id": c["id"], "table_id": c["table_id"],
                                             "order_id": c["id"], "reason": "closing" if closing else "patience",
                                             "reputation": sim.reputation}))
        _remove(sim, c, events)

    if closing:
        sim.done = True
        sim.reason = "time"
        events.append(("quan_end", {"reason": "time", "money": sim.money, "earned": sim.earned,
                                    "shift_earned": sim.shift_earned, "reputation": sim.reputation,
                                    **(dict(sim.shift) if sim.day_mode else {})}))
