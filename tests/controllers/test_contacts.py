from pytest import mark
from app.controllers.contacts import get_service
from app.config.jwt import create_access_token, owner_required
from app.errors.exceptions import ForbiddenError, NotFoundError


@mark.asyncio
class TestContactsCreate:
    async def test_create_contact_successfully(
        self, client, mocker, create_contacts, create_contact_request
    ):
        user_id = 1
        contacts = create_contacts(count=1, name='João Silva')
        contacts[0].id = 10
        contacts[0].user_id = user_id

        mock_service = mocker.AsyncMock()
        mock_service.create_contact.return_value = contacts[0]

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        access_token = create_access_token(str(user_id))
        payload = create_contact_request(name='João Silva').model_dump()

        response = await client.post(
            f'/users/{user_id}/contacts/',
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 201
        assert response.json()['name'] == 'João Silva'
        assert response.json()['id'] == 10

    async def test_create_contact_user_not_found(
        self, client, mocker, create_contact_request
    ):
        user_id = 999
        mock_service = mocker.AsyncMock()
        mock_service.create_contact.side_effect = NotFoundError()

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        access_token = create_access_token(str(user_id))
        payload = create_contact_request().model_dump()

        response = await client.post(
            f'/users/{user_id}/contacts/',
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 404


@mark.asyncio
class TestContactsGetAll:
    async def test_get_all_contacts_successfully(self, client, mocker, create_contacts):
        user_id = 1
        page, per_page = 1, 10
        contacts = create_contacts(count=2)

        for idx, contact in enumerate(contacts, start=1):
            contact.id = idx
            contact.user_id = user_id

        mock_service = mocker.AsyncMock()
        mock_service.get_all_contacts.return_value = (contacts, 2, 1)

        client.app.dependency_overrides[get_service] = lambda: mock_service

        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        response = await client.get(
            f'/users/{user_id}/contacts/?page={page}&per_page={per_page}',
        )

        assert response.status_code == 200

        json_response = response.json()

        assert len(json_response['data']) == 2
        assert json_response['pagination']['total'] == 2
        assert json_response['pagination']['page'] == page

        mock_service.get_all_contacts.assert_called_once_with(user_id, page, per_page)


@mark.asyncio
class TestContactsUpdate:
    async def test_update_contact_successfully(
        self, client, mocker, create_contacts, create_contact_request
    ):
        user_id = 1
        contact_id = 10
        updated_contacts = create_contacts(count=1, name='Nome Atualizado')
        updated_contacts[0].id = contact_id

        mock_service = mocker.AsyncMock()
        mock_service.update_contact.return_value = updated_contacts[0]

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        access_token = create_access_token(str(user_id))
        payload = create_contact_request(name='Nome Atualizado').model_dump()

        response = await client.put(
            f'/users/{user_id}/contacts/{contact_id}',
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 200
        assert response.json()['name'] == 'Nome Atualizado'

    async def test_update_contact_forbidden(
        self, client, mocker, create_contact_request
    ):
        user_id = 1
        contact_id = 10

        mock_service = mocker.AsyncMock()
        # Simula erro de permissão (usuário tentando editar contato de outro)
        mock_service.update_contact.side_effect = ForbiddenError()

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        access_token = create_access_token(str(user_id))
        payload = create_contact_request().model_dump()

        response = await client.put(
            f'/users/{user_id}/contacts/{contact_id}',
            json=payload,
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 403


@mark.asyncio
class TestContactsDelete:
    async def test_delete_contact_successfully(self, client, mocker):
        user_id = 1
        contact_id = 10

        mock_service = mocker.AsyncMock()
        mock_service.delete_contact.return_value = None

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        access_token = create_access_token(str(user_id))

        response = await client.delete(
            f'/users/{user_id}/contacts/{contact_id}',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 200
        assert f'Contact with ID {contact_id} was deleted' in response.json()['detail']
        mock_service.delete_contact.assert_called_once_with(user_id, contact_id)

    async def test_delete_contact_not_found(self, client, mocker):
        user_id = 1
        contact_id = 99

        mock_service = mocker.AsyncMock()
        mock_service.delete_contact.side_effect = NotFoundError()

        client.app.dependency_overrides[get_service] = lambda: mock_service
        client.app.dependency_overrides[owner_required] = lambda: str(user_id)

        access_token = create_access_token(str(user_id))

        response = await client.delete(
            f'/users/{user_id}/contacts/{contact_id}',
            headers={'Authorization': f'Bearer {access_token}'},
        )

        assert response.status_code == 404
