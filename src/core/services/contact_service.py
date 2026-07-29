"""
Backend service layer for Contacts.

Full MVS ContactService: CRUD + customer/vendor filtered lists + VCF I/O.
UI and other sub-apps must use this Protocol — never import the Contact
model directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Protocol, Union

from peewee import DoesNotExist

from src.apps.contacts.vcf import (
    MAX_VCF_BYTES,
    VCardData,
    VcfParseResult,
    cards_to_vcf,
    parse_vcf_text,
)
from src.core.db.models import Contact, Item, Purchase, Receipt
from src.core.errors import ContactError, ContactInUseError, ContactServiceError


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
    created: int
    skipped: int
    errors: tuple[str, ...] = ()


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

    def import_vcf(
        self,
        source: Union[str, Path, bytes],
        *,
        default_is_customer: bool = True,
        default_is_vendor: bool = False,
    ) -> VcfImportReport: ...

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

    def import_vcf(
        self,
        source: Union[str, Path, bytes],
        *,
        default_is_customer: bool = True,
        default_is_vendor: bool = False,
    ) -> VcfImportReport:
        """Import contacts from a .vcf path, raw bytes, or text string.

        Security: size limit, text decode only, allowlisted properties in parser.
        Does not deduplicate (MVS). Defaults roles to customer unless specified.
        """
        if isinstance(source, (str, Path)) and not isinstance(source, bytes):
            path = Path(source)
            if not path.is_file():
                raise ContactServiceError("فایل VCF یافت نشد")
            size = path.stat().st_size
            if size > MAX_VCF_BYTES:
                raise ContactServiceError(
                    f"حجم فایل از سقف {MAX_VCF_BYTES // (1024 * 1024)} مگابایت بیشتر است"
                )
            raw = path.read_bytes()
        elif isinstance(source, bytes):
            if len(source) > MAX_VCF_BYTES:
                raise ContactServiceError(
                    f"حجم داده از سقف {MAX_VCF_BYTES // (1024 * 1024)} مگابایت بیشتر است"
                )
            raw = source
        else:
            raw = str(source).encode("utf-8")

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")

        parsed: VcfParseResult = parse_vcf_text(text)
        if parsed.errors and not parsed.cards:
            raise ContactServiceError("؛ ".join(parsed.errors))

        created = 0
        for card in parsed.cards:
            try:
                self.create_contact(
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
            except ContactServiceError:
                parsed.skipped += 1

        return VcfImportReport(
            created=created,
            skipped=parsed.skipped,
            errors=tuple(parsed.errors),
        )

    def export_vcf(self, contact_ids: Optional[List[int]] = None) -> str:
        """Export contacts as VCF 3.0 text. None = all contacts."""
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
