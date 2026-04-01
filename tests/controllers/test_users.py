from pytest import mark
from app.controllers.users import get_service
from app.config.jwt import create_access_token, owner_required
from app.errors.exceptions import NotFoundError, ConflictError
from tests.factories import UserRequestFactory, UserFactory


@mark.asyncio
class TestUsersRegister:
    async def test_create_successfully(self, client, mocker):
        user = UserFactory.build(email='test@example.com')

        mock_service = mocker.AsyncMock()
        mock_service.create_user.return_value = user

        client.app.dependency_overrides[get_service] = lambda: mock_service

        user_payload = UserRequestFactory.build(email='test@example.com').model_dump()

        response = await client.post('/users/register', json=user_payload)

        assert response.status_code == 201
        assert response.json()['email'] == 'test@example.com'
        assert 'id' in response.json()

    async def test_create_with_duplicate_email(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.create_user.side_effect = ConflictError()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        user_payload = UserRequestFactory.build().model_dump()

        response = await client.post('/users/register', json=user_payload)

        assert response.status_code == 409
        assert 'Resource already exists' in response.json()['error']

    async def test_create_with_invalid_data(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        invalid_payload = {'name': 'Test', 'email': 'invalid-email'}
        response = await client.post('/users/register', json=invalid_payload)

        assert response.status_code == 422


@mark.asyncio
class TestUsersGetAll:
    async def test_get_all_successfully(self, client, mocker):
        users = UserFactory.build_batch(size=3)

        mock_service = mocker.AsyncMock()
        mock_total = 3
        mock_pages = 1
        mock_service.get_all_users.return_value = (users, mock_total, mock_pages)

        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('123')

        response = await client.get(
            '/users/', headers={'Authorization': f'Bearer {access_token}'}
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data['data']) == 3
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] == 3
        assert data['pagination']['pages'] == 1
        mock_service.get_all_users.assert_called_once_with(1, 10)

    async def test_get_all_with_pagination(self, client, mocker):
        user = UserFactory.build()

        mock_service = mocker.AsyncMock()
        mock_total = 25
        mock_pages = 3
        mock_service.get_all_users.return_value = ([user], mock_total, mock_pages)

        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('123')

        response = await client.get(
            '/users/?page=2&per_page=10',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        data = response.json()

        assert response.status_code == 200
        assert data['pagination']['page'] == 2
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] == 25
        assert data['pagination']['pages'] == 3
        mock_service.get_all_users.assert_called_once_with(2, 10)

    async def test_get_all_without_authentication(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.get('/users/')

        assert response.status_code == 401

    async def test_get_all_with_invalid_token(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.get(
            '/users/', headers={'Authorization': 'Bearer invalid-token'}
        )

        assert response.status_code == 401

    async def test_get_all_with_invalid_pagination(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('123')

        # Página inválida (0 ou negativa)
        response = await client.get(
            '/users/?page=0', headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 422

        # per_page maior que 100
        response = await client.get(
            '/users/?per_page=150', headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 422


@mark.asyncio
class TestUsersUpdate:
    async def test_update_successfully(self, client, mocker):
        mock_updated_user = UserFactory.build(
            id=1, name='Updated Name', email='updated@example.com'
        )

        mock_service = mocker.AsyncMock()
        mock_service.update_user.return_value = mock_updated_user

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: '1'

        access_token = create_access_token('1')

        update_payload = UserRequestFactory.build(
            name='Updated Name', email='updated@example.com'
        ).model_dump()

        response = await client.put(
            '/users/1',
            json=update_payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )
        data = response.json()

        assert response.status_code == 200
        assert data['name'] == 'Updated Name'
        assert data['email'] == 'updated@example.com'
        mock_service.update_user.assert_called_once()

    async def test_update_user_not_found(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.update_user.side_effect = NotFoundError()

        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('999')

        update_payload = UserRequestFactory.build().model_dump()

        response = await client.put(
            '/users/999',
            json=update_payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 404
        assert 'Resource not found' in response.json()['error']

    async def test_update_without_authorization(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        # Token de outro usuário (tentando atualizar id=1 com token de user=2)
        access_token = create_access_token('2')

        update_payload = UserRequestFactory.build(
            name='Updated', email='updated@example.com'
        ).model_dump()

        response = await client.put(
            '/users/1',
            json=update_payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 403

    async def test_update_without_authentication(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        update_payload = UserRequestFactory.build().model_dump()

        response = await client.put('/users/1', json=update_payload)

        assert response.status_code == 401

    async def test_update_with_invalid_data(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('1')

        invalid_payload = {'name': 'Test', 'email': 'invalid-email'}
        response = await client.put(
            '/users/1',
            json=invalid_payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 422


@mark.asyncio
class TestUsersDelete:
    async def test_delete_successfully(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.delete_user.return_value = None

        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('1')

        response = await client.delete(
            '/users/1', headers={'Authorization': f'Bearer {access_token}'}
        )
        data = response.json()

        assert response.status_code == 200
        assert 'User with ID 1 was deleted' in data['detail']
        mock_service.delete_user.assert_called_once_with(1)

    async def test_delete_user_not_found(self, client, mocker):
        mock_service = mocker.AsyncMock()
        mock_service.delete_user.side_effect = NotFoundError()

        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('999')

        response = await client.delete(
            '/users/999', headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 404
        assert 'Resource not found' in response.json()['error']

    async def test_delete_without_authorization(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        access_token = create_access_token('2')

        response = await client.delete(
            '/users/1', headers={'Authorization': f'Bearer {access_token}'}
        )

        assert response.status_code == 403

    async def test_delete_without_authentication(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.delete('/users/1')

        assert response.status_code == 401

    async def test_delete_with_invalid_token(self, client, mocker):
        mock_service = mocker.AsyncMock()
        client.app.dependency_overrides[get_service] = lambda: mock_service

        response = await client.delete(
            '/users/1', headers={'Authorization': 'Bearer invalid-token'}
        )

        assert response.status_code == 401
