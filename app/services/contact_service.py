from app.errors.exceptions import ForbiddenError, NotFoundError
from app.models.contact import Contact
from app.repositories.contact_repository import ContactRepository
from app.repositories.user_repository import UserRepository


class ContactService:
    def __init__(
        self,
        contact_repository: ContactRepository,
        user_repository: UserRepository,
    ):
        self.repository = contact_repository
        self.user_repository = user_repository

    async def create_contact(self, user_id: int, data):
        if not await self.user_repository.exists_by_id(user_id):
            raise NotFoundError(detail='User not found')

        contact = Contact(name=data.name, phone=data.phone, email=data.email)
        return await self.repository.save(user_id, contact)

    async def delete_contact(self, user_id: int, id: int):
        contact = await self.repository.find_by_id(id)
        if contact is None:
            raise NotFoundError(detail='Contact not found')

        if contact.user_id != user_id:
            raise ForbiddenError(
                detail=f'User {user_id} does not have access to this contact {id}.'
            )

        await self.repository.delete(id)

    async def update_contact(self, user_id: int, id: int, data):
        contact = await self.repository.find_by_id(id)

        if contact is None:
            raise NotFoundError(detail='Contact not found')

        if contact.user_id != user_id:
            raise ForbiddenError(
                detail=f'User {user_id} does not have access to this contact {id}'
            )

        contact.name = data.name
        contact.email = data.email
        contact.phone = data.phone

        return await self.repository.save(data=contact)

    async def get_all_contacts(self, user_id: int, page, per_page):
        if not await self.user_repository.exists_by_id(user_id):
            raise NotFoundError(detail='User not found')

        items, total = await self.repository.get_all(user_id, page, per_page)
        pages = (total + per_page - 1) // per_page
        return items, total, pages
