from sqlalchemy import delete, exists, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user_id: int = None, data: Contact = None) -> Contact:
        try:
            if user_id is not None:
                data.user_id = user_id
            self.session.add(data)
            await self.session.commit()
            await self.session.refresh(data)
            return data
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error saving contact to database: {str(e)}')

    async def delete(self, id: int) -> bool:
        try:
            stmt = delete(Contact).where(Contact.id == id)

            result = await self.session.execute(
                stmt, execution_options={'synchronize_session': 'evaluate'}
            )
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise ValueError(f'Error deleting contact to database: {str(e)}')

    async def get_all(self, user_id: int, page: int, per_page: int):
        try:
            stmt_contacts = (
                select(Contact)
                .where(Contact.user_id == user_id)
                .order_by(Contact.id)
                .limit(per_page)
                .offset((page - 1) * per_page)
            )
            result_contacts = await self.session.execute(stmt_contacts)
            contacts = result_contacts.scalars().all()

            stmt_count = (
                select(func.count())
                .select_from(Contact)
                .where(Contact.user_id == user_id)
            )
            result_count = await self.session.execute(stmt_count)
            total = result_count.scalar()

            return contacts, total
        except Exception as e:
            raise ValueError(f'Error getting all contacts from database: {str(e)}')

    async def exists_by_id(self, id: int) -> bool:
        try:
            stmt = select(exists().where(Contact.id == id))
            result = await self.session.execute(stmt)
            return result.scalar()
        except Exception as e:
            raise ValueError(f'Error getting contact by id to database: {str(e)}')

    async def find_by_id(self, id: int) -> Contact:
        try:
            contact = await self.session.get(Contact, id)
            return contact
        except Exception as e:
            raise ValueError(f'Error finding contact by id to database: {str(e)}')
