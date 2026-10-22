"""The seven input files and the allowed cash denominations."""

CSV_HEADERS = {
    "cashiers.csv": ("cashier_id", "display_name"),
    "registers.csv": ("register_id", "label"),
    "shifts.csv": (
        "shift_code",
        "business_date",
        "register_id",
        "cashier_id",
        "opened_at",
        "closed_at",
        "opening_float",
        "verifier_id",
        "variance_note",
    ),
    "pos_totals.csv": (
        "shift_code",
        "cash_sales",
        "card_sales",
        "cash_refunds",
        "paid_outs",
        "paid_ins",
        "void_count",
        "no_sale_count",
    ),
    "safe_drops.csv": ("shift_code", "amount", "dropped_at", "bag_number"),
    "cash_counts.csv": ("shift_code", "denomination", "quantity"),
    "bank_deposits.csv": ("deposit_date", "amount", "reference"),
}

DENOMINATIONS_CENTS = (10000, 5000, 2000, 1000, 500, 200, 100, 50, 25, 10, 5, 1)
