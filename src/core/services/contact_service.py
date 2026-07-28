"""
Backend service layer for Contacts.

Full MVS ContactService: CRUD + customer/vendor filtered lists.
UI and other sub-apps must use this Protocol — never import the Contact
model directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol

from peewee import DoesNotExist

from src.core.db.models import Contact, Item, Purchase, Receipt
from src.core.errors import ContactError, ContactInUseError, ContactServiceError


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
            phone=phone or None,
            mobile=mobile or None,
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

        # Integrity: do not hard-delete if business records still point here.
        # (Security + Database agents — avoid silent SET NULL data loss.)
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
