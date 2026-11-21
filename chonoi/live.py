"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan|day [--days 1-5] [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
                    {"pause": bool}  -> tạm dừng / chạy tiếp: khi pause, luồng nền KHÔNG bước tick (trình bày, không vào luật)
                    mode day thêm {"buy": "<mã nâng cấp>"} và {"shop_done": bool} như input v1.1 của headless
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
from fractions import Fraction
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import load_contract
from .errors import BadInput
from .inputs import BUTTONS_V11, LiveInputs
from .inventory import ingredient_kinds, read_inventory
from .runner import DaySession, Session
from .scenario import load_scenario

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40
FRESH_EXPORT_DIGITS = 5  # v1.2: cùng độ chính xác với item_payload của file kho/JSONL (chỉ để hiển thị)


def _json_default(o):
    """v1.2 giữ fresh là Fraction trong sim; client nhận số JSON 5 chữ số như file kho. Luật không đọc lại số này."""
    if isinstance(o, Fraction):
        r = round(float(o), FRESH_EXPORT_DIGITS)
        return 0.0 if r == 0 else r
    raise TypeError(f"không xuất JSON được kiểu {type(o).__name__}")


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=1,
                 *, contract_version="1.0", freshness=None):
        self.contract_version = contract_version
        self.freshness = freshness  # v1.2: {initial, gather_decay_per_s, quan_decay_per_s, spoiled_below} để HUD biết ngưỡng ươn
        self._args = (mode, tuning, scenario, seed, inventory)
        self.days = days
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        if self.mode == "day":
            mode, tuning, scenario, seed, _ = self._args
            self.session = DaySession(tuning, scenario, seed, self.days)
            self.inputs = LiveInputs(buttons=BUTTONS_V11, allow_buy=True)
            self.events = self.session._wrap(0, self.session.initial_events)  # day_start, day_plan, phase_start
            self.served_dishes = {}
            self.shift_start_reputation = self.session.sim.reputation
        else:
            self.session = Session(*self._args, contract_version=self.contract_version)
            self.inputs = LiveInputs()
            self.events = []
        self._saved = False
        self.error = None
        self.paused = False  # restart luôn bỏ pause

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done or self.paused:  # pause: sim đứng yên hoàn toàn (oxy, giờ, kiên nhẫn, Shop)
            return
        for row in s.step(self.inputs.advance()):
            self.events.append(row)
            if self.mode == "day":
                if row["name"] == "phase_start" and row["phase"] == "quan":
                    self.shift_start_reputation = s.sim.reputation
                elif row["name"] == "served":
                    dish_id = row["data"]["dish_id"]
                    self.served_dishes[dish_id] = self.served_dishes.get(dish_id, 0) + 1
        del self.events[:-RECENT_EVENTS]
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            if self.mode == "day":
                # Client vẽ theo pha hiện tại; bảng nâng cấp (giá, cấp tối đa) cho màn Shop nằm ở day_meta.
                snap["meta"] = self.tuning.get(snap.get("phase"), {}) if snap.get("phase") in ("gather", "quan") else {}
                snap["day_meta"] = self.tuning.get("day", {})
                snap["shift_reputation_delta"] = round(snap["reputation"] - self.shift_start_reputation, 9)
                snap["served_dishes"] = self.served_dishes
                if snap["phase"] == "quan":
                    snap["cookable_dishes"] = self.session.sim.phase_sim.cookable_dishes()
            else:
                snap["meta"] = self.tuning[self.mode]
            if snap["phase"] == "gather" and "monsters" in snap:
                gather = self.session.sim.phase_sim if self.mode == "day" else self.session.sim
                snap["monster_warning_radius"] = gather.monster_rules["detect_radius"]
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            snap["paused"] = self.paused
            snap["contract_version"] = self.contract_version  # HUD chọn schema kho: v1.2 mảng cá thể, cũ là object đếm
            if self.freshness is not None:
                snap["freshness"] = self.freshness
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":"), default=_json_default).encode("utf-8")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in ("interact", "catch", "shop_done"):
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        buy = body.get("buy")
        if buy is not None and (not isinstance(buy, str) or not buy):
            raise ValueError("buy phải là chuỗi mã nâng cấp")
        pause = body.get("pause")
        if pause is not None and not isinstance(pause, bool):
            raise ValueError("pause phải là boolean")
        with self._lock:
            if pause is not None:
                self.paused = pause
            self.inputs.set(move, buy=buy, **buttons)

    def restart(self):
        with self._lock:
            self._reset()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/restart":
                self.game.restart()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])  # day cần contract v1.1+
    p.add_argument("--days", type=int, help="chỉ với day: số ngày 1–5 (mặc định 5)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        if a.days is not None and a.mode != "day":
            raise BadInput("--days chỉ dùng với --mode day")
        days = 5 if a.days is None else a.days
        if a.mode == "day" and not 1 <= days <= 5:
            raise BadInput("--days phải là số nguyên trong [1, 5]")
        if a.mode == "day" and (a.inventory or a.inventory_out):
            raise BadInput("day không nhận cờ file kho --inventory/--inventory-out")
        contract = load_contract()
        version = contract.get("contract_version", "1.0")
        if a.mode == "day" and version not in ("1.1", "1.2"):
            raise BadInput("--mode day cần game.contract.json v1.1 trở lên (bảng day_plans, upgrades); file hiện là v" + str(version))
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning, version)
        inventory = None
        if a.inventory:
            if version == "1.2":  # kho mảng cá thể; file đếm cũ bị từ chối (mã 2)
                inventory = read_inventory(a.inventory, ingredient_kinds(version), contract_version=version)
            else:
                inventory = read_inventory(a.inventory, ingredient_kinds(version))
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out,
                        days=days, contract_version=version,
                        freshness=contract.get("freshness", tuning.get("freshness")))
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
