"""Small immutable records shared by calculations, commands, and future reports."""

from dataclasses import dataclass
from typing import Literal

from drawercheck.config import Config


@dataclass(frozen=True)
class PosTotals:
    """The imported cash movements and other POS totals for one shift."""

    cash_sales_cents: int
    card_sales_cents: int
    cash_refunds_cents: int
    paid_outs_cents: int
    paid_ins_cents: int
    void_count: int
    no_sale_count: int


@dataclass(frozen=True)
class Shift:
    """One shift with independent POS, count, and safe-drop records."""

    id: int
    shift_code: str
    business_date: str
    register_id: str
    cashier_id: str
    opened_at: str
    closed_at: str | None
    opening_float_cents: int
    verifier_id: str | None
    variance_note: str | None
    pos: PosTotals | None
    counts: tuple[tuple[int, int], ...]
    safe_drops_cents: int


@dataclass(frozen=True)
class Flag:
    """A neutral review lead with the values used to produce it."""

    shift_id: int | None
    business_date: str
    rule_code: str
    severity: Literal["info", "warn", "review"]
    message: str
    evidence: dict[str, object]


@dataclass(frozen=True)
class ShiftResult:
    """Exact calculations, status, surrounding records, and saved review leads."""

    shift: Shift
    expected_cents: int | None
    counted_cents: int | None
    variance_cents: int | None
    status: Literal["open", "incomplete", "balanced", "over", "short"]
    overlapping_codes: tuple[str, ...] = ()
    other_closing_codes: tuple[str, ...] = ()
    flags: tuple[Flag, ...] = ()


@dataclass(frozen=True)
class DailyDeposit:
    """A calculated daily amount, with None indicating incomplete inputs."""

    business_date: str
    expected_cents: int | None
    flags: tuple[Flag, ...] = ()


@dataclass(frozen=True)
class ReconciliationResult:
    """The selected shifts and daily totals from one successful run."""

    from_date: str
    to_date: str
    shifts: tuple[ShiftResult, ...]
    deposits: tuple[DailyDeposit, ...]

    @property
    def flags(self) -> tuple[Flag, ...]:
        """Include both shift review leads and date-level integrity leads."""
        return tuple(flag for result in self.shifts for flag in result.flags) + tuple(
            flag for day in self.deposits for flag in day.flags
        )


@dataclass(frozen=True)
class ShiftExplanation:
    """A shift's saved review leads and the policies behind its calculations."""

    result: ShiftResult
    config: Config
    deposit_contribution_cents: int | None
    daily_deposit_cents: int | None
    daily_flags: tuple[Flag, ...] = ()
