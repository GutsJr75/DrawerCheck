"""The M11 block 1 walkthrough drawers, as manual entries and as the seven CSVs."""

from pathlib import Path

DENOMINATION_KEYS = (
    "100.00",
    "50.00",
    "20.00",
    "10.00",
    "5.00",
    "2.00",
    "1.00",
    "0.50",
    "0.25",
    "0.10",
    "0.05",
    "0.01",
)
CASES = {
    "A": {
        "register_id": "R1",
        "cashier_id": "cashier_01",
        "counts": (0, 2, 10, 8, 12, 0, 56, 0, 80, 30, 20, 61),
        "report": ("842.35", "6.49", "0.00", "15.00"),
        "drops": (("500.00", "DEMO-BAG-1102-R1-A"),),
    },
    "B": {
        "register_id": "R2",
        "cashier_id": "cashier_02",
        "counts": (1, 3, 12, 6, 9, 0, 47, 0, 72, 35, 31, 60),
        "report": ("1316.40", "18.25", "20.00", "32.50"),
        "drops": (
            ("400.00", "DEMO-BAG-1102-R2-A"),
            ("400.00", "DEMO-BAG-1102-R2-B"),
        ),
    },
    "C": {
        "register_id": "R3",
        "cashier_id": "cashier_03",
        "counts": (0, 2, 8, 7, 10, 0, 38, 0, 60, 28, 40, 0),
        "report": None,
        "drops": (("300.00", "DEMO-BAG-1102-R3-A"),),
    },
}
SIGN_OFF = {
    "verifier_id": "manager_01",
    "variance_note": "Recounted with manager. Still short 20.00. Report and drop log rechecked.",
}


def drawer_payload(case: str, **changes: object) -> dict:
    """Build one walkthrough drawer as the JSON the Close a drawer page sends."""
    values = CASES[case]
    report = values["report"]
    payload = {
        "business_date": "2026-11-02",
        "register_id": values["register_id"],
        "cashier_id": values["cashier_id"],
        "opened_at": "2026-11-02T08:00",
        "closed_at": "2026-11-02T20:00",
        "opening_float": "200.00",
        "counts": {
            key: str(quantity)
            for key, quantity in zip(DENOMINATION_KEYS, values["counts"], strict=True)
        },
        "recount": None,
        "register_report": None
        if report is None
        else dict(
            zip(
                ("cash_sales", "cash_refunds", "paid_ins", "paid_outs"),
                report,
                strict=True,
            )
        ),
        "safe_drops": [
            {"amount": amount, "bag_number": bag} for amount, bag in values["drops"]
        ],
        "verifier_id": "",
        "variance_note": "",
    }
    payload.update(changes)
    return payload


def write_case_csvs(directory: Path, *, signed: bool = False) -> None:
    """Write all three walkthrough drawers as the seven import files."""
    directory.mkdir(parents=True, exist_ok=True)
    shifts = [
        "shift_code,business_date,register_id,cashier_id,opened_at,closed_at,"
        "opening_float,verifier_id,variance_note"
    ]
    pos = [
        "shift_code,cash_sales,card_sales,cash_refunds,paid_outs,paid_ins,"
        "void_count,no_sale_count"
    ]
    drops = ["shift_code,amount,dropped_at,bag_number"]
    counts = ["shift_code,denomination,quantity"]
    for case, values in CASES.items():
        code = f"2026-11-02-{values['register_id']}"
        verifier, note = ("", "")
        if signed and case == "B":
            verifier, note = SIGN_OFF["verifier_id"], SIGN_OFF["variance_note"]
        shifts.append(
            f"{code},2026-11-02,{values['register_id']},{values['cashier_id']},"
            f"2026-11-02T08:00:00,2026-11-02T20:00:00,200.00,{verifier},{note}"
        )
        if values["report"] is not None:
            sales, refunds, paid_ins, paid_outs = values["report"]
            pos.append(f"{code},{sales},0.00,{refunds},{paid_outs},{paid_ins},0,0")
        for amount, bag in values["drops"]:
            drops.append(f"{code},{amount},2026-11-02T16:00:00,{bag}")
        for key, quantity in zip(DENOMINATION_KEYS, values["counts"], strict=True):
            counts.append(f"{code},{key},{quantity}")
    files = {
        "cashiers.csv": [
            "cashier_id,display_name",
            "cashier_01,Demo Cashier 01",
            "cashier_02,Demo Cashier 02",
            "cashier_03,Demo Cashier 03",
            "manager_01,Demo Manager 01",
        ],
        "registers.csv": [
            "register_id,label",
            "R1,Demo Register 1",
            "R2,Demo Register 2",
            "R3,Demo Register 3",
        ],
        "shifts.csv": shifts,
        "pos_totals.csv": pos,
        "safe_drops.csv": drops,
        "cash_counts.csv": counts,
        "bank_deposits.csv": ["deposit_date,amount,reference"],
    }
    for name, lines in files.items():
        (directory / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
