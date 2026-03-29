from fastapi import APIRouter, Depends, BackgroundTasks

from app.config.jwt import (
    create_access_token,
    verify_access_token,
    verify_refresh_token,
)
from app.repositories.user_repository import UserRepository
from app.config.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.schemas.schemas import (
    LoginSchema,
    TokenResponse,
    UserResponse,
    EmailSchema,
    ResetPasswordRequest,
)
from app.services.email_service import EmailService
from app.repositories.token_repository import TokenRepository
from app.config.email import fm

auth_router = APIRouter(prefix='/auth', tags=['auth'])


async def get_service(db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)
    email_service = EmailService(mail_engine=fm)
    return AuthService(
        email_service=email_service, token_repo=token_repo, user_repo=user_repo
    )


@auth_router.post('/login', response_model=TokenResponse, status_code=200)
async def login(login_data: LoginSchema, service: AuthService = Depends(get_service)):
    access_token, refresh_token = await service.login_user(login_data)
    return TokenResponse(access=access_token, refresh=refresh_token)


@auth_router.get('/refresh', status_code=200)
async def refresh(user_id: str = Depends(verify_refresh_token)):
    new_access_token = create_access_token(user_id)

    return {'detail': 'Access token created', 'access_token': new_access_token}


@auth_router.get('/me', status_code=200, response_model=UserResponse)
async def me(
    user_id: str = Depends(verify_access_token),
    service: AuthService = Depends(get_service),
):
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@auth_router.post('/forgot-password', status_code=200)
async def forgot_password(
    data: EmailSchema,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_service),
):
    await service.email_forgot_password_link(data, background_tasks)
    return {'detail': 'A email with password reset link has been sent to you.'}


@auth_router.post('/reset-password', status_code=200)
async def reset_password(
    data: ResetPasswordRequest, service: AuthService = Depends(get_service)
):
    await service.reset_password(data)
    return {'detail': 'Password updated successfully'}
