from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.config.jwt import owner_required
from app.repositories.contact_repository import ContactRepository
from app.repositories.user_repository import UserRepository
from app.schemas.schemas import ContactRequest, ContactResponse
from app.services.contact_service import ContactService

contact_router: APIRouter = APIRouter(prefix='/users', tags=['contacts'])


async def get_service(db: AsyncSession = Depends(get_db)) -> ContactService:
    user_repository = UserRepository(db)
    contact_repository = ContactRepository(db)
    return ContactService(
        contact_repository=contact_repository, user_repository=user_repository
    )


@contact_router.get(
    '/{user_id}/contacts/',
    response_model=dict,
    status_code=200,
)
async def get_all(
    user_id: int,
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0, le=100),
    service: ContactService = Depends(get_service),
    current_user: str = Depends(owner_required),
):
    contacts, total, pages = await service.get_all_contacts(user_id, page, per_page)
    return {
        'data': [ContactResponse.model_validate(c) for c in contacts],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
        },
    }


@contact_router.post(
    '/{user_id}/contacts/', response_model=ContactResponse, status_code=201
)
async def create(
    user_id: int,
    contact_data: ContactRequest,
    service: ContactService = Depends(get_service),
    current_user: str = Depends(owner_required),
):
    return await service.create_contact(user_id=user_id, data=contact_data)


@contact_router.delete('/{user_id}/contacts/{id}', status_code=200)
async def delete(
    user_id: int,
    id: int,
    service: ContactService = Depends(get_service),
    current_user: str = Depends(owner_required),
):
    await service.delete_contact(user_id, id)

    return {'detail': f'Contact with ID {id} was deleted'}


@contact_router.put(
    '/{user_id}/contacts/{id}', response_model=ContactResponse, status_code=200
)
async def update(
    user_id: int,
    id: int,
    contact_data: ContactRequest,
    service: ContactService = Depends(get_service),
    current_user: str = Depends(owner_required),
):
    return await service.update_contact(user_id=user_id, id=id, data=contact_data)
