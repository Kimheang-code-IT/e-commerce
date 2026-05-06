"""Stock band rules; mirrored on `Product.stock_status`."""


def stock_status_tier(in_stock: int) -> str:
    if in_stock > 15:
        return "aLot"
    if in_stock >= 1:
        return "lower"
    return "out"
