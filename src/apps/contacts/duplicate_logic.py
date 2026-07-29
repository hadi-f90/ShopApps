"""
Pure duplicate-detection helpers for Contacts (no Peewee/Qt).

Exact match: normalized mobile, phone, or email.
Fuzzy match: Persian-normalized names via difflib (threshold configurable).
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Callable, Iterable, Optional, Sequence, TypeVar

T = TypeVar("T")

# Name similarity above this counts as fuzzy duplicate (0..1)
DEFAULT_NAME_THRESHOLD = 0.88

# Persian / Arabic character folding for comparison
_TRANS = str.maketrans(
    {
        "ك": "ک",
        "ي": "ی",
        "ى": "ی",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ی",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "\u200c": "",  # ZWNJ
        "\u200d": "",
        "\u0640": "",  # tatweel
    }
)


def normalize_phone(value: str | None) -> str:
    if not value:
        return ""
    out: list[str] = []
    for ch in str(value).strip():
        if ch.isdigit():
            out.append(ch)
        elif ch == "+" and not out:
            out.append(ch)
    return "".join(out)


def phone_core(value: str | None) -> str:
    """Last 10 digits for loose mobile compare (ignores country code noise)."""
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    return digits[-10:] if len(digits) >= 7 else digits


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    s = str(value).strip().translate(_TRANS)
    s = " ".join(s.split())
    return s.casefold()


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def name_similarity(a: str | None, b: str | None) -> float:
    na, nb = normalize_name(a), normalize_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


@dataclass(frozen=True)
class MatchResult:
    key: str  # identifier of matched record (e.g. contact id as str)
    reason: str  # mobile | phone | email | name_fuzzy
    score: float = 1.0


def match_against_index(
    *,
    mobile: str = "",
    phone: str = "",
    email: str = "",
    name: str = "",
    by_mobile: dict[str, str],
    by_phone: dict[str, str],
    by_email: dict[str, str],
    name_entries: Sequence[tuple[str, str]],
    name_threshold: float = DEFAULT_NAME_THRESHOLD,
) -> Optional[MatchResult]:
    """
    name_entries: list of (normalized_or_display_name, key).
    Indexes map normalized field → key.
    """
    m = normalize_phone(mobile)
    if m and m in by_mobile:
        return MatchResult(by_mobile[m], "mobile", 1.0)
    # also try last-10 core
    mc = phone_core(mobile)
    if mc and len(mc) >= 7:
        for k, key in by_mobile.items():
            if phone_core(k) == mc:
                return MatchResult(key, "mobile", 0.95)

    p = normalize_phone(phone)
    if p and p in by_phone:
        return MatchResult(by_phone[p], "phone", 1.0)
    pc = phone_core(phone)
    if pc and len(pc) >= 7:
        for k, key in by_phone.items():
            if phone_core(k) == pc:
                return MatchResult(key, "phone", 0.95)

    em = normalize_email(email)
    if em and em in by_email:
        return MatchResult(by_email[em], "email", 1.0)

    if name and name_entries:
        best_key = None
        best = 0.0
        for other_name, key in name_entries:
            sc = name_similarity(name, other_name)
            if sc > best:
                best, best_key = sc, key
        if best_key is not None and best >= name_threshold:
            return MatchResult(best_key, "name_fuzzy", best)

    return None


def cluster_duplicates(
    items: Sequence[T],
    *,
    get_id: Callable[[T], int],
    get_mobile: Callable[[T], str],
    get_phone: Callable[[T], str],
    get_email: Callable[[T], str],
    get_name: Callable[[T], str],
    name_threshold: float = DEFAULT_NAME_THRESHOLD,
) -> list[list[T]]:
    """
    Partition items into groups of 2+ that share exact contact keys or fuzzy names.
    Uses Union-Find style linking.
    """
    n = len(items)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    by_mobile: dict[str, int] = {}
    by_phone: dict[str, int] = {}
    by_email: dict[str, int] = {}
    by_core: dict[str, int] = {}

    for i, it in enumerate(items):
        for val, bucket in (
            (normalize_phone(get_mobile(it)), by_mobile),
            (normalize_phone(get_phone(it)), by_phone),
            (normalize_email(get_email(it)), by_email),
        ):
            if not val:
                continue
            if val in bucket:
                union(i, bucket[val])
            else:
                bucket[val] = i
        for raw in (get_mobile(it), get_phone(it)):
            core = phone_core(raw)
            if len(core) >= 7:
                if core in by_core:
                    union(i, by_core[core])
                else:
                    by_core[core] = i

    # Fuzzy name pairs — O(n²) acceptable for shop-scale lists (< a few thousand)
    names = [get_name(it) for it in items]
    for i in range(n):
        if not normalize_name(names[i]):
            continue
        for j in range(i + 1, n):
            if find(i) == find(j):
                continue
            if name_similarity(names[i], names[j]) >= name_threshold:
                union(i, j)

    groups: dict[int, list[T]] = {}
    for i, it in enumerate(items):
        groups.setdefault(find(i), []).append(it)

    return [g for g in groups.values() if len(g) >= 2]
