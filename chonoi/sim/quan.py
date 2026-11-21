"""Buổi tối — lịch khách, kho và vòng tick chung của quán (PRD-0 mục F)."""

from ..ids import sort_by_id
from ..errors import BadInput
from ..inventory import ingredient_kinds, validate_items
from .ramp import ramp_velocity
from .quan_service import advance_stoves, interact, settle_customers

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, dish_ids=None, start=None,
                 *, contract_version="1.0"):
        """`dish_ids`: tập ID món trong kế hoạch Ngày (mode `day`); None = quán độc lập, bán cả menu.
        `start`: {"money", "earned", "reputation"} bàn giao từ pha trước trong `day`; None = ca mới."""
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        # Chỉ mode `day` truyền dish_ids/start; quán độc lập giữ JSONL đúng định dạng v1.0 (không thêm khóa).
        self.day_mode = dish_ids is not None or start is not None
        if dish_ids is None:
            self.dish_ids = sorted(self.menu)
        else:
            if not isinstance(dish_ids, (list, tuple, set, frozenset)):
                raise BadInput("dish_ids phải là danh sách ID món")
            unknown = sorted(set(dish_ids) - set(self.menu))
            if unknown:
                raise BadInput(f"kế hoạch Ngày có món không có trong menu: {unknown}")
            self.dish_ids = sorted(set(dish_ids))
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.phase_tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.customers = []
        patience = int(round(t["patience_s"] * TICK))
        for source in scenario.get("customers", []):
            customer = dict(source)
            customer.setdefault("state", "waiting")
            customer.setdefault("order_tick", 0)
            customer.setdefault("patience_ticks_left", patience)
            customer.setdefault("order_status", "reserved")
            customer.setdefault("eat_ticks_left", 0)
            customer.setdefault("tip", 0)
            if customer["order_status"] == "reserved" and "reserved" not in customer:
                dish_id = customer.get("dish_id")
                if not isinstance(dish_id, str) or dish_id not in self.dish_ids:
                    raise BadInput(f"customers.{customer['id']}.dish_id cần là món trong menu tối nay")
                customer["reserved"] = dict(self.menu[dish_id]["recipe"])
            else:
                customer.setdefault("reserved", {})
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self._validate_fixture(ingredient_kinds(contract_version))
        start = start or {}
        self.money = start.get("money", 0)
        self.earned = start.get("earned", 0)
        for name in ("money", "earned"):
            v = getattr(self, name)
            if isinstance(v, bool) or not isinstance(v, int):
                raise BadInput(f"start.{name} phải là số nguyên")
        if not (0 <= self.money <= self.earned):
            raise BadInput("cần 0 ≤ money ≤ earned khi mở quán")
        if "reputation" in start:
            rep = start["reputation"]
            if (isinstance(rep, bool) or not isinstance(rep, (int, float))
                    or not (t["reputation_min"] <= rep <= t["reputation_max"])):
                raise BadInput("start.reputation phải là số trong [reputation_min, reputation_max]")
            self.reputation = rep
        self.shift_earned = 0
        # Báo cáo cuối ca cho HUD/DayResult; quan_service cập nhật.
        # Khách fixture đang ăn tính là đã phục vụ, để paid ≤ served.
        self.shift = {"served": sum(c["state"] == "eating" for c in self.customers),
                      "paid": 0, "left": 0, "left_closing": 0, "tips": 0}
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        snap = {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }
        if self.day_mode:
            snap["menu"] = list(self.dish_ids)
            snap["shift"] = dict(self.shift, shift_earned=self.shift_earned)
        return snap

    def available_stock(self):
        """Physical stock less reservations still owned by reserved orders."""
        available = dict(self.stock)
        for customer in self.customers:
            if customer.get("order_status") == "reserved":
                for kind, count in customer.get("reserved", {}).items():
                    available[kind] = available.get(kind, 0) - count
        return available

    def cookable_dishes(self):
        available = self.available_stock()
        return [dish_id for dish_id in self.dish_ids
                if all(available.get(kind, 0) >= count
                       for kind, count in self.menu[dish_id]["recipe"].items())]

    def _validate_fixture(self, kinds):
        """Validate linked fixture data before runner creates its output file."""
        self.stock = validate_items(self.stock, kinds)
        table_ids = {table["id"] for table in self.tables}
        customer_by_id = {customer["id"]: customer for customer in self.customers}
        if any(customer["table_id"] not in table_ids for customer in self.customers):
            raise BadInput("customer tham chiếu bàn không tồn tại")
        reserved_total = {}
        for customer in self.customers:
            status = customer.get("order_status")
            state = customer.get("state")
            if status not in ("reserved", "assigned", "unfulfillable", "served"):
                raise BadInput(f"customers.{customer['id']}.order_status không hợp lệ")
            dish_id = customer.get("dish_id")
            if not isinstance(dish_id, str) or dish_id not in self.dish_ids:
                raise BadInput(f"customers.{customer['id']}.dish_id không thuộc menu tối nay")
            expected = self.menu[dish_id]["recipe"]
            held = validate_items(customer.get("reserved", {}), kinds)
            customer["reserved"] = held
            if status == "reserved":
                if held != expected or state != "waiting":
                    raise BadInput(f"customers.{customer['id']}: reserved phải đúng công thức và đang chờ")
                for kind, amount in held.items():
                    reserved_total[kind] = reserved_total.get(kind, 0) + amount
            elif held:
                raise BadInput(f"customers.{customer['id']}: đơn không reserved không được giữ kho")
            if status == "assigned" and state != "waiting":
                raise BadInput(f"customers.{customer['id']}: assigned phải đang chờ")
            if status == "served" and state != "eating":
                raise BadInput(f"customers.{customer['id']}: served phải đang ăn")
            if state == "eating":
                if status != "served" or customer["eat_ticks_left"] <= 0:
                    raise BadInput(f"customers.{customer['id']}: eating cần served và timer dương")
                if customer.get("base_price") != self.menu[dish_id]["price"]:
                    raise BadInput(f"customers.{customer['id']}: eating cần base_price khớp món")
                if "tip" not in customer or isinstance(customer["tip"], bool) or not isinstance(customer["tip"], int):
                    raise BadInput(f"customers.{customer['id']}: eating cần tip đã chốt")
            if status == "unfulfillable" and state != "waiting":
                raise BadInput(f"customers.{customer['id']}: unfulfillable phải đang chờ")
            for name in ("order_tick", "patience_ticks_left", "eat_ticks_left", "tip"):
                value = customer.get(name)
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise BadInput(f"customers.{customer['id']}.{name} phải là số nguyên không âm")
        if any(amount > self.stock.get(kind, 0) for kind, amount in reserved_total.items()):
            raise BadInput("tổng reserved vượt tồn vật lý")

        payloads = []
        for stove in self.stoves:
            state = stove.get("state")
            dish = stove.get("dish")
            if state == "idle":
                if dish is not None or stove["cook_ticks_left"] != 0:
                    raise BadInput(f"stoves.{stove['id']}: idle không có món hoặc timer nấu")
            elif state in ("cooking", "ready"):
                self._validate_payload(dish, customer_by_id, state)
                payloads.append(dish)
                if state == "cooking" and stove["cook_ticks_left"] <= 0:
                    raise BadInput(f"stoves.{stove['id']}: cooking cần timer dương")
                if state == "ready" and stove["cook_ticks_left"] != 0:
                    raise BadInput(f"stoves.{stove['id']}: ready không còn timer nấu")
            else:
                raise BadInput(f"stoves.{stove['id']}.state không hợp lệ")
        if self.hand is not None:
            self._validate_payload(self.hand, customer_by_id, "hand")
            payloads.append(self.hand)
        orders = [payload["order_id"] for payload in payloads]
        if len(orders) != len(set(orders)):
            raise BadInput("một đơn không thể ở cả bếp và tay")
        for customer in self.customers:
            count = orders.count(customer["id"])
            if (customer["order_status"] == "assigned") != (count == 1):
                raise BadInput(f"customers.{customer['id']}: assigned cần đúng một món ở bếp hoặc tay")

    def _validate_payload(self, payload, customers, source):
        if not isinstance(payload, dict) or set(payload) != {"order_id", "dish_id", "base_price"}:
            raise BadInput(f"{source}.dish phải có order_id, dish_id, base_price")
        customer = customers.get(payload["order_id"])
        if customer is None or customer.get("order_status") not in ("assigned", "served"):
            raise BadInput(f"{source}.dish.order_id không khớp đơn được gán")
        dish_id = payload["dish_id"]
        if not isinstance(dish_id, str) or dish_id not in self.menu or customer.get("dish_id") != dish_id:
            raise BadInput(f"{source}.dish_id không khớp khách")
        if payload["base_price"] != self.menu[dish_id]["price"]:
            raise BadInput(f"{source}.base_price không khớp giá món")

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        # Customers present at tick start lose patience/eat time; arrivals below start next tick.
        for customer in self.customers:
            if customer.get("state") == "waiting" and customer.get("patience_ticks_left", 0) > 0:
                customer["patience_ticks_left"] -= 1
            elif customer.get("state") == "eating" and customer.get("eat_ticks_left", 0) > 0:
                customer["eat_ticks_left"] -= 1
        advance_stoves(self, events)
        self._move(inp)
        if inp.pressed("interact"):
            interact(self, events)
        settle_customers(self, events)
        if not self.done:
            self._spawn_scheduled_customer(events)
        return events

    def _spawn_scheduled_customer(self, events):
        if not self.random_customers or self.time_left_ticks <= 0:
            return
        first = int(self.t["first_customer_tick"])
        interval = int(round(self.t["customer_interval_s"] * TICK))
        if self.phase_tick < first or (self.phase_tick - first) % interval:
            return
        occupied = {c["table_id"] for c in self.customers}
        free_tables = [table for table in self.tables if table["id"] not in occupied]
        if not free_tables:
            return
        table = free_tables[0]
        choices = self.cookable_dishes()
        if not choices:
            events.append(("no_dish", {"table_id": table["id"]}))
            return
        dish_id = self.rng.get("customers").choice(choices)
        customer_id = self.ids.new("C")
        customer = {
            "id": customer_id, "table_id": table["id"], "state": "waiting",
            "order_tick": self.phase_tick, "patience_ticks_left": int(round(self.t["patience_s"] * TICK)),
            "order_status": "reserved", "dish_id": dish_id, "eat_ticks_left": 0,
            "tip": 0, "reserved": dict(self.menu[dish_id]["recipe"]),
        }
        self.customers.append(customer)
        # Payload is a minimal working assumption until the missing PRD event glossary is resolved.
        events.append(("customer_arrived", {"customer_id": customer_id, "table_id": table["id"],
                                               "dish_id": dish_id}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
