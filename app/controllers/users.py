from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.config.jwt import (
    owner_required,
    verify_access_token,
)
from app.repositories.user_repository import UserRepository
from app.schemas.schemas import (
    UserRequest,
    UserResponse,
)
from app.services.user_service import UserService

user_router = APIRouter(prefix='/users', tags=['users'])  # tags é o nome no swagger


async def get_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


@user_router.post('/register', response_model=UserResponse, status_code=201)
async def create(user_data: UserRequest, service: UserService = Depends(get_service)):
    response = await service.create_user(user_data)
    return UserResponse.model_validate(response)


@user_router.get('/', status_code=200, response_model=dict)
async def get_all(
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0, le=100),
    service: UserService = Depends(get_service),
    current_user: str = Depends(verify_access_token),
):

    users, total, pages = await service.get_all_users(page, per_page)

    return {
        'data': [UserResponse.model_validate(u).model_dump() for u in users],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
        },
    }


@user_router.put('/{user_id}', status_code=200, response_model=UserResponse)
async def update(
    user_id: int,
    user_data: UserRequest,
    service: UserService = Depends(get_service),
    current_user: str = Depends(owner_required),
):

    response = await service.update_user(id=user_id, data=user_data)
    return UserResponse.model_validate(response)


@user_router.delete('/{user_id}', status_code=200)
async def delete(
    user_id: int,
    service: UserService = Depends(get_service),
    current_user: str = Depends(owner_required),
):
    await service.delete_user(user_id)

    return {'detail': f'User with ID {user_id} was deleted'}
