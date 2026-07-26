"""
Backend service layer for Contacts — READ-ONLY SLICE.

This is a narrow subset added specifically to support the Inventory
vendor-picker feature (search/select a supplier from existing Contacts).
It is NOT the full ContactService retrofit that the Contacts architectural
debt calls for — ContactForm/ContactsManager still import the Contact model
directly, and that larger retrofit is still deferred until Contacts work
resumes. This file exists so Inventory doesn't repeat the same
direct-ORM-import pattern into a *second* sub-app while that debt is
outstanding.

Known limitation: the Contact model still uses a single `contact_type`
field rather than the independent is_customer/is_vendor booleans that
contacts-mvs-spec.md was revised to require. A contact currently cannot be
both a customer and a vendor. list_vendors() below filters on
contact_type == "vendor" and will miss such dual-role contacts until that
model is updated.
"""

from dataclasses import dataclass
from typing import List, Protocol

from src.core.db.models import Contact


@dataclass(frozen=True)
class ContactDTO:
    id: int
    name: str
    mobile: str = ""
    phone: str = ""
    organization: str = ""
    contact_type: str = "customer"


class ContactService(Protocol):
    def list_vendors(self, search: str = "") -> List[ContactDTO]: ...

    def get_contact(self, contact_id: int) -> ContactDTO: ...


class LocalContactService:
    def _to_dto(self, c: Contact) -> ContactDTO:
        return ContactDTO(
            id=c.id,
            name=c.name,
            mobile=c.mobile or "",
            phone=c.phone or "",
            organization=c.organization or "",
            contact_type=c.contact_type,
        )

    def list_vendors(self, search: str = "") -> List[ContactDTO]:
        query = Contact.select().where(Contact.contact_type == "vendor")
        if search:
            query = query.where(
                Contact.name.contains(search)
                | Contact.mobile.contains(search)
                | Contact.organization.contains(search)
            )
        return [self._to_dto(c) for c in query.order_by(Contact.name)]

    def get_contact(self, contact_id: int) -> ContactDTO:
        return self._to_dto(Contact.get_by_id(contact_id))
