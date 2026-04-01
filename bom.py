import json
import os

_EQUIPMENT_DB = None

def _load_db() -> dict:
    global _EQUIPMENT_DB
    if _EQUIPMENT_DB is None:
        db_path = os.path.join(os.path.dirname(__file__), "equipment.json")
        with open(db_path) as f:
            _EQUIPMENT_DB = json.load(f)
    return _EQUIPMENT_DB


def generate_bom(topology: dict) -> dict:
    """Generate Bill of Materials from topology JSON.
    Returns {"items": [...], "total_thb": int}
    """
    db = _load_db()
    nodes = topology.get("nodes", [])

    # Count how many of each model_hint we need
    hint_counts = {}
    for node in nodes:
        hint = node.get("specs", {}).get("model_hint")
        if hint:
            hint_counts[hint] = hint_counts.get(hint, 0) + 1

    items = []
    total = 0

    for hint, qty in hint_counts.items():
        if hint in db:
            eq = db[hint]
            subtotal = eq["price_thb"] * qty
            total += subtotal
            items.append({
                "model_hint": hint,
                "name": eq["name"],
                "brand": eq["brand"],
                "category": eq["category"],
                "specs": eq["specs"],
                "qty": qty,
                "unit_price_thb": eq["price_thb"],
                "subtotal_thb": subtotal,
            })
        else:
            items.append({
                "model_hint": hint,
                "name": f"Unknown ({hint})",
                "brand": "-",
                "category": "-",
                "specs": "-",
                "qty": qty,
                "unit_price_thb": 0,
                "subtotal_thb": 0,
            })

    # Sort by subtotal descending
    items.sort(key=lambda x: x["subtotal_thb"], reverse=True)

    return {"items": items, "total_thb": total}


if __name__ == "__main__":
    sample_topology = {
        "nodes": [
            {"id": "fw-1",    "specs": {"model_hint": "enterprise_firewall"}},
            {"id": "router-1","specs": {"model_hint": "enterprise_router"}},
            {"id": "sw-core", "specs": {"model_hint": "core_switch"}},
            {"id": "sw-f1",   "specs": {"model_hint": "poe_switch"}},
            {"id": "sw-f2",   "specs": {"model_hint": "poe_switch"}},
            {"id": "sw-f3",   "specs": {"model_hint": "poe_switch"}},
            {"id": "ap-1",    "specs": {"model_hint": "access_point"}},
            {"id": "ap-2",    "specs": {"model_hint": "access_point"}},
            {"id": "ap-3",    "specs": {"model_hint": "access_point"}},
            {"id": "srv-1",   "specs": {"model_hint": "rack_server"}},
        ]
    }
    result = generate_bom(sample_topology)
    print(f"{'Category':<20} {'Model':<30} {'Qty':>4} {'Unit':>10} {'Subtotal':>12}")
    print("-" * 80)
    for item in result["items"]:
        print(f"{item['category']:<20} {item['name']:<30} {item['qty']:>4} {item['unit_price_thb']:>10,} {item['subtotal_thb']:>12,}")
    print("-" * 80)
    print(f"{'TOTAL (THB)':<56} {result['total_thb']:>12,}")
