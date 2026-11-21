"""Lát của Hạnh Phase 2 (`phase2/fish-and-tuning`): cá bơi, tuổi cá và sinh đàn.

Điểm nối với vòng tick đã ghép trên main (chonoi/sim/gather.py): `GatherSim`
nhận `advance_fish=` (một hàm `(sim, events)`) và gọi nó ở CUỐI mỗi bước,
chỉ khi vẫn còn giờ — đúng chỗ "sau bước bắt cá và khi còn giờ" của
docs/plan/phase-2-tasks.md. Hàm vào của lát này là `advance_fish` cùng chữ số,
sẵn sàng truyền như sau (một dòng, thuộc file của Đăng Quang / Nghĩa — báo
chủ file khi ghép):

    from .gather_fish import advance_fish as fish_rules
    GatherSim(tuning, scenario, streams, ids, day=day, advance_fish=fish_rules)

Mọi số cho cá đọc từ `sim.t` tuning, không đặt sẵn giá trị nào (bảng chuẩn
P2-01 chờ trên lab board — docs/clarify.md):

- `sim.t["fish_motion"]`: mapping theo kind, tùy chọn. Có khóa này, mỗi đàn
  bơi theo `heading_deg` + `speed_m_per_s` (kẹp biên) và tăng `age_ticks`
  mỗi bước (tuổi cá cho luật lớn lên/sinh). Chưa có thì cá đứng yên — hành vi
  v1.0, không gãy regression P1.
- `sim.t["fish_spawn"]`: lịch sinh, tùy chọn:
    {"interval_s": <số>, "kinds": [<kind>, ...],
     "area": {"x": [lo, hi], "d": [lo, hi]}, "max": <số>}

Cá fixture (`random_fish: false`): ĐỨNG YÊN và không sinh — không có cấu hình
`fish_motion`/`fish_spawn` cho fixture, hoặc nhẹ hơn: nơi dựng sim (Quang)
đặt `sim._fish_spawn_allowed = False` / chọn không truyền `advance_fish`.

Mọi số ngẫu nhiên qua `sim.rng.get("fish")` (Streams) — tất định theo seed;
không dùng `random` toàn cục, không dùng đồng hồ hệ thống. ID đàn mới qua
`sim.ids.new("F")` (IdAllocator, nối tiếp hậu tố đàn đã có).

Event: `fish_spawned` {fish_id, kind, pos} khi sinh đàn mới. Cá bơi chỉ đổi
trạng thái hiển thị qua snapshot, không phát event mỗi đàn.
"""

import math

from ..ids import sort_by_id

TICK = 60.0  # trùng chonoi.sim.gather; nếu v1.1 đổi tick_hz thì đọc từ tuning


def advance_fish(sim, events):
    """Điểm vào duy nhất theo rãnh `GatherSim(..., advance_fish=...)` trên main.

    Gồm: cá bơi một bước (`move_fish`) rồi xét lịch sinh (`spawn_fish`).
    Fixture (`random_fish: false`, tín hiệu qua `sim._fish_spawn_allowed=False`)
    bỏ qua cả hai — cá đứng yên đúng spec. Trả id đàn sinh mới (hoặc None).
    """
    if not getattr(sim, "_fish_spawn_allowed", True):
        return None
    move_fish(sim, events)
    return spawn_fish(sim, events)


def move_fish(sim, events):
    """Cá bơi một bước theo `heading_deg` + `speed_m_per_s`, đập biên bằng kẹp.

    Trả True nếu có đàn nào chuyển vị trí; False khi no-op (chưa có
    `fish_motion` trong tuning, hoặc kind không có cấu hình).
    """
    cfg = sim.t.get("fish_motion")
    if not cfg:
        return False
    b = sim.t["bounds"]
    changed = False
    for f in sort_by_id(sim.fish):
        spec = cfg.get(f["kind"])
        if not spec:
            continue
        speed = float(spec["speed_m_per_s"])
        rad = math.radians(f.get("heading_deg", 0.0))
        f["age_ticks"] = f.get("age_ticks", 0) + 1
        dx = math.cos(rad) * speed / TICK
        dd = math.sin(rad) * speed / TICK
        if dx == 0.0 and dd == 0.0:
            continue
        f["pos"][0] = min(b["x"][1], max(b["x"][0], f["pos"][0] + dx))
        f["pos"][1] = min(b["d"][1], max(b["d"][0], f["pos"][1] + dd))
        changed = True
    return changed


def spawn_fish(sim, events):
    """Sinh đàn mới theo lịch `fish_spawn`. Mọi số lấy từ tuning, không đặt sẵn.

    Luật sinh (nội bộ hàm, cần thông báo với Quang khi ghép):
    - Đếm ngược riêng lưu trên `sim._fish_spawn_left` (khởi tạo lần gọi đầu =
      `interval_s * TICK`): về 0 thì sinh đúng một đàn rồi đếm lại từ đầu.
    - Chọn kind xoay vòng theo `sim._fish_spawn_idx` (bắt đầu từ 0).
    - Vị trí + hướng xuất phát: `sim.rng.get("fish")` (Streams) — tất định
      theo seed, không dùng `random` toàn cục.
    - ID: `sim.ids.new("F")` nối tiếp hậu tố đàn đã có (IdAllocator).
    - Đã đủ `max` đàn tổng trong `sim.fish` thì thôi sinh.
    - Event: `("fish_spawned", {"fish_id", "kind", "pos"})`.

    Gate `random_fish: false` (fixture đứng yên, không sinh): đặt flag
    `sim._fish_spawn_allowed = False` ở nơi dựng sim/gọi (Quang); mặc định True.

    Trả id đàn vừa sinh, hoặc None khi no-op (chưa có `fish_spawn` trong
    tuning, chưa tới lịch, hết hạn ngạch `max`, hoặc bị gate fixture).
    """
    cfg = sim.t.get("fish_spawn")
    if not cfg:
        return None
    if not getattr(sim, "_fish_spawn_allowed", True):
        return None
    if not hasattr(sim, "_fish_spawn_left"):
        sim._fish_spawn_left = int(round(float(cfg["interval_s"]) * TICK))
        sim._fish_spawn_idx = 0
    if len(sim.fish) >= int(cfg["max"]):
        return None
    if sim._fish_spawn_left > 0:
        sim._fish_spawn_left -= 1
        if sim._fish_spawn_left > 0:
            return None
        # biến đếm vừa về 0 ở bước này -> sinh ngay trong bước, rồi khởi đếm lại

    kind = cfg["kinds"][sim._fish_spawn_idx % len(cfg["kinds"])]
    area = cfg["area"]
    rng = sim.rng.get("fish")
    pos = [float(rng.uniform(area["x"][0], area["x"][1])),
           float(rng.uniform(area["d"][0], area["d"][1]))]
    fid = sim.ids.new("F")
    sim.fish.append({"id": fid, "kind": kind, "pos": pos,
                     "heading_deg": float(rng.uniform(0.0, 360.0)), "age_ticks": 0})
    sim._fish_spawn_idx += 1
    sim._fish_spawn_left = int(round(float(cfg["interval_s"]) * TICK))
    events.append(("fish_spawned", {"fish_id": fid, "kind": kind, "pos": pos}))
    return fid
