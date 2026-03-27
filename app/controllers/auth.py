from fastapi import APIRouter, Depends

from app.config.jwt import (
    create_access_token,
    verify_access_token,
    verify_refresh_token,
)
from app.repositories.user_repository import UserRepository
from app.config.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.schemas.schemas import LoginSchema, TokenResponse, UserRequest, UserResponse

auth_router = APIRouter(prefix='/auth', tags=['auth'])


async def get_service(db: AsyncSession = Depends(get_db)):
    repository = UserRepository(db)
    return UserService(repository)


@auth_router.post('/register', response_model=UserResponse, status_code=201)
async def create(user_data: UserRequest, service: UserService = Depends(get_service)):
    response = await service.create_user(user_data)
    return UserResponse.model_validate(response)


@auth_router.post('/login', response_model=TokenResponse, status_code=200)
async def login(login_data: LoginSchema, service: UserService = Depends(get_service)):
    access_token, refresh_token = await service.login_user(login_data)
    return TokenResponse(access=access_token, refresh=refresh_token)


@auth_router.get('/refresh', status_code=200)
async def refresh(user_id: str = Depends(verify_refresh_token)):
    new_access_token = create_access_token(user_id)

    return {'detail': 'Access token created', 'access_token': new_access_token}


@auth_router.get('/me', status_code=200, response_model=UserResponse)
async def me(
    user_id: str = Depends(verify_access_token),
    service: UserService = Depends(get_service),
):
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)
