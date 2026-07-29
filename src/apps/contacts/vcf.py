"""
VCF (vCard) parse/serialize for Contacts MVS.

Pure functions — no Peewee, no Qt. Security constraints (Security Agent):
- Parse as text data only; never execute or eval file contents.
- Allowlisted property names only; unknown properties ignored.
- PHOTO / binary values are skipped (no attachment import in MVS).
- Callers must enforce file size and contact-count limits before/after parse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

# Properties we map into Contact fields. Everything else is ignored.
ALLOWED_PROPERTIES = frozenset(
    {
        "BEGIN",
        "END",
        "VERSION",
        "FN",
        "N",
        "TEL",
        "EMAIL",
        "ORG",
        "TITLE",
        "ADR",
        "NOTE",
        "CATEGORIES",  # maps to tags
    }
)

MAX_VCF_BYTES = 2 * 1024 * 1024  # 2 MiB
MAX_CARDS_PER_IMPORT = 500


@dataclass
class VCardData:
    """One parsed vCard → fields suitable for ContactService.create_contact."""

    name: str = ""
    phone: str = ""
    mobile: str = ""
    email: str = ""
    organization: str = ""
    title: str = ""
    address: str = ""
    tags: str = ""
    note: str = ""


@dataclass
class VcfParseResult:
    cards: List[VCardData] = field(default_factory=list)
    skipped: int = 0  # cards without a usable name
    errors: List[str] = field(default_factory=list)


def _unfold(text: str) -> List[str]:
    """RFC 6350 line unfolding: continuation lines start with space or tab."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines: List[str] = []
    for line in raw:
        if lines and line.startswith((" ", "\t")):
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _split_prop(line: str) -> tuple[str, str]:
    """Return (property_name_upper, value). Drops parameters after PROP."""
    if ":" not in line:
        return "", ""
    left, value = line.split(":", 1)
    name = left.split(";", 1)[0].strip().upper()
    # group.PREFIX like item1.TEL → TEL
    if "." in name:
        name = name.split(".")[-1]
    return name, value.strip()


def _is_mobile_tel(params_and_name: str) -> bool:
    upper = params_and_name.upper()
    return any(
        t in upper
        for t in ("CELL", "MOBILE", "IPHONE", "TYPE=CELL", "TYPE=MOBILE")
    )


def parse_vcf_text(text: str) -> VcfParseResult:
    """Parse VCF text into VCardData list. Invalid structure yields errors, not raise."""
    result = VcfParseResult()
    if not text or not text.strip():
        result.errors.append("فایل خالی است")
        return result

    lines = _unfold(text)
    current: Optional[dict] = None
    tel_home: List[str] = []
    tel_cell: List[str] = []

    def _flush():
        nonlocal current, tel_home, tel_cell
        if current is None:
            return
        name = (current.get("fn") or current.get("n") or "").strip()
        if not name:
            result.skipped += 1
            current = None
            tel_home, tel_cell = [], []
            return
        phone = tel_home[0] if tel_home else (tel_cell[1] if len(tel_cell) > 1 else "")
        mobile = tel_cell[0] if tel_cell else ""
        # If only one TEL and not marked cell, treat as phone
        if not mobile and not phone and tel_home:
            phone = tel_home[0]
        if not mobile and tel_cell:
            mobile = tel_cell[0]
        if not phone and len(tel_cell) > 1:
            phone = tel_cell[1]
        result.cards.append(
            VCardData(
                name=name,
                phone=phone,
                mobile=mobile,
                email=current.get("email", ""),
                organization=current.get("org", ""),
                title=current.get("title", ""),
                address=current.get("adr", ""),
                tags=current.get("categories", ""),
                note=current.get("note", ""),
            )
        )
        current = None
        tel_home, tel_cell = [], []

    for line in lines:
        if not line.strip():
            continue
        # Full left side for TEL type detection
        left = line.split(":", 1)[0] if ":" in line else ""
        prop, value = _split_prop(line)
        if not prop:
            continue
        if prop not in ALLOWED_PROPERTIES:
            continue  # ignore PHOTO, X-*, etc.

        if prop == "BEGIN" and value.upper() == "VCARD":
            _flush()
            current = {}
            tel_home, tel_cell = [], []
            continue
        if prop == "END" and value.upper() == "VCARD":
            _flush()
            continue
        if current is None:
            continue
        if prop == "FN":
            current["fn"] = value
        elif prop == "N" and "fn" not in current:
            # N: Family;Given;... → "Given Family" or join non-empty
            parts = [p.strip() for p in value.split(";") if p.strip()]
            if parts:
                # Prefer Given + Family order when 2+
                if len(parts) >= 2:
                    current["n"] = f"{parts[1]} {parts[0]}".strip()
                else:
                    current["n"] = parts[0]
        elif prop == "TEL":
            if _is_mobile_tel(left):
                tel_cell.append(value)
            else:
                tel_home.append(value)
        elif prop == "EMAIL" and "email" not in current:
            current["email"] = value
        elif prop == "ORG" and "org" not in current:
            current["org"] = value.split(";", 1)[0].strip()
        elif prop == "TITLE" and "title" not in current:
            current["title"] = value
        elif prop == "ADR" and "adr" not in current:
            # ADR: PO;ext;street;city;region;postcode;country
            parts = [p.strip() for p in value.split(";")]
            current["adr"] = ", ".join(p for p in parts if p)
        elif prop == "NOTE" and "note" not in current:
            current["note"] = value.replace("\\n", "\n")
        elif prop == "CATEGORIES" and "categories" not in current:
            current["categories"] = value.replace(";", ", ")

    _flush()
    if len(result.cards) > MAX_CARDS_PER_IMPORT:
        result.errors.append(
            f"تعداد مخاطبین از سقف {MAX_CARDS_PER_IMPORT} بیشتر است"
        )
        result.cards = result.cards[:MAX_CARDS_PER_IMPORT]
    return result


def escape_vcf_value(value: str) -> str:
    return (
        (value or "")
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def card_to_vcf(card: VCardData) -> str:
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{escape_vcf_value(card.name)}",
    ]
    if card.organization:
        lines.append(f"ORG:{escape_vcf_value(card.organization)}")
    if card.title:
        lines.append(f"TITLE:{escape_vcf_value(card.title)}")
    if card.mobile:
        lines.append(f"TEL;TYPE=CELL:{escape_vcf_value(card.mobile)}")
    if card.phone:
        lines.append(f"TEL;TYPE=VOICE:{escape_vcf_value(card.phone)}")
    if card.email:
        lines.append(f"EMAIL:{escape_vcf_value(card.email)}")
    if card.address:
        lines.append(f"ADR:;;{escape_vcf_value(card.address)};;;;")
    if card.tags:
        lines.append(f"CATEGORIES:{escape_vcf_value(card.tags)}")
    if card.note:
        lines.append(f"NOTE:{escape_vcf_value(card.note)}")
    lines.append("END:VCARD")
    return "\n".join(lines)


def cards_to_vcf(cards: List[VCardData]) -> str:
    return "\n".join(card_to_vcf(c) for c in cards) + ("\n" if cards else "")
