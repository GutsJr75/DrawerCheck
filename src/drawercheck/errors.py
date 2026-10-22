"""Expected application errors and their user-facing messages."""

INVALID_MONEY = (
    "Invalid money value {value!r}. "
    "Use dollars with exactly two decimal places, such as 1250.75."
)
MONEY_OUT_OF_RANGE = (
    "Money value {value!r} is outside the supported range of integer cents."
)
SQLITE_TOO_OLD = (
    "SQLite 3.37.0 or newer is required; found {version}. "
    "Use a Python installation with a newer SQLite."
)
INVALID_ARGUMENTS = "Invalid command: {detail}. Run 'drawercheck --help' for usage."


class DrawerCheckError(Exception):
    """An expected problem that can be explained without a traceback."""


class MoneyValidationError(DrawerCheckError, ValueError):
    """A dollar value cannot be represented as supported integer cents."""


class DatabaseVersionError(DrawerCheckError):
    """The installed SQLite is too old for STRICT tables."""


class UsageError(DrawerCheckError):
    """The command-line arguments are invalid."""
