from pytest import mark, raises

from app.errors.exceptions import (
    ConflictError,
    NotFoundError,
)
from app.models.user import User
from app.services.user_service import UserService
from tests.factories import UserFactory, UserRequestFactory


@mark.asyncio
class TestUserServiceCreateUser:
    async def test_create_user_successfully(self, mocker):
        data = UserRequestFactory.build()

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.exists_by_email.return_value = False
        mock_user = User(id=1, name=data.name, email=data.email, password=data.password)
        mock_user_repository.save.return_value = mock_user

        result = await UserService(mock_user_repository).create_user(data)

        assert result is not None
        assert result.id == 1
        assert result.email == data.email

        mock_user_repository.exists_by_email.assert_called_once_with(data.email)
        mock_user_repository.save.assert_called_once()

    async def test_create_fails_with_email_already_exists(self, mocker):
        data = UserRequestFactory.build()

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.exists_by_email.return_value = True

        with raises(ConflictError) as exc_info:
            await UserService(mock_user_repository).create_user(data)

        assert exc_info.value.detail == 'Email already exists'

        mock_user_repository.exists_by_email.assert_called_once()
        mock_user_repository.save.assert_not_called()


@mark.asyncio
class TestUserServiceUpdateUser:
    async def test_update_user_successfully(
        self,
        mocker,
    ):
        id = 1
        data = UserRequestFactory.build(
            name='New Name', email='new@example.com', password='newpass1'
        )

        mock_user = UserFactory.build(
            id=1, name='Old Name', email='old@example.com', password='oldpass1'
        )

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.save.return_value = mock_user

        result = await UserService(mock_user_repository).update_user(id, data)

        assert result.id == id
        assert result.email == data.email
        assert result.name == data.name
        assert await result.check_password(data.password)

        mock_user_repository.save.assert_called_once()
        mock_user_repository.exists_by_email.assert_called_once_with(data.email)
        mock_user_repository.find_by_id.assert_called_once_with(id)

    async def test_update_user_fails_with_new_email_already_exists(
        self,
        mocker,
    ):
        id = 1
        data = UserRequestFactory.build(email='new@example.com')
        mock_user = UserFactory.build(email='old@example.com')

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.exists_by_email.return_value = True

        with raises(ConflictError) as exc_info:
            await UserService(mock_user_repository).update_user(id, data)

        assert exc_info.value.detail == 'Email already exists'

        mock_user_repository.save.assert_not_called()
        mock_user_repository.exists_by_email.assert_called_once_with(data.email)
        mock_user_repository.find_by_id.assert_called_once_with(id)

    async def test_update_user_fails_when_user_not_found(self, mocker):
        id = 1
        data = UserRequestFactory.build()

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = None

        with raises(NotFoundError) as exc_info:
            await UserService(mock_user_repository).update_user(id, data)

        assert exc_info.value.detail == 'User not found'

        mock_user_repository.save.assert_not_called()
        mock_user_repository.exists_by_email.assert_not_called()
        mock_user_repository.find_by_id.assert_called_once_with(id)

    async def test_update_does_not_check_email_when_email_unchanged(
        self,
        mocker,
    ):
        id = 1
        data = UserRequestFactory.build(name='New Name', email='same@example.com')

        mock_user = UserFactory.build(
            id=1, name='Old Name', email='same@example.com', password=''
        )

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = mock_user
        mock_user_repository.save.return_value = mock_user

        result = await UserService(mock_user_repository).update_user(id, data)
        assert result is not None

        mock_user_repository.exists_by_email.assert_not_called()


@mark.asyncio
class TestUserServiceDeleteUser:
    async def test_delete_user_successfully(self, mocker):
        id = 1

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.exists_by_id.return_value = True
        mock_user_repository.delete.return_value = True

        result = await UserService(mock_user_repository).delete_user(id)

        assert result

        mock_user_repository.delete.assert_called_once_with(id)
        mock_user_repository.exists_by_id.assert_called_once_with(id)

    async def test_delete_user_fails_when_user_not_found(self, mocker):
        id = 99

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.exists_by_id.return_value = False

        with raises(NotFoundError) as exc_info:
            await UserService(mock_user_repository).delete_user(id)

        assert exc_info.value.detail == 'User not found'

        mock_user_repository.exists_by_id.assert_called_once_with(id)
        mock_user_repository.delete.assert_not_called()


@mark.asyncio
class TestUserServiceGetAllUsers:
    async def test_get_all_users_successfully(self, mocker):
        page = 1
        per_page = 10

        total = 7
        mock_items = UserFactory.build_batch(size=7)

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.get_all.return_value = mock_items, total

        result_items, result_total, result_pages = await UserService(
            mock_user_repository
        ).get_all_users(page, per_page)

        assert result_items is not None
        assert result_pages == 1
        assert result_total == 7

        mock_user_repository.get_all.assert_called_once()

    async def test_get_all_users_calculates_pages_correctly(self, mocker):
        page = 1
        per_page = 3
        total = 10

        mock_items = UserFactory.build_batch(size=3)

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.get_all.return_value = mock_items, total

        result_items, result_total, result_pages = await UserService(
            mock_user_repository
        ).get_all_users(page, per_page)

        expected_total = 10
        expected_pages = 4
        assert result_pages == expected_pages  # 10 itens / 3 por página = 4 páginas
        assert result_total == expected_total

    async def test_get_all_users_returns_empty_when_no_users(self, mocker):
        page = 1
        per_page = 10

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.get_all.return_value = [], 0

        result_items, result_total, result_pages = await UserService(
            mock_user_repository
        ).get_all_users(page, per_page)

        assert len(result_items) == 0
        assert result_total == 0
        assert result_pages == 0

        mock_user_repository.get_all.assert_called_once_with(page, per_page)
