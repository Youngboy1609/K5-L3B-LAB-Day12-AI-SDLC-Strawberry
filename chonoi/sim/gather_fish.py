"""Lát của Hạnh Phase 2 (`phase2/fish-and-tuning`): cá bơi và sinh đàn.

Vai trò gọi trong `step()` (Đăng Quang ghép, theo docs/plan/phase-2-tasks.md
mục "day → gather"): SAU bước bắt cá và khi vẫn còn giờ — tức trước chỉ kết
thúc `time` của tick. Hàm quản cá bơi: `sim.fish` (danh sách đàn), tạo đàn
mới qua `sim.ids` (IdAllocator) và mọi số ngẫu nhiên qua `sim.rng` (Streams) —
không dùng `random` toàn cục, không dùng đồng hồ hệ thống.

Về số chuẩn: bảng P2-01 (preset cá, tốc độ, lịch sinh) chưa chốt trên lab
board. Đến khi `game.contract.json` v1.1 có khóa `fish_motion`, cá giữ nguyên
hành vi v1.0 (đứng yên) nên không làm gãy regression P1; lịch sinh
(`fish_spawn`) đã chạy đầy đủ ngay khi khóa đó xuất hiện:

- `sim.t["fish_motion"]`: mapping theo kind:
    {"<kind>": {"speed_m_per_s": <số>}}   # heading_deg đã có trong đàn
  Khi có khóa này, mỗi đàn được tăng `age_ticks` mỗi bước (tuổi cá, dùng cho
  luật lớn lên/sinh theo bảng P2-01); chưa có thì cá đứng yên và không tính tuổi.
- `sim.t["fish_spawn"]`: lịch sinh:
    {"interval_s": <số>, "kinds": [<kind>, ...],
     "area": {"x": [lo, hi], "d": [lo, hi]}, "max": <số>}

Cá fixture (`random_fish: false`): ĐỨNG YÊN và không sinh — hành vi chốt từ
Phase 1, giữ nguyên. Gate cờ này nằm ở `step()` khi gọi `maybe_spawn_fish`.

Event phát ra (tên dùng chung với nhóm; payload chốt lại khi bảng P2-01 vào):
- `fish_spawned` {fish_id, kind, pos} khi sinh đàn mới.
- Cá bơi chỉ đổi trạng thái hiển thị qua snapshot, không phát event mỗi đàn.
"""

import math

from ..ids import sort_by_id


def advance_fish(sim, events):
    """Cá bơi một bước theo `heading_deg` + `speed_m_per_s`, đập biên bằng cách kẹp.

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
        dx = math.cos(rad) * speed / sim.tick_hz
        dd = math.sin(rad) * speed / sim.tick_hz
        if dx == 0.0 and dd == 0.0:
            continue
        f["pos"][0] = min(b["x"][1], max(b["x"][0], f["pos"][0] + dx))
        f["pos"][1] = min(b["d"][1], max(b["d"][0], f["pos"][1] + dd))
        changed = True
    return changed


def maybe_spawn_fish(sim, events):
    """Sinh đàn mới theo lịch `fish_spawn`. Mọi số lấy từ tuning, không đặt sẵn.

    Luật sinh (nội bộ hàm, cần thông báo với Quang khi ghép):
    - Đếm ngược riêng lưu trên `sim._fish_spawn_left` (khởi tạo lần gọi đầu =
      `interval_s * tick_hz`): về 0 thì sinh đúng một đàn rồi đếm lại từ đầu.
    - Chọn kind xoay vòng theo `sim._fish_spawn_idx` (bắt đầu từ 0).
    - Vị trí + hướng xuất phát: `sim.rng.get("fish")` (Streams) — tất định
      theo seed, không dùng `random` toàn cục.
    - ID: `sim.ids.new("F")` nối tiếp hậu tố đàn đã có (IdAllocator).
    - Đã đủ `max` đàn trong `sim.fish` thì thôi sinh.
    - Event: `("fish_spawned", {"fish_id", "kind", "pos"})`.

    Gate `random_fish: false` (fixture đứng yên, không sinh): đặt flag
    `sim._fish_spawn_allowed = False` ở nơi gọi (`step()` của Quang) hoặc khi
    dựng fixture trong `GatherSim.__init__`; mặc định True.

    Trả id đàn vừa sinh, hoặc None khi no-op (chưa có `fish_spawn` trong
    tuning, chưa tới lịch, hết hạn ngạch `max`, hoặc bị gate fixture).
    """
    cfg = sim.t.get("fish_spawn")
    if not cfg:
        return None
    if not getattr(sim, "_fish_spawn_allowed", True):
        return None
    if not hasattr(sim, "_fish_spawn_left"):
        sim._fish_spawn_left = int(round(float(cfg["interval_s"]) * sim.tick_hz))
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
    sim.fish.append({"id": fid, "pos": pos, "kind": kind,
                     "heading_deg": float(rng.uniform(0.0, 360.0)), "age_ticks": 0})
    sim._fish_spawn_idx += 1
    sim._fish_spawn_left = int(round(float(cfg["interval_s"]) * sim.tick_hz))
    events.append(("fish_spawned", {"fish_id": fid, "kind": kind, "pos": pos}))
    return fid
