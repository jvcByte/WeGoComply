from __future__ import annotations


def mask_identifier(value: str, *, visible_suffix: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= visible_suffix:
        return "*" * len(value)
    masked_length = len(value) - visible_suffix
    return f"{'*' * masked_length}{value[-visible_suffix:]}"
