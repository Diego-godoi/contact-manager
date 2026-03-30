from pytest import mark
from app.controllers.auth import get_service
from app.config.jwt import create_access_token, create_tokens
from app.errors.exceptions import InvalidCredentialsError, NotFoundError
from tests.factories import (
    LoginFactory,
    UserFactory,
    ResetPasswordRequestFactory,
    EmailSchemaFactory,
)


@mark.asyncio
class TestAuthLogin:
    async def test_login_successfully(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_access = 'access-token-123'
        mock_refresh = 'refresh-token-abc'

        mock_service.login_user.return_value = (mock_access, mock_refresh)

        client.app.dependency_overrides[get_service] = lambda: mock_service

        login_payload = LoginFactory.build().model_dump()

        response = await client.post('/auth/login', json=login_payload)

        data = response.json()

        assert response.status_code == 200
        assert data['access'] == mock_access
        assert data['refresh'] == mock_refresh

        mock_service.login_user.assert_called_once()

    async def test_login_with_invalid_credentials(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.login_user.side_effect = InvalidCredentialsError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        login_payload = LoginFactory.build().model_dump()
        response = await client.post('/auth/login', json=login_payload)

        assert response.status_code == 401
        assert 'Invalid Resource' in response.json()['error']

    async def test_login_with_missing_fields(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        incomplete_payload = {'email': 'test@example.com'}
        response = await client.post('/auth/login', json=incomplete_payload)

        assert response.status_code == 422


@mark.asyncio
class TestAuthRefresh:
    async def test_refresh_successfully(self, client):
        user_id = 123
        access_token, refresh_token = create_tokens(user_id)

        response = await client.get(
            '/auth/refresh', headers={'Authorization': f'Bearer {refresh_token}'}
        )
        data = response.json()

        assert response.status_code == 200
        assert 'access_token' in data
        assert 'Access token created' in data['detail']

    async def test_refresh_with_invalid_token(self, client):
        response = await client.get(
            '/auth/refresh', headers={'Authorization': 'Bearer invalid-token-123'}
        )

        assert response.status_code == 401

    async def test_refresh_without_token(self, client):
        response = await client.get('/auth/refresh')

        assert response.status_code == 401

    async def test_refresh_with_access_token_instead_of_refresh(self, client):
        access_token = create_access_token(123)

        response = await client.get(
            '/auth/refresh', headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 401


@mark.asyncio
class TestAuthMe:
    async def test_get_me_successfully(self, client, mocker):
        user_id = 1
        user = UserFactory.build(email='diego@example.com')
        user.id = user_id

        access_token = create_access_token(user_id)

        mock_service = mocker.AsyncMock()
        mock_service.get_user.return_value = user
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.get(
            '/auth/me', headers={'Authorization': f'Bearer {access_token}'}
        )
        data = response.json()

        assert response.status_code == 200
        assert data['id'] == user_id
        assert data['email'] == 'diego@example.com'
        assert data['name'] == user.name

        mock_service.get_user.assert_called_once_with(str(user_id))

    async def test_get_me_with_invalid_token(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.get(
            '/auth/me', headers={'Authorization': 'Bearer token-invalido-123'}
        )

        assert response.status_code == 401
        assert 'Invalid or expired token' in response.json()['detail']

    async def test_get_me_without_token(self, client):
        response = await client.get('/auth/me')

        assert response.status_code == 401
        assert 'Missing token' in response.json()['detail']

    async def test_get_me_user_not_found(self, client, mocker):
        user_id = 999
        access_token = create_access_token(user_id)

        mock_service = mocker.AsyncMock()
        mock_service.get_user.side_effect = NotFoundError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.get(
            '/auth/me', headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 404


@mark.asyncio
class TestAuthForgotPassword:
    async def test_forgot_password_successfully(self, client, mocker):
        mock_service = mocker.AsyncMock()

        mock_service.email_forgot_password_link.return_value = None

        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = EmailSchemaFactory.build().model_dump()
        response = await client.post('/auth/forgot-password', json=payload)

        assert response.status_code == 200
        assert (
            response.json()['detail']
            == 'A email with password reset link has been sent to you.'
        )

        mock_service.email_forgot_password_link.assert_called_once()

    async def test_forgot_password_invalid_email_format(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = {'email': 'invalid-email'}
        response = await client.post('/auth/forgot-password', json=payload)

        assert response.status_code == 422

    async def test_forgot_password_missing_payload(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.post('/auth/forgot-password', json={})

        assert response.status_code == 422

    async def test_forgot_password_with_unregistered_email(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.email_forgot_password_link.side_effect = NotFoundError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = EmailSchemaFactory.build().model_dump()
        response = await client.post('/auth/forgot-password', json=payload)

        assert response.status_code == 404


@mark.asyncio
class TestAuthResetPassword:
    async def test_reset_password_successfully(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.reset_password.return_value = None
        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = ResetPasswordRequestFactory.build().model_dump()

        response = await client.post('/auth/reset-password', json=payload)

        assert response.status_code == 200
        assert response.json()['detail'] == 'Password updated successfully'
        mock_service.reset_password.assert_called_once()

    async def test_reset_password_token_not_found(self, client, mocker):

        mock_service = mocker.AsyncMock()
        mock_service.reset_password.side_effect = NotFoundError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = ResetPasswordRequestFactory.build().model_dump()

        response = await client.post('/auth/reset-password', json=payload)

        assert response.status_code == 404
        assert response.json()['error'] == 'Resource not found'

    async def test_reset_password_token_expired(self, client, mocker):

        mock_service = mocker.AsyncMock()
        mock_service.reset_password.side_effect = InvalidCredentialsError(
            detail='Token has expired'
        )
        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = ResetPasswordRequestFactory.build().model_dump()

        response = await client.post('/auth/reset-password', json=payload)

        assert response.status_code == 401
        assert response.json()['error'] == 'Token has expired'

    async def test_reset_password_validation_error(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        payload = {'token': 'some-token'}  # Faltando a nova senha

        response = await client.post('/auth/reset-password', json=payload)

        assert response.status_code == 422  # Unprocessable Entity do Pydantic
