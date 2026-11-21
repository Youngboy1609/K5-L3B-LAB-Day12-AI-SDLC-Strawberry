"""Vòng tick (Contract B, mô hình tick). KHUNG — thường không cần sửa.

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math
import os
import tempfile

from .ids import IdAllocator
from .inputs import BUTTONS_V11, InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim
from .sim.day import DaySim


def build_sim(mode, tuning, scenario, seed, inventory, *, contract_version="1.0"):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        if contract_version == "1.2":
            return GatherSim(tuning, scenario, streams, ids, day=1, contract_version=contract_version)
        return GatherSim(tuning, scenario, streams, ids, day=1 if contract_version == "1.1" else None)
    return QuanSim(tuning, scenario, streams, ids, inventory=inventory, contract_version=contract_version)


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, *, contract_version="1.0"):
        self.mode = mode
        self.tuning = tuning
        self.contract_version = contract_version
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, contract_version=contract_version)
        self.tick = 0
        self.initial_events = [{"type": "event", "tick": 0, "phase": mode, "name": name, "data": data}
                               for name, data in getattr(self.sim, "initial_events", ())]

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        s = _common(self.sim, self.tick, self.tick, self.tick, self.tuning, "finished" if self.sim.done else "playing")
        s.update(self.sim.snapshot())
        return s

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event (tick = k + 1)."""
        events = self.sim.step(inp)
        self.tick += 1
        return [{"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
                for name, data in events]

    def end_row(self) -> dict:
        sim = self.sim
        score = _common(sim, self.tick, self.tick, self.tick, self.tuning, "")["score"]
        return {"type": "end", "ticks": self.tick, "sim_tick": self.tick, "mode": sim.mode,
                "state": "finished" if sim.done else "playing",
                "reason": sim.reason if sim.done else "tick_limit",
                "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score}

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            items = self.sim.inventory_items()
            if self.contract_version == "1.2":
                write_inventory(inventory_out, items, contract_version=self.contract_version)
            else:
                write_inventory(inventory_out, items)


class V11Session(Session):
    """v1.1 single-mode session: pause advances wall ticks while simulation clocks stop."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, *, contract_version="1.1"):
        super().__init__(mode, tuning, scenario, seed, inventory, contract_version=contract_version)
        self.sim_tick = 0
        self.phase_tick = 0
        self.paused = False

    def snapshot(self):
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning,
                    "paused" if self.paused else ("finished" if self.sim.done else "playing"))
        s.update(self.sim.snapshot())
        return s

    def step(self, inp):
        self.tick += 1
        if inp.pressed("pause"):
            self.paused = not self.paused
            pause_event = {"type": "event", "tick": self.tick, "phase": self.sim.phase,
                           "name": "paused" if self.paused else "resumed", "data": {}}
            if self.paused:
                return [pause_event]
        else:
            pause_event = None
        if self.paused:
            return []
        self.sim_tick += 1
        self.phase_tick += 1
        rows = [{"type": "event", "tick": self.tick, "phase": self.sim.phase, "name": name, "data": data}
                for name, data in self.sim.step(inp)]
        return ([pause_event] if pause_event else []) + rows

    def end_row(self):
        row = super().end_row()
        row["ticks"] = self.tick
        row["sim_tick"] = self.sim_tick
        return row


class DaySession:
    def __init__(self, tuning, scenario, seed, days, *, contract_version="1.1", repeat_day_plans=False):
        self.sim = DaySim(tuning, scenario, seed, days, contract_version=contract_version,
                          repeat_day_plans=repeat_day_plans)
        self.tuning, self.mode = tuning, "day"
        self.tick = 0
        self.sim_tick = 0
        self.paused = False
        self.initial_events = self.sim.morning_events()

    @property
    def done(self):
        return self.sim.done

    @property
    def phase_tick(self):
        return self.sim.phase_tick

    def snapshot(self):
        s = _common(self.sim, self.tick, self.sim_tick, self.phase_tick, self.tuning,
                    "paused" if self.paused else ("finished" if self.done else "playing"))
        s.update(self.sim.snapshot())
        return s

    def _wrap(self, tick, events, old_day=None):
        rows = []
        for phase, name, data in events:
            day = old_day if phase == "shop" and old_day is not None else self.sim.day
            row = {"type": "event", "tick": tick, "phase": phase, "day": day,
                   "name": name, "data": data}
            rows.append(row)
        return rows

    def step(self, inp):
        self.tick += 1
        if inp.pressed("pause"):
            self.paused = not self.paused
            pause_event = [(self.sim.phase, "paused" if self.paused else "resumed", {})]
            if self.paused:
                return self._wrap(self.tick, pause_event)
        else:
            pause_event = []
        if self.paused:
            return []
        self.sim_tick += 1
        old_day = self.sim.day
        return self._wrap(self.tick, pause_event + self.sim.step(inp), old_day)

    def end_row(self):
        s = self.sim
        mult = self.tuning["score"]["reputation_multiplier"]
        return {"type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": "day",
                "state": "finished" if s.done else "playing", "reason": s.reason if s.done else "tick_limit",
                "money": s.money, "earned": s.earned, "reputation": s.reputation,
                "score": s.earned + mult * math.floor(s.reputation), "days_completed": s.days_completed}


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every, inventory=None,
        inventory_out=None, contract_version="1.0", days=1):
    if mode == "day":
        sess = DaySession(tuning, scenario, seed, days, contract_version=contract_version)
    elif contract_version in ("1.1", "1.2"):
        sess = V11Session(mode, tuning, scenario, seed, inventory, contract_version=contract_version)
    else:
        sess = Session(mode, tuning, scenario, seed, inventory)
    player = InputPlayer(frames, buttons=BUTTONS_V11) if contract_version in ("1.1", "1.2") else InputPlayer(frames)
    target = out_path
    temp = None
    if mode == "day":
        fd, temp = tempfile.mkstemp(prefix=".day-", suffix=".jsonl.tmp", dir=os.path.dirname(os.path.abspath(out_path)))
        os.close(fd)
        target = temp
    w = None
    try:
        w = JsonlWriter(target)
        if mode == "day":
            for row in sess._wrap(0, sess.initial_events):
                w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        if mode != "day":
            for row in sess.initial_events:
                w.write(row)
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            before_phase = getattr(sess.sim, "phase", mode)
            for row in sess.step(inp):
                w.write(row)
            changed = mode == "day" and sess.sim.phase != before_phase
            if changed or sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    except BaseException:
        try:
            if w is not None:
                w.close()
        finally:
            if temp and os.path.exists(temp):
                os.unlink(temp)
        raise
    else:
        try:
            if w is not None:
                w.close()
        except BaseException:
            if temp and os.path.exists(temp):
                os.unlink(temp)
            raise
    if mode != "day":
        sess.write_inventory_if_done(inventory_out)
    if temp:
        try:
            os.replace(temp, out_path)
        except BaseException:
            if os.path.exists(temp):
                os.unlink(temp)
            raise
    return sess.sim
