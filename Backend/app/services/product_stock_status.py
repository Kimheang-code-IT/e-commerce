from __future__ import annotations


def stock_status_tier(in_stock: int) -> str:
    qty = max(0, int(in_stock or 0))
    if qty == 0:
        return "out"
    if qty <= 10:
        return "lower"
    return "aLot"
