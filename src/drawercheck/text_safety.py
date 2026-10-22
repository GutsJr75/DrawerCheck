"""Keep imported text readable without letting it control terminal output."""

import unicodedata

_UNSAFE_CATEGORIES = {"Cc", "Cf", "Cs", "Zl", "Zp"}
_TEXT_WHITESPACE = "\n\r\t"


def has_unsafe_controls(value: str) -> bool:
    """Reject nonprinting controls while allowing ordinary multiline free text."""
    return any(
        character not in _TEXT_WHITESPACE
        and unicodedata.category(character) in _UNSAFE_CATEGORIES
        for character in value
    )


def terminal_text(value: object) -> str:
    """Render one field or message on one terminal line using visible escapes."""
    escaped = []
    replacements = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
    for character in str(value):
        if character in replacements:
            escaped.append(replacements[character])
        elif unicodedata.category(character) in _UNSAFE_CATEGORIES:
            code = ord(character)
            escaped.append(f"\\x{code:02x}" if code < 256 else f"\\u{code:04x}")
        else:
            escaped.append(character)
    return "".join(escaped)
