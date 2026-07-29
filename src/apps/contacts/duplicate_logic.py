"""
Pure duplicate-detection helpers for Contacts (no Peewee/Qt).

Exact match: normalized mobile, phone, or email.
Phone fuzzy: Iranian equivalents (+98… / 0098… / 09… / 9…).
Fuzzy name: Persian-normalized names via difflib.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Callable, Optional, Sequence, TypeVar

T = TypeVar("T")

DEFAULT_NAME_THRESHOLD = 0.88

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
        "\u200c": "",
        "\u200d": "",
        "\u0640": "",
    }
)


def normalize_phone(value: str | None) -> str:
    """Digits only, optional leading + kept only if present at start before digits."""
    if not value:
        return ""
    out: list[str] = []
    for ch in str(value).strip():
        if ch.isdigit():
            out.append(ch)
        elif ch == "+" and not out:
            out.append(ch)
    return "".join(out)


def phone_digits(value: str | None) -> str:
    return "".join(ch for ch in (value or "") if ch.isdigit())


def phone_match_keys(value: str | None) -> set[str]:
    """
    Equivalent phone keys for matching, e.g.:
      +989123456789  → 989123456789, 9123456789, 09123456789, …
      09123456789    → same set overlap
      9123456789     → same
    """
    digits = phone_digits(value)
    if not digits:
        return set()

    keys: set[str] = {digits}

    # International 00 prefix
    if digits.startswith("00") and len(digits) > 4:
        digits = digits[2:]
        keys.add(digits)

    # Iran country code 98
    if digits.startswith("98") and len(digits) >= 12:
        national = digits[2:]  # 9xxxxxxxxx (10 digits typical)
        keys.add(national)
        keys.add("0" + national)
        if len(national) >= 10:
            keys.add(national[-10:])
            keys.add("0" + national[-10:])

    # Leading 0 national (09xxxxxxxxx)
    if digits.startswith("0") and len(digits) >= 10:
        without0 = digits[1:]
        keys.add(without0)
        keys.add(digits[-10:] if len(digits) >= 10 else digits)
        # as if dialed with +98
        keys.add("98" + without0)
        if without0.startswith("9") and len(without0) == 10:
            keys.add("98" + without0)

    # Bare 9xxxxxxxxx (10 digits, no leading 0)
    if not digits.startswith("0") and not digits.startswith("98") and len(digits) == 10:
        keys.add("0" + digits)
        keys.add("98" + digits)

    # Always index last 10 digits when long enough
    if len(digits) >= 10:
        last10 = digits[-10:]
        keys.add(last10)
        if last10.startswith("9"):
            keys.add("0" + last10)
            keys.add("98" + last10)

    return {k for k in keys if len(k) >= 7}


def phone_core(value: str | None) -> str:
    """Preferred canonical core: last 10 digits of the national number when possible."""
    keys = phone_match_keys(value)
    if not keys:
        return ""
    # Prefer 10-digit national starting with 9
    for k in keys:
        if len(k) == 10 and k.startswith("9"):
            return k
    for k in keys:
        if len(k) == 11 and k.startswith("09"):
            return k[1:]
    digits = phone_digits(value)
    return digits[-10:] if len(digits) >= 7 else digits


def phones_equivalent(a: str | None, b: str | None) -> bool:
    ka, kb = phone_match_keys(a), phone_match_keys(b)
    return bool(ka and kb and (ka & kb))


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
    key: str
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
    Indexes map *any* phone_match_key → contact key.
    Callers should register every key from phone_match_keys when building indexes.
    """
    for raw, bucket, reason, score in (
        (mobile, by_mobile, "mobile", 1.0),
        (phone, by_phone, "phone", 1.0),
    ):
        for key in phone_match_keys(raw):
            if key in bucket:
                return MatchResult(bucket[key], reason, score)

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
    """Partition into groups of 2+ sharing phone keys, email, or fuzzy names."""
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

    by_phone_key: dict[str, int] = {}
    by_email: dict[str, int] = {}

    for i, it in enumerate(items):
        for raw in (get_mobile(it), get_phone(it)):
            for key in phone_match_keys(raw):
                if key in by_phone_key:
                    union(i, by_phone_key[key])
                else:
                    by_phone_key[key] = i
        em = normalize_email(get_email(it))
        if em:
            if em in by_email:
                union(i, by_email[em])
            else:
                by_email[em] = i

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
