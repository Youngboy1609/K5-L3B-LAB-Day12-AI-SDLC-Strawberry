"""Session sim for one or more v1.1 days (gather -> quan -> Shop)."""

from copy import deepcopy

from ..errors import BadInput
from ..inventory import hold_to_items
from ..ids import IdAllocator
from .gather import GatherSim
from .quan import QuanSim


def ingredients_for(dishes, menu):
    out = {}
    for dish_id, servings in dishes.items():
        if dish_id not in menu:
            raise BadInput(f"món không thuộc menu: {dish_id}")
        for kind, amount in menu[dish_id]["recipe"].items():
            out[kind] = out.get(kind, 0) + amount * servings
    return {k: out[k] for k in sorted(out) if out[k]}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, seed, days=1, *, contract_version="1.1"):
        if contract_version not in ("1.1", "1.2"):
            raise BadInput("DaySim cần contract_version 1.1 hoặc 1.2")
        self.contract_version = contract_version
        self.tuning = tuning
        self.day_tuning = tuning.get("day")
        if not isinstance(self.day_tuning, dict):
            raise BadInput("tuning.day cần bảng day_plans và upgrades cho contract v1.1")
        catalog = self.day_tuning.get("upgrades")
        if not isinstance(catalog, dict):
            raise BadInput("tuning.day.upgrades phải là object")
        if not isinstance(self.day_tuning.get("day_plans"), dict):
            raise BadInput("tuning.day.day_plans phải là object")
        from ..scenario import _validate_upgrades
        if any(not isinstance(spec, dict) for spec in catalog.values()):
            raise BadInput("tuning.day.upgrades entries phải là object")
        _validate_upgrades({name: spec.get("max_level") for name, spec in catalog.items()},
                           self.day_tuning)
        self.scenario = scenario
        self.days = days
        self.day_state = scenario.get("day", {})
        self.money = self.day_state.get("money", 0)
        self.earned = self.day_state.get("earned", 0)
        self.reputation = self.day_state.get("reputation", tuning["quan"]["reputation_initial"])
        self.upgrades = deepcopy(self.day_state.get("upgrades", {}))
        self.active_upgrades = deepcopy(self.upgrades)
        self.seed = seed
        self.ids = IdAllocator()
        self._fixture_id_map = {}
        self.day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0
        self.shop_duration = self.day_tuning.get("shop_ticks")
        if isinstance(self.shop_duration, bool) or not isinstance(self.shop_duration, int) or self.shop_duration <= 0:
            raise BadInput("tuning.day.shop_ticks phải là số nguyên dương")
        self.done = False
        self.reason = None
        self.phase_sim = None
        self.plan = None
        self._build_day()

    def _plan_for(self, day):
        override = self.day_state.get("day_plan")
        if isinstance(override, dict) and "dishes" not in override:
            plan = deepcopy(override.get(str(day), override.get(f"D{day}")))
            if plan is None:
                plans = self.day_tuning["day_plans"]
                plan = deepcopy(plans.get(str(day), plans.get(f"D{day}")))
        elif isinstance(override, dict) and "dishes" in override:
            plan = deepcopy(override)
        else:
            plans = self.day_tuning["day_plans"]
            plan = deepcopy(plans.get(str(day), plans.get(f"D{day}")))
        if not plan or not isinstance(plan.get("dishes"), dict):
            raise BadInput(f"thiếu tuning.day.day_plans cho D{day}; không tự tạo số chuẩn")
        from ..scenario import _validate_day_plan
        _validate_day_plan(plan, self.tuning)
        computed = ingredients_for(plan["dishes"], self.tuning["menu"])
        if "ingredients" in plan and plan["ingredients"] != computed:
            raise BadInput(f"day_plan D{day}: ingredients không khớp công thức")
        return {"dishes": dict(plan["dishes"]), "ingredients": computed}

    @property
    def time_left_ticks(self):
        if self.phase == "shop":
            return max(0, self.shop_duration - self.phase_tick)
        return self.phase_sim.time_left_ticks

    def _effective_tuning(self):
        tuning = deepcopy(self.tuning)
        catalog = self.day_tuning["upgrades"]
        for name, level in self.active_upgrades.items():
            if level <= 0:
                continue
            spec = catalog[name]
            for effect_path, value in spec["levels"][level]["effects"].items():
                if effect_path not in ("gather.hp_max", "gather.oxygen_max_s"):
                    raise BadInput(f"hiệu ứng nâng cấp chưa hỗ trợ: {effect_path}")
                _, key = effect_path.split(".")
                tuning["gather"][key] = value
        return tuning

    def _build_day(self):
        from ..rng import Streams
        tuning = self._effective_tuning()
        self.plan = self._plan_for(self.day)
        self.phase = "gather"
        self.phase_tick = 0
        gs = self.scenario.get("gather", {})
        # Day fixture starts from current active levels; explicit fixture fields win (P2-03).
        if self.contract_version == "1.2":
            try:
                from ..inventory import new_item
            except ImportError as e:
                raise BadInput("v1.2 Day cần inventory.new_item từ adapter Hạnh") from e
            # Fixture IDs are retained on D1. Later days allocate fresh IDs in
            # source order while preserving each fixture item's original kind/fresh.
            fixture = gs.get("hold", [])
            if self.day == 1:
                for item in fixture:
                    self.ids.reserve(item["id"])
                # The engine can age or empty its own hold without modifying the next day's template.
                gather_scenario = deepcopy(gs)
            else:
                gather_scenario = dict(gs)
                remapped = []
                self._fixture_id_map = {}
                for item in fixture:
                    created = new_item(self.ids, item["kind"], item["fresh"])
                    self._fixture_id_map[item["id"]] = created["id"]
                    remapped.append(created)
                if "hold" in gs:
                    gather_scenario["hold"] = remapped
            self.phase_sim = GatherSim(tuning, gather_scenario, Streams(self.seed + self.day - 1),
                                       self.ids, day=self.day, contract_version=self.contract_version)
        else:
            self.phase_sim = GatherSim(tuning, gs, Streams(self.seed + self.day - 1), self.ids, day=self.day)
        self.phase_sim.money, self.phase_sim.earned, self.phase_sim.reputation = self.money, self.earned, self.reputation

    def _build_quan(self):
        from ..rng import Streams
        tuning = self._effective_tuning()
        if self.contract_version == "1.2":
            items = self.phase_sim.inventory_items()
            if self.phase_sim.reason == "fainted":
                items = []
        else:
            items = hold_to_items(self.phase_sim.hold)
            if self.phase_sim.reason == "fainted":
                items = {}
        qs = self.scenario.get("quan", {})
        if self.contract_version == "1.2" and "customers" in qs and self.day > 1:
            qs = deepcopy(qs)
            for customer in qs["customers"]:
                if isinstance(customer.get("reserved"), list):
                    customer["reserved"] = [self._fixture_id_map.get(ref, ref) for ref in customer["reserved"]]
        menu_ids = list(self.plan["dishes"])
        start = {"money": self.money, "earned": self.earned, "reputation": self.reputation}
        self.phase_sim = QuanSim(tuning, qs, Streams(self.seed + self.day - 1), self.ids,
                                 inventory=items, dish_ids=menu_ids, start=start,
                                 contract_version=self.contract_version)
        self.phase = "quan"
        self.phase_tick = 0

    def snapshot(self):
        data = self.phase_sim.snapshot() if self.phase_sim and self.phase != "shop" else {}
        if self.phase == "shop":
            data = {"stock": self._shop_stock_payload(),
                    "time_left_ticks": max(0, self.shop_duration - self.phase_tick)}
        return {**data, "day": self.day, "day_plan": deepcopy(self.plan),
                "upgrades": deepcopy(self.upgrades), "active_upgrades": deepcopy(self.active_upgrades),
                "days_completed": self.days_completed}

    def _shop_stock_payload(self):
        stock = getattr(self, "shop_stock", {} if self.contract_version == "1.1" else [])
        if self.contract_version != "1.2":
            return stock
        try:
            from ..inventory import item_payload
        except ImportError as e:
            raise BadInput("v1.2 Shop cần inventory.item_payload từ adapter Hạnh") from e
        return [item_payload(item) for item in stock]

    def step(self, inp):
        if self.phase == "shop":
            return self._step_shop(inp)
        self.phase_tick += 1
        before = self.phase
        events = self.phase_sim.step(inp)
        self.money, self.earned, self.reputation = self.phase_sim.money, self.phase_sim.earned, self.phase_sim.reputation
        rows = [(before, n, d) for n, d in events]
        if self.phase_sim.done and before == "gather":
            self._build_quan()
            rows.append(("quan", "phase_start", {"phase": "quan"}))
        elif self.phase_sim.done and before == "quan":
            self.shop_stock = list(self.phase_sim.stock) if self.contract_version == "1.2" else dict(self.phase_sim.stock)
            self.phase = "shop"
            self.phase_tick = 0
            rows.append(("shop", "phase_start", {"phase": "shop"}))
        return rows

    def _step_shop(self, inp):
        rows = []
        self.phase_tick += 1
        buy = inp.commands.get("buy")
        if buy:
            catalog = self.day_tuning["upgrades"]
            spec = catalog.get(buy)
            level = self.upgrades.get(buy, 0)
            if spec is None:
                rows.append(("shop", "buy_failed", {"buy": buy, "reason": "unsupported"}))
            elif level >= spec["max_level"]:
                rows.append(("shop", "buy_failed", {"buy": buy, "reason": "max_level"}))
            else:
                next_level = level + 1
                price = spec["levels"][next_level]["price"]
                if self.money < price:
                    rows.append(("shop", "buy_failed", {"buy": buy, "reason": "money"}))
                else:
                    self.money -= price
                    self.upgrades[buy] = next_level
                    rows.append(("shop", "buy_success", {"upgrade": buy, "level": next_level,
                                                           "price": price, "money": self.money}))
        if inp.pressed("shop_done") or self.phase_tick >= self.shop_duration:
            reason = "done" if inp.pressed("shop_done") else "time"
            rows.append(("shop", "shop_end", {"reason": reason}))
            self.days_completed += 1
            self.shop_stock = [] if self.contract_version == "1.2" else {}
            if self.days_completed >= self.days:
                self.done, self.reason = True, "days_complete"
            else:
                self.day += 1
                self.active_upgrades = deepcopy(self.upgrades)
                self._build_day()
                rows.extend([("gather", "day_start", {}),
                             ("gather", "day_plan", deepcopy(self.plan)),
                             ("gather", "phase_start", {"phase": "gather"})])
        return rows
