from pytest import mark, raises
from app.errors.exceptions import ForbiddenError, NotFoundError
from app.services.contact_service import ContactService


@mark.asyncio
class TestContactServiceCreateContact:
    async def test_create_contact_successfully(
        self, mocker, create_contact_request, create_contacts
    ):
        user_id = 1
        data = create_contact_request()

        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()

        mock_user_repo.exists_by_id.return_value = True

        mock_contact = create_contacts(count=1, name=data.name)
        mock_contact[0].id = 10
        mock_contact_repo.save.return_value = mock_contact[0]

        service = ContactService(mock_contact_repo, mock_user_repo)
        result = await service.create_contact(user_id, data)

        assert result.id == 10
        assert result.name == data.name
        mock_user_repo.exists_by_id.assert_called_once_with(user_id)
        mock_contact_repo.save.assert_called_once()

    async def test_create_contact_fails_when_user_not_found(
        self, mocker, create_contact_request
    ):
        user_id = 99
        data = create_contact_request()

        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()
        mock_user_repo.exists_by_id.return_value = False

        service = ContactService(mock_contact_repo, mock_user_repo)
        with raises(NotFoundError) as exc_info:
            await service.create_contact(user_id, data)

        assert exc_info.value.detail == 'User not found'
        mock_contact_repo.save.assert_not_called()


@mark.asyncio
class TestContactServiceUpdateContact:
    async def test_update_contact_successfully(
        self, mocker, create_contact_request, create_contacts
    ):
        user_id = 1
        contact_id = 10
        data = create_contact_request(name='Updated Name')

        mock_contact = create_contacts(count=1, name='Old Name')
        mock_contact[0].id = contact_id
        mock_contact[0].user_id = user_id

        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()

        mock_contact_repo.find_by_id.return_value = mock_contact[0]
        mock_contact_repo.save.return_value = mock_contact[0]

        service = ContactService(mock_contact_repo, mock_user_repo)
        result = await service.update_contact(user_id, contact_id, data)

        assert result.name == 'Updated Name'
        mock_contact_repo.save.assert_called_once()

    async def test_update_contact_fails_forbidden_user(
        self, mocker, create_contact_request, create_contacts
    ):
        user_id = 1  # Usuário logado
        contact_id = 10
        data = create_contact_request()

        # Contato pertence a OUTRO usuário (user_id 2)
        mock_contact = create_contacts(count=1)
        mock_contact[0].user_id = 2

        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()
        mock_contact_repo.find_by_id.return_value = mock_contact[0]

        service = ContactService(mock_contact_repo, mock_user_repo)
        with raises(ForbiddenError) as exc_info:
            await service.update_contact(user_id, contact_id, data)

        assert 'does not have access' in exc_info.value.detail
        mock_contact_repo.save.assert_not_called()


@mark.asyncio
class TestContactServiceDeleteContact:
    async def test_delete_contact_successfully(self, mocker, create_contacts):
        user_id = 1
        contact_id = 10

        mock_contact = create_contacts(count=1)
        mock_contact[0].user_id = user_id

        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()
        mock_contact_repo.find_by_id.return_value = mock_contact[0]

        service = ContactService(mock_contact_repo, mock_user_repo)
        await service.delete_contact(user_id, contact_id)

        mock_contact_repo.delete.assert_called_once_with(contact_id)

    async def test_delete_fails_when_contact_not_found(self, mocker):
        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()
        mock_contact_repo.find_by_id.return_value = None

        service = ContactService(mock_contact_repo, mock_user_repo)
        with raises(NotFoundError) as exc_info:
            await service.delete_contact(1, 10)

        assert exc_info.value.detail == 'Contact not found'


@mark.asyncio
class TestContactServiceGetAll:
    async def test_get_all_contacts_successfully(self, mocker, create_contacts):
        user_id = 1
        page, per_page = 1, 10
        mock_contacts = create_contacts(count=3)
        total_count = 3

        mock_contact_repo = mocker.AsyncMock()
        mock_user_repo = mocker.AsyncMock()

        mock_user_repo.exists_by_id.return_value = True
        mock_contact_repo.get_all.return_value = (mock_contacts, total_count)

        service = ContactService(mock_contact_repo, mock_user_repo)

        items, total, pages = await service.get_all_contacts(user_id, page, per_page)

        assert len(items) == 3
        assert total == 3
        assert pages == 1  # (3 + 10 - 1) // 10 = 1

        mock_contact_repo.get_all.assert_called_once_with(user_id, page, per_page)
