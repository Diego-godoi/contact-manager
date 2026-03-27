from pytest import mark
from app.controllers.auth import get_service
from app.config.jwt import create_access_token, create_tokens
from app.errors.exceptions import ConflictError, InvalidCredentialsError


@mark.asyncio
class TestAuthCreate:
    async def test_create_successfully(
        self, client, mocker, create_users, create_user_request
    ):
        users = create_users(count=1, email='test@example.com')
        users[0].id = 1

        mock_service = mocker.AsyncMock()
        mock_service.create_user.return_value = users[0]

        client.app.dependency_overrides[get_service] = lambda: mock_service

        user_payload = create_user_request(email='test@example.com').model_dump()

        response = await client.post('/auth/register', json=user_payload)

        assert response.status_code == 201
        assert response.json()['email'] == 'test@example.com'
        assert 'id' in response.json()

    async def test_create_with_duplicate_email(
        self, client, mocker, create_user_request
    ):
        mock_service = mocker.AsyncMock()
        mock_service.create_user.side_effect = ConflictError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        user_payload = create_user_request().model_dump()

        response = await client.post('/auth/register', json=user_payload)

        assert response.status_code == 409
        assert 'Resource already exists' in response.json()['error']

    async def test_create_with_invalid_data(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        invalid_payload = {'name': 'Test', 'email': 'invalid-email'}
        response = await client.post('/auth/register', json=invalid_payload)

        assert response.status_code == 422


@mark.asyncio
class TestAuthLogin:
    async def test_login_successfully(self, client, mocker, create_login):
        mock_service = mocker.AsyncMock()
        mock_access = 'access-token-123'
        mock_refresh = 'refresh-token-abc'

        mock_service.login_user.return_value = (mock_access, mock_refresh)

        client.app.dependency_overrides[get_service] = lambda: mock_service

        login_payload = create_login().model_dump()

        response = await client.post('/auth/login', json=login_payload)

        data = response.json()

        assert response.status_code == 200
        assert data['access'] == mock_access
        assert data['refresh'] == mock_refresh

        mock_service.login_user.assert_called_once()

    async def test_login_with_invalid_credentials(self, client, mocker, create_login):
        mock_service = mocker.AsyncMock()
        mock_service.login_user.side_effect = InvalidCredentialsError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        login_payload = create_login().model_dump()
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
        # Tentar usar access token em vez de refresh token
        access_token = create_access_token(123)

        response = await client.get(
            '/auth/refresh', headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 401


@mark.asyncio
class TestAuthMe:
    async def test_get_me_successfully(self, client, mocker, create_users):
        user_id = 1
        user = create_users(count=1, email='diego@example.com')[0]
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
        # Caso onde o token é válido mas o usuário foi deletado do banco
        from app.errors.exceptions import (
            NotFoundError,
        )

        user_id = 999
        access_token = create_access_token(user_id)

        mock_service = mocker.AsyncMock()
        mock_service.get_user.side_effect = NotFoundError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.get(
            '/auth/me', headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 404
