"""
Backend service layer for Contacts.

Full MVS ContactService: CRUD + customer/vendor filtered lists + VCF I/O.
UI and other sub-apps must use this Protocol — never import the Contact
model directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Protocol, Sequence, Union

from peewee import DoesNotExist

from src.apps.contacts.duplicate_logic import (
    DEFAULT_NAME_THRESHOLD,
    cluster_duplicates,
    match_against_index,
    normalize_email as _norm_email,
    normalize_name as _norm_name,
    normalize_phone as _dup_norm_phone,
)
from src.apps.contacts.vcf import (
    MAX_VCF_BYTES,
    VCardData,
    VcfParseResult,
    cards_to_vcf,
    parse_vcf_text,
)
from src.core.db.models import Contact, Item, Purchase, Receipt, db
from src.core.errors import ContactError, ContactInUseError, ContactServiceError

# Duplicate policy for selective import
DUP_SKIP = "skip"
DUP_MERGE = "merge"
DUP_CREATE = "create"


def normalize_phone(value: str | None) -> str:
    """Strip spaces/separators from pasted phone numbers; keep digits and leading +."""
    if not value:
        return ""
    out: list[str] = []
    for ch in str(value).strip():
        if ch.isdigit():
            out.append(ch)
        elif ch == "+" and not out:
            out.append(ch)
    return "".join(out)


@dataclass(frozen=True)
class ContactDTO:
    id: Optional[int]
    name: str
    phone: str = ""
    mobile: str = ""
    email: str = ""
    organization: str = ""
    title: str = ""
    address: str = ""
    is_customer: bool = True
    is_vendor: bool = False
    tags: str = ""
    note: str = ""
    tasks: str = ""


@dataclass(frozen=True)
class VcfImportReport:
    created: int = 0
    merged: int = 0
    skipped: int = 0
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class VcfPreviewRow:
    """One parsed card plus optional match against an existing contact."""

    index: int
    card: VCardData
    match_id: Optional[int] = None
    match_name: str = ""
    match_reason: str = ""  # mobile | phone | email | name_fuzzy
    match_score: float = 0.0


class ContactService(Protocol):
    def create_contact(
        self,
        name: str,
        phone: str = "",
        mobile: str = "",
        email: str = "",
        organization: str = "",
        title: str = "",
        address: str = "",
        is_customer: bool = True,
        is_vendor: bool = False,
        tags: str = "",
        note: str = "",
        tasks: str = "",
    ) -> ContactDTO: ...

    def update_contact(self, contact_id: int, **fields) -> ContactDTO: ...

    def get_contact(self, contact_id: int) -> ContactDTO: ...

    def list_contacts(self, search: str = "") -> List[ContactDTO]: ...

    def list_customers(self, search: str = "") -> List[ContactDTO]: ...

    def list_vendors(self, search: str = "") -> List[ContactDTO]: ...

    def delete_contact(self, contact_id: int) -> None: ...

    def read_vcf_source(self, source: Union[str, Path, bytes]) -> str: ...

    def preview_vcf(
        self, source: Union[str, Path, bytes]
    ) -> tuple[list[VcfPreviewRow], tuple[str, ...]]: ...

    def import_vcf_cards(
        self,
        cards: Sequence[VCardData],
        *,
        duplicate_policy: str = DUP_SKIP,
        default_is_customer: bool = True,
        default_is_vendor: bool = False,
    ) -> VcfImportReport: ...

    def import_vcf(
        self,
        source: Union[str, Path, bytes],
        *,
        default_is_customer: bool = True,
        default_is_vendor: bool = False,
    ) -> VcfImportReport: ...


    def find_duplicate_groups(
        self, *, name_threshold: float = DEFAULT_NAME_THRESHOLD
    ) -> list[list[ContactDTO]]:
        """Groups of existing contacts that look like duplicates (exact or fuzzy name)."""
        contacts = self.list_contacts()
        return cluster_duplicates(
            contacts,
            get_id=lambda c: c.id or 0,
            get_mobile=lambda c: c.mobile,
            get_phone=lambda c: c.phone,
            get_email=lambda c: c.email,
            get_name=lambda c: c.name,
            name_threshold=name_threshold,
        )

    def export_vcf(self, contact_ids: Optional[List[int]] = None) -> str: ...


class LocalContactService:
    def _to_dto(self, c: Contact) -> ContactDTO:
        return ContactDTO(
            id=c.id,
            name=c.name,
            phone=c.phone or "",
            mobile=c.mobile or "",
            email=c.email or "",
            organization=c.organization or "",
            title=c.title or "",
            address=c.address or "",
            is_customer=bool(c.is_customer),
            is_vendor=bool(c.is_vendor),
            tags=c.tags or "",
            note=c.note or "",
            tasks=c.tasks or "",
        )

    def _validate_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ContactServiceError("نام الزامی است")

    def create_contact(
        self,
        name: str,
        phone: str = "",
        mobile: str = "",
        email: str = "",
        organization: str = "",
        title: str = "",
        address: str = "",
        is_customer: bool = True,
        is_vendor: bool = False,
        tags: str = "",
        note: str = "",
        tasks: str = "",
    ) -> ContactDTO:
        self._validate_name(name)
        c = Contact.create(
            name=name.strip(),
            phone=normalize_phone(phone) or None,
            mobile=normalize_phone(mobile) or None,
            email=email or None,
            organization=organization or None,
            title=title or None,
            address=address or None,
            is_customer=is_customer,
            is_vendor=is_vendor,
            tags=tags or None,
            note=note or None,
            tasks=tasks or None,
        )
        return self._to_dto(c)

    def update_contact(self, contact_id: int, **fields) -> ContactDTO:
        try:
            c = Contact.get_by_id(contact_id)
        except DoesNotExist:
            raise ContactServiceError("مخاطب مورد نظر یافت نشد")

        if "name" in fields:
            self._validate_name(fields["name"])
            c.name = fields["name"].strip()

        for key in (
            "phone",
            "mobile",
            "email",
            "organization",
            "title",
            "address",
            "tags",
            "note",
            "tasks",
        ):
            if key in fields:
                val = fields[key]
                if key in ("phone", "mobile"):
                    val = normalize_phone(val) if val else None
                setattr(c, key, val if val else None)

        if "is_customer" in fields:
            c.is_customer = bool(fields["is_customer"])
        if "is_vendor" in fields:
            c.is_vendor = bool(fields["is_vendor"])

        c.save()
        return self._to_dto(c)

    def get_contact(self, contact_id: int) -> ContactDTO:
        try:
            return self._to_dto(Contact.get_by_id(contact_id))
        except DoesNotExist:
            raise ContactServiceError("مخاطب مورد نظر یافت نشد")

    def _search_query(self, base, search: str):
        if not search:
            return base
        return base.where(
            Contact.name.contains(search)
            | Contact.mobile.contains(search)
            | Contact.phone.contains(search)
            | Contact.organization.contains(search)
            | Contact.email.contains(search)
        )

    def list_contacts(self, search: str = "") -> List[ContactDTO]:
        query = self._search_query(Contact.select(), search)
        return [self._to_dto(c) for c in query.order_by(Contact.name)]

    def list_customers(self, search: str = "") -> List[ContactDTO]:
        query = self._search_query(
            Contact.select().where(Contact.is_customer == True),  # noqa: E712
            search,
        )
        return [self._to_dto(c) for c in query.order_by(Contact.name)]

    def list_vendors(self, search: str = "") -> List[ContactDTO]:
        query = self._search_query(
            Contact.select().where(Contact.is_vendor == True),  # noqa: E712
            search,
        )
        return [self._to_dto(c) for c in query.order_by(Contact.name)]

    def delete_contact(self, contact_id: int) -> None:
        try:
            Contact.get_by_id(contact_id)
        except DoesNotExist:
            raise ContactServiceError("مخاطب مورد نظر یافت نشد")

        reasons: list[str] = []
        if Receipt.select().where(Receipt.contact == contact_id).exists():
            reasons.append("فاکتور فروش")
        if Purchase.select().where(Purchase.vendor_contact == contact_id).exists():
            reasons.append("سند خرید")
        if Item.select().where(Item.vendor_contact == contact_id).exists():
            reasons.append("کالای دارای فروشنده پیش‌فرض")

        if reasons:
            raise ContactInUseError(
                "حذف ممکن نیست؛ این مخاطب در موارد زیر استفاده شده است: "
                + "، ".join(reasons)
            )

        Contact.get_by_id(contact_id).delete_instance()

    # ----- VCF -----

    def read_vcf_source(self, source: Union[str, Path, bytes]) -> str:
        """Load VCF bytes/path/text with size limit; return decoded text."""
        if isinstance(source, bytes):
            if len(source) > MAX_VCF_BYTES:
                raise ContactServiceError(
                    f"حجم داده از سقف {MAX_VCF_BYTES // (1024 * 1024)} مگابایت بیشتر است"
                )
            raw = source
        elif isinstance(source, (str, Path)):
            path = Path(source)
            # plain VCF text passed as str (no path) — rare
            if not path.is_file() and isinstance(source, str) and "BEGIN:VCARD" in source.upper():
                return source
            if not path.is_file():
                raise ContactServiceError("فایل VCF یافت نشد")
            size = path.stat().st_size
            if size > MAX_VCF_BYTES:
                raise ContactServiceError(
                    f"حجم فایل از سقف {MAX_VCF_BYTES // (1024 * 1024)} مگابایت بیشتر است"
                )
            raw = path.read_bytes()
        else:
            raw = str(source).encode("utf-8")

        for enc in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1", errors="replace")

    def _build_dup_index(self):
        """Indexes for exact fields + name list for fuzzy match."""
        by_mobile: dict[str, ContactDTO] = {}
        by_phone: dict[str, ContactDTO] = {}
        by_email: dict[str, ContactDTO] = {}
        by_id: dict[int, ContactDTO] = {}
        name_entries: list[tuple[str, str]] = []  # (name, id_str)
        for c in self.list_contacts():
            by_id[c.id] = c
            m = normalize_phone(c.mobile)
            p = normalize_phone(c.phone)
            if m and m not in by_mobile:
                by_mobile[m] = c
            if p and p not in by_phone:
                by_phone[p] = c
            em = _norm_email(c.email)
            if em and em not in by_email:
                by_email[em] = c
            if c.name:
                name_entries.append((c.name, str(c.id)))
        return by_mobile, by_phone, by_email, by_id, name_entries

    def _match_card(
        self,
        card: VCardData,
        by_mobile: dict,
        by_phone: dict,
        by_email: dict,
        by_id: dict,
        name_entries: list,
        *,
        name_threshold: float = DEFAULT_NAME_THRESHOLD,
    ) -> tuple[Optional[ContactDTO], str, float]:
        mr = match_against_index(
            mobile=card.mobile,
            phone=card.phone,
            email=card.email,
            name=card.name,
            by_mobile={k: str(v.id) for k, v in by_mobile.items()},
            by_phone={k: str(v.id) for k, v in by_phone.items()},
            by_email={k: str(v.id) for k, v in by_email.items()},
            name_entries=name_entries,
            name_threshold=name_threshold,
        )
        if not mr:
            return None, "", 0.0
        dto = by_id.get(int(mr.key))
        return dto, mr.reason, mr.score

    def preview_vcf(
        self, source: Union[str, Path, bytes]
    ) -> tuple[list[VcfPreviewRow], tuple[str, ...]]:
        text = self.read_vcf_source(source)
        parsed: VcfParseResult = parse_vcf_text(text)
        if parsed.errors and not parsed.cards:
            raise ContactServiceError("؛ ".join(parsed.errors))

        by_mobile, by_phone, by_email, by_id, name_entries = self._build_dup_index()
        rows: list[VcfPreviewRow] = []
        for i, card in enumerate(parsed.cards):
            match, reason, score = self._match_card(
                card, by_mobile, by_phone, by_email, by_id, name_entries
            )
            rows.append(
                VcfPreviewRow(
                    index=i,
                    card=card,
                    match_id=match.id if match else None,
                    match_name=match.name if match else "",
                    match_reason=reason,
                    match_score=score,
                )
            )
        return rows, tuple(parsed.errors)

    def _merge_into(self, contact_id: int, card: VCardData) -> ContactDTO:
        """Fill empty fields on existing contact from VCF card; keep existing when both set."""
        existing = self.get_contact(contact_id)
        fields: dict = {}
        # Prefer existing non-empty; only overwrite empties
        if not (existing.phone or "").strip() and card.phone:
            fields["phone"] = card.phone
        if not (existing.mobile or "").strip() and card.mobile:
            fields["mobile"] = card.mobile
        if not (existing.email or "").strip() and card.email:
            fields["email"] = card.email
        if not (existing.organization or "").strip() and card.organization:
            fields["organization"] = card.organization
        if not (existing.title or "").strip() and card.title:
            fields["title"] = card.title
        if not (existing.address or "").strip() and card.address:
            fields["address"] = card.address
        if not (existing.tags or "").strip() and card.tags:
            fields["tags"] = card.tags
        elif card.tags and existing.tags and card.tags not in existing.tags:
            fields["tags"] = f"{existing.tags}, {card.tags}"
        if not (existing.note or "").strip() and card.note:
            fields["note"] = card.note
        if not fields:
            return existing
        return self.update_contact(contact_id, **fields)

    def import_vcf_cards(
        self,
        cards: Sequence[VCardData],
        *,
        duplicate_policy: str = DUP_SKIP,
        default_is_customer: bool = True,
        default_is_vendor: bool = False,
    ) -> VcfImportReport:
        """Import already-parsed cards with duplicate policy. Uses one DB transaction."""
        if duplicate_policy not in (DUP_SKIP, DUP_MERGE, DUP_CREATE):
            duplicate_policy = DUP_SKIP

        by_mobile, by_phone, by_email, by_id, name_entries = self._build_dup_index()
        created = merged = skipped = 0
        errors: list[str] = []

        with db.atomic():
            for card in cards:
                if not (card.name or "").strip():
                    skipped += 1
                    continue
                match, _reason, _score = self._match_card(
                    card, by_mobile, by_phone, by_email, by_id, name_entries
                )
                try:
                    if match is None or duplicate_policy == DUP_CREATE:
                        dto = self.create_contact(
                            name=card.name,
                            phone=card.phone,
                            mobile=card.mobile,
                            email=card.email,
                            organization=card.organization,
                            title=card.title,
                            address=card.address,
                            tags=card.tags,
                            note=card.note,
                            is_customer=default_is_customer,
                            is_vendor=default_is_vendor,
                        )
                        created += 1
                        # keep index fresh within batch
                        m = normalize_phone(dto.mobile)
                        p = normalize_phone(dto.phone)
                        if m:
                            by_mobile[m] = dto
                        if p:
                            by_phone[p] = dto
                        em = (dto.email or "").strip().lower()
                        if em:
                            by_email[em] = dto
                    elif duplicate_policy == DUP_SKIP:
                        skipped += 1
                    else:  # MERGE
                        self._merge_into(match.id, card)
                        merged += 1
                except ContactServiceError as exc:
                    skipped += 1
                    errors.append(getattr(exc, "message_fa", None) or str(exc))

        return VcfImportReport(
            created=created,
            merged=merged,
            skipped=skipped,
            errors=tuple(errors[:20]),
        )

    def import_vcf(
        self,
        source: Union[str, Path, bytes],
        *,
        default_is_customer: bool = True,
        default_is_vendor: bool = False,
        duplicate_policy: str = DUP_SKIP,
    ) -> VcfImportReport:
        """Parse whole file and import all cards (no UI selection). Prefer preview + import_vcf_cards."""
        text = self.read_vcf_source(source)
        parsed = parse_vcf_text(text)
        if parsed.errors and not parsed.cards:
            raise ContactServiceError("؛ ".join(parsed.errors))
        return self.import_vcf_cards(
            parsed.cards,
            duplicate_policy=duplicate_policy,
            default_is_customer=default_is_customer,
            default_is_vendor=default_is_vendor,
        )


    def find_duplicate_groups(
        self, *, name_threshold: float = DEFAULT_NAME_THRESHOLD
    ) -> list[list[ContactDTO]]:
        """Groups of existing contacts that look like duplicates (exact or fuzzy name)."""
        contacts = self.list_contacts()
        return cluster_duplicates(
            contacts,
            get_id=lambda c: c.id or 0,
            get_mobile=lambda c: c.mobile,
            get_phone=lambda c: c.phone,
            get_email=lambda c: c.email,
            get_name=lambda c: c.name,
            name_threshold=name_threshold,
        )

    def export_vcf(self, contact_ids: Optional[List[int]] = None) -> str:
        if contact_ids is not None:
            contacts = []
            for cid in contact_ids:
                try:
                    contacts.append(self.get_contact(cid))
                except ContactServiceError:
                    continue
        else:
            contacts = self.list_contacts()

        cards = [
            VCardData(
                name=c.name,
                phone=c.phone,
                mobile=c.mobile,
                email=c.email,
                organization=c.organization,
                title=c.title,
                address=c.address,
                tags=c.tags,
                note=c.note,
            )
            for c in contacts
        ]
        return cards_to_vcf(cards)
