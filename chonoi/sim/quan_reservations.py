"""Deterministic reservation fixtures and generated orders for Quán v1.2."""

from ..errors import BadInput
from ..ids import sort_by_id


def build_reservations(tuning, scenario, streams, dish_ids):
    """Return the reservation schedule for one Quán/Day phase.

    Explicit ``quan.reservations`` replaces generation. Generated arrival ticks use
    the Ticket-03 standard-shift interval [1800, 10799].
    """
    config = tuning.get("reservations")
    if not isinstance(config, dict):
        return []
    quan = scenario.get("quan", scenario)
    if not isinstance(quan, dict):
        raise BadInput("quan phải là object")
    explicit = quan.get("reservations")
    if explicit is not None:
        return normalize_reservations(explicit, tuning)
    if not quan.get("random_reservations", True):
        return []

    count = config.get("count", 2)
    tables = sorted(tuning["quan"]["tables"], key=lambda table: table["id"])
    dishes = sorted(set(dish_ids))
    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 2:
        raise BadInput("reservations.count phải là số nguyên trong [0, 2]")
    if count == 0 or not tables or not dishes:
        return []
    if count > len(tables):
        raise BadInput("reservations.count vượt số bàn")
    rng = streams.get("reservations")
    chosen_tables = rng.sample(tables, count)
    rows = []
    for index, table in enumerate(chosen_tables, 1):
        rows.append({"id": f"R{index}", "table_id": table["id"],
                     "dish_id": rng.choice(dishes), "arrival_tick": rng.randint(1800, 10799)})
    return normalize_reservations(rows, tuning)


def normalize_reservations(rows, tuning):
    config = tuning.get("reservations", {"table_hold_s": 30})
    if not isinstance(rows, list):
        raise BadInput("reservations phải là mảng")
    hold_ticks = round(config.get("table_hold_s", 30) * tuning.get("tick_hz", 60))
    result = []
    for row in rows:
        if not isinstance(row, dict) or not {"id", "table_id", "dish_id", "arrival_tick"} <= set(row):
            raise BadInput("reservation cần id, table_id, dish_id, arrival_tick")
        if set(row) - {"id", "table_id", "dish_id", "arrival_tick", "state"}:
            raise BadInput("reservation có trường không hỗ trợ")
        if any(not isinstance(row.get(key), str) or not row[key]
               for key in ("id", "table_id", "dish_id")):
            raise BadInput("reservation.id, table_id, dish_id phải là chuỗi khác rỗng")
        item = dict(row)
        arrival = item.get("arrival_tick")
        if isinstance(arrival, bool) or not isinstance(arrival, int) or arrival < 1:
            raise BadInput("reservation.arrival_tick phải là số nguyên dương")
        item["state"] = "holding" if max(0, arrival - hold_ticks) == 0 else "scheduled"
        result.append(item)
    return sort_by_id(result)
