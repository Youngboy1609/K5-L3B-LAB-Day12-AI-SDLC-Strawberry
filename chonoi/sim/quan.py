"""Buổi tối — Mở Quán. KHUNG: đi lại, chặn biên, đồng hồ, kho nạp từ file/scenario.

Nhóm viết tiếp (PRD-0 mục F, Quán):
  TODO(nhóm, lát 3): khách đến theo lịch, chọn món nấu được, giữ chỗ nguyên liệu, kiên nhẫn,
                     bỏ đi (customer_left), no_dish, vòng đời khách.
  TODO(nhóm, lát 4): interact tại bếp/bàn (cook_started, dish_ready, dish_picked, served),
                     ăn xong trả tiền (paid), boa, uy tín, hết ca (quan_end).
"""

from ..ids import sort_by_id
from ..errors import BadInput
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
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
                if not isinstance(dish_id, str) or dish_id not in self.menu:
                    raise BadInput(f"customers.{customer['id']}.dish_id cần là món trong menu")
                customer["reserved"] = dict(self.menu[dish_id]["recipe"])
            else:
                customer.setdefault("reserved", {})
            self.customers.append(customer)
        for e in self.customers:
            ids.reserve(e["id"])
        self._validate_fixture()
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def available_stock(self):
        """Physical stock less reservations still owned by reserved orders."""
        available = dict(self.stock)
        for customer in self.customers:
            if customer.get("order_status") == "reserved":
                for kind, count in customer.get("reserved", {}).items():
                    available[kind] = available.get(kind, 0) - count
        return available

    def _validate_fixture(self):
        """Validate linked fixture data before runner creates its output file."""
        from ..inventory import validate_items

        self.stock = validate_items(self.stock)
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
            if not isinstance(dish_id, str) or dish_id not in self.menu:
                raise BadInput(f"customers.{customer['id']}.dish_id không hợp lệ")
            expected = self.menu[dish_id]["recipe"]
            held = validate_items(customer.get("reserved", {}))
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
        self._move(inp)
        # Integration contract: Quang's service module is not present in this checkout.
        # Call advance_stoves(sim, events) before movement, interact(sim, events) after movement,
        # then settle_customers(sim, events) before scheduling arrivals.
        self._spawn_scheduled_customer(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
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
        available = self.available_stock()
        choices = [dish_id for dish_id in sorted(self.menu)
                   if all(available.get(kind, 0) >= count
                          for kind, count in self.menu[dish_id]["recipe"].items())]
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
