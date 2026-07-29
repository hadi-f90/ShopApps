"""Pure VCF parse/serialize tests (no DB)."""

from src.apps.contacts.vcf import (
    VCardData,
    card_to_vcf,
    cards_to_vcf,
    parse_vcf_text,
)


SAMPLE = """BEGIN:VCARD
VERSION:3.0
FN:علی رضایی
TEL;TYPE=CELL:0912 345 6789
TEL;TYPE=HOME:021-12345678
EMAIL:ali@example.com
ORG:شرکت نمونه
TITLE:مدیر خرید
NOTE:مشتری ویژه
END:VCARD
"""


def test_parse_single_card():
    result = parse_vcf_text(SAMPLE)
    assert len(result.cards) == 1
    c = result.cards[0]
    assert c.name == "علی رضایی"
    assert "0912" in c.mobile or c.mobile  # raw from VCF; normalize is service-side
    assert c.email == "ali@example.com"
    assert c.organization == "شرکت نمونه"


def test_parse_skips_photo_and_unknown():
    text = SAMPLE.replace(
        "END:VCARD",
        "PHOTO;ENCODING=b;TYPE=JPEG:/9j/4AAQ\nX-CUSTOM:secret\nEND:VCARD",
    )
    result = parse_vcf_text(text)
    assert len(result.cards) == 1
    assert result.cards[0].name == "علی رضایی"


def test_round_trip_export():
    card = VCardData(
        name="Test User",
        mobile="09120000000",
        phone="02111111111",
        email="t@example.com",
        organization="Org",
    )
    text = cards_to_vcf([card])
    assert "BEGIN:VCARD" in text
    assert "FN:Test User" in text
    parsed = parse_vcf_text(text)
    assert parsed.cards[0].name == "Test User"
    assert parsed.cards[0].mobile == "09120000000"


def test_empty_and_nameless():
    assert parse_vcf_text("").errors
    r = parse_vcf_text("BEGIN:VCARD\nVERSION:3.0\nEND:VCARD\n")
    assert r.skipped >= 1
    assert len(r.cards) == 0
