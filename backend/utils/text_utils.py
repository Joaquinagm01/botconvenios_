from __future__ import annotations

import re
from typing import Iterable


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned.strip()


def first_match(patterns: Iterable[str], text: str, flags: int = re.IGNORECASE | re.MULTILINE) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            value = next((group for group in match.groups() if group), match.group(0))
            return value.strip()
    return ""


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in full_name.split() if part]
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:])
    if parts:
        return parts[0], ""
    return "", ""


def choose_best_line(lines: list[str], keywords: tuple[str, ...]) -> str:
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in keywords):
            return line.strip()
    return ""


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
