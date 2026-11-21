"""Lát 2 của `gather`: mọc lại nút, hái nút, bắt đàn cá.

Ba hàm nhận `(sim, events)` chốt với Quang trong kickoff Phase 1 (xem
`docs/standup.md`, mục "Chốt hợp đồng gather_actions"):

1. `advance_nodes` gánh bộ đếm `regrow_ticks` + event `node_regrown`; khi ghép,
   `GatherSim.step()` thay vòng lặp cũ bằng đúng một lời gọi hàm này. Nút vừa
   mọc (về 0 trong tick) hái được ngay trong tick đó vì bước hái chạy sau.
2. `step()` giảm `catch_cd_ticks` đầu tick; `try_catch` chỉ ĐẶT lại hồi chiêu
   khi bắt thành công, không tự giảm.
3. `step()` gate lệnh E: xét cập bến trước, rồi kiểm tra đang ở mặt nước sau
   khi di chuyển trước khi gọi `try_harvest` — hàm này không kiểm lại.
4. Thiếu chỗ cho toàn bộ sản lượng: phát `hold_full` đúng một lần, giữ nguyên
   nút/đàn (vẫn `ready`) và giữ nguyên hồi chiêu (không đặt, không hủy).
5. Thứ tự gọi trong `step()`: giảm bộ đếm -> `advance_nodes` -> di chuyển -> oxy
   -> cập bến -> `try_harvest` -> `try_catch` -> hết giờ. Lượt bắt hợp lệ ở tick
   cuối, trước kiểm hết giờ, vẫn được tính vào kho khi `gather_end`.

Chọn đối tượng: gần nhất trong bán kính; bằng khoảng cách -> id nhỏ hơn thắng
(dùng thứ tự `ids.sort_by_id`, quét tuyến tính giữ phần tử đầu tiên khi hòa).
Mép bán kính (đúng bằng bán kính) tính là trong. Số liệu đọc từ tuning, không
hard-code.
"""

import math

from ..ids import sort_by_id

TICK = 60.0  # trùng chonoi.sim.gather; không import ngược để tránh vòng


def advance_nodes(sim, events):
    """Giảm timer mọc lại theo ID; nút về 0 phát `node_regrown` {node_id}."""
    for n in sort_by_id(sim.nodes):
        if n["regrow_ticks"] > 0:
            n["regrow_ticks"] -= 1
            if n["regrow_ticks"] == 0:
                events.append(("node_regrown", {"node_id": n["id"]}))


def try_harvest(sim, events):
    """Hái nút `ready` gần nhất trong `interact_radius` (đã ở mặt nước do step() gate).

    Event: `gather` {node_id, kind, count} khi hái được, hoặc `hold_full` khi
    giỏ không đủ chỗ cho toàn bộ sản lượng (xem chú thích payload ở file head).
    """
    node, best_d = None, None
    for n in sort_by_id(sim.nodes):
        if n["regrow_ticks"] > 0:
            continue
        d = math.dist(sim.pos, n["pos"])
        if d <= sim.t["interact_radius"] and (best_d is None or d < best_d):
            node, best_d = n, d
    if node is None:
        return False
    count = int(sim.t["node_yield"])
    if len(sim.hold) + count > sim.t["hold_capacity"]:
        events.append(("hold_full", {"hold_count": len(sim.hold),
                                     "hold_capacity": sim.t["hold_capacity"]}))
        return False
    for _ in range(count):
        sim.hold.append(node["kind"])
    node["regrow_ticks"] = int(round(sim.t["regrow_s"] * TICK))
    events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "count": count}))
    return True


def try_catch(sim, events):
    """Bắt đàn gần nhất trong `catch_radius`, chỉ khi `catch_cd_ticks == 0` và đang dưới nước.

    Đủ chỗ: thêm toàn bộ `fish_yield[kind]` vào giỏ, đặt lại hồi chiêu
    `catch_cooldown_s * TICK`, phát `fish_caught` {fish_id, kind, count}.
    Thiếu chỗ: phát `hold_full`, giữ nguyên đàn, KHÔNG đặt hồi chiêu.
    """
    if sim.catch_cd_ticks > 0:
        return False
    if sim.pos[1] <= sim.t["surface_depth"]:
        return False  # phải đang dưới nước
    fish, best_d = None, None
    for f in sort_by_id(sim.fish):
        d = math.dist(sim.pos, f["pos"])
        if d <= sim.t["catch_radius"] and (best_d is None or d < best_d):
            fish, best_d = f, d
    if fish is None:
        return False
    count = int(sim.t["fish_yield"][fish["kind"]])
    if len(sim.hold) + count > sim.t["hold_capacity"]:
        events.append(("hold_full", {"hold_count": len(sim.hold),
                                     "hold_capacity": sim.t["hold_capacity"]}))
        return False
    for _ in range(count):
        sim.hold.append(fish["kind"])
    sim.catch_cd_ticks = int(round(sim.t["catch_cooldown_s"] * TICK))
    events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "count": count}))
    return True
