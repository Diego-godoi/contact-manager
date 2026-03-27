from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from app.errors.exceptions import ForbiddenError

bearer_scheme = HTTPBearer(auto_error=False)


def create_tokens(user_id: int):
    id = str(user_id)
    access_info = {
        'sub': id,
        'type': 'access',
        'exp': datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    access_token = jwt.encode(access_info, SECRET_KEY, ALGORITHM)
    refresh_info = {
        'sub': id,
        'type': 'refresh',
        'exp': datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    refresh_token = jwt.encode(refresh_info, SECRET_KEY, ALGORITHM)
    return access_token, refresh_token


def create_access_token(user_id: int):
    info = {
        'sub': str(user_id),
        'type': 'access',
        'exp': datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(info, SECRET_KEY, ALGORITHM)


def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail='Missing token')
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        if payload.get('type') != 'access':
            raise HTTPException(status_code=401, detail='Invalid token type')
        return payload.get('sub')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid or expired token')


def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail='Missing token')
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        if payload.get('type') != 'refresh':
            raise HTTPException(status_code=401, detail='Invalid token type')
        return payload.get('sub')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid or expired token')


def owner_required(
    user_id: int, current_user: str = Depends(verify_access_token)
) -> str:
    if current_user != str(user_id):
        raise ForbiddenError(detail='This resource belongs to another user')
    return current_user
