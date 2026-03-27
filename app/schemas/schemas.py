from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints
from typing import Annotated, List, Dict

RequiredStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=100)]
CleanEmail = Annotated[
    EmailStr, StringConstraints(max_length=100, to_lower=True, strip_whitespace=True)
]
PhoneStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r'^\d{10,11}$')
]


class UserRequest(BaseModel):
    name: RequiredStr
    email: CleanEmail
    password: PasswordStr


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ContactRequest(BaseModel):
    name: RequiredStr
    phone: PhoneStr | None = None
    email: CleanEmail | None = None


class ContactResponse(BaseModel):
    id: int
    name: str
    phone: str | None
    email: EmailStr | None

    model_config = ConfigDict(from_attributes=True)


class LoginSchema(BaseModel):
    email: CleanEmail
    password: PasswordStr


class TokenResponse(BaseModel):
    access: str
    refresh: str


class ValidationErrorResponse(BaseModel):
    error: List[Dict[str, str]]

    model_config = {
        'json_schema_extra': {
            'example': {
                'error': [
                    {
                        'password': "The field 'password must be at least 8 characters long"
                    }
                ]
            }
        }
    }
