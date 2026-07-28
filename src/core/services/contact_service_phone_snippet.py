"""
Snippet — merge into src/core/services/contact_service.py

1. Add normalize_phone() at module level (below imports).
2. Call it in create_contact / update_contact for phone and mobile.
"""


def normalize_phone(value: str | None) -> str:
    """Remove spaces and common separators from pasted phone numbers.

    Keeps digits and a single leading '+'. Does not validate Iranian format
    (that can be Phase 2). Empty input → empty string.
    """
    if not value:
        return ""
    s = str(value).strip()
    out: list[str] = []
    for i, ch in enumerate(s):
        if ch.isdigit():
            out.append(ch)
        elif ch == "+" and not out:
            out.append(ch)
        # drop spaces, tabs, -, –, —, (), dots, etc.
    return "".join(out)


# --- In create_contact, replace phone/mobile assignment with: ---
# phone = normalize_phone(phone) or None
# mobile = normalize_phone(mobile) or None
#
# --- In update_contact, inside the field loop: ---
# if key in ("phone", "mobile"):
#     val = normalize_phone(val) if val else None
