from pytest import mark, raises
from unittest.mock import MagicMock

from app.errors.exceptions import NotFoundError, InvalidCredentialsError
from app.services.auth_service import AuthService


@mark.asyncio
class TestAuthServiceLoginUser:
    async def test_login_user_successfully(self, mocker, create_login, create_users):
        data = create_login(email='test@example.com', password='pass1234')

        mock_user = create_users(count=1, email='test@example.com', password='pass1234')
        mock_user[0].check_password = mocker.AsyncMock(return_value=True)

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_email.return_value = mock_user[0]

        mock_email_service = mocker.AsyncMock()
        mock_token_repository = mocker.AsyncMock()

        result_access_token, result_refresh_token = await AuthService(
            email_service=mock_email_service,
            token_repo=mock_token_repository,
            user_repo=mock_user_repository,
        ).login_user(data)

        assert result_access_token is not None
        assert result_refresh_token is not None

        mock_user_repository.find_by_email.assert_called_once_with(data.email)

    async def test_login_user_fails_with_invalid_password(
        self, mocker, create_login, create_users
    ):
        data = create_login(email='test@example.com', password='pass1234')

        mock_user = create_users(count=1, email='test@example.com', password='')
        mock_user[0].check_password = mocker.AsyncMock(
            return_value=False
        )  # senha errada

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_email.return_value = mock_user[0]

        mock_email_service = mocker.AsyncMock()
        mock_token_repository = mocker.AsyncMock()

        with raises(InvalidCredentialsError) as exc_info:
            await AuthService(
                email_service=mock_email_service,
                token_repo=mock_token_repository,
                user_repo=mock_user_repository,
            ).login_user(data)

        assert exc_info.value.detail == 'Invalid password'

        mock_user_repository.find_by_email.assert_called_once_with(data.email)

    async def test_login_user_fails_when_user_not_found(self, mocker, create_login):
        data = create_login()

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_email.return_value = None

        mock_email_service = mocker.AsyncMock()
        mock_token_repository = mocker.AsyncMock()

        with raises(NotFoundError) as exc_info:
            await AuthService(
                email_service=mock_email_service,
                token_repo=mock_token_repository,
                user_repo=mock_user_repository,
            ).login_user(data)

        assert exc_info.value.detail == 'User not found'

        mock_user_repository.find_by_email.assert_called_once_with(data.email)


@mark.asyncio
class TestAuthServiceGetUser:
    async def test_get_user_successfully(self, mocker, create_users):
        id = 1
        mock_user = create_users(count=1)[0]
        mock_user.id = id

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = mock_user

        mock_email_service = mocker.AsyncMock()
        mock_token_repository = mocker.AsyncMock()

        result = await AuthService(
            email_service=mock_email_service,
            token_repo=mock_token_repository,
            user_repo=mock_user_repository,
        ).get_user(id)

        assert result is not None
        assert result.id == id
        assert result.email == mock_user.email

        mock_user_repository.find_by_id.assert_called_once_with(id)

    async def test_get_user_fails_when_user_not_found(self, mocker):
        id = 999
        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = None

        mock_email_service = mocker.AsyncMock()
        mock_token_repository = mocker.AsyncMock()

        with raises(NotFoundError) as exc_info:
            await AuthService(
                email_service=mock_email_service,
                token_repo=mock_token_repository,
                user_repo=mock_user_repository,
            ).get_user(id)

        assert exc_info.value.detail == 'User not found'

        mock_user_repository.find_by_id.assert_called_once_with(id)


@mark.asyncio
class TestAuthServiceForgotPassword:
    async def test_email_forgot_password_link_success(
        self, mocker, create_users, create_email_schema
    ):

        user = create_users(count=1)[0]

        email_data = create_email_schema(email=user.email)

        mock_user_repo = mocker.AsyncMock()
        mock_email_service = mocker.AsyncMock()
        mock_token_repo = mocker.AsyncMock()
        mock_background_tasks = MagicMock()

        mock_user_repo.find_by_email.return_value = user
        mock_token_repo.save.return_value = None

        await AuthService(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            email_service=mock_email_service,
        ).email_forgot_password_link(email_data, mock_background_tasks)

        mock_user_repo.find_by_email.assert_called_once_with(user.email)
        mock_token_repo.save.assert_called_once()
        mock_background_tasks.add_task.assert_called_once()

    async def test_email_forgot_password_user_not_found(
        self, mocker, create_email_schema
    ):

        mock_user_repo = mocker.AsyncMock()
        mock_email_service = mocker.AsyncMock()
        mock_token_repo = mocker.AsyncMock()
        mock_background_tasks = MagicMock()

        mock_user_repo.find_by_email.return_value = None
        mock_background_tasks = MagicMock()
        email_data = create_email_schema()

        with raises(NotFoundError):
            await AuthService(
                email_service=mock_email_service,
                token_repo=mock_token_repo,
                user_repo=mock_user_repo,
            ).email_forgot_password_link(email_data, mock_background_tasks)


@mark.asyncio
class TestAuthServiceResetPassword:
    async def test_reset_password_successfully(
        self, mocker, create_reset_password_request, create_users, create_tokens
    ):
        user = create_users(count=1)[0]
        data = create_reset_password_request(count=1)[0]

        mock_token_obj = create_tokens(count=1)[0]
        mock_token_obj.id = 1
        mock_token_obj.user_id = user.id
        mocker.patch.object(
            type(mock_token_obj),
            'is_expired',
            new_callable=mocker.PropertyMock,
            return_value=False,
        )

        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = mock_token_obj

        mock_user_repo = mocker.AsyncMock()
        mock_user_repo.find_by_id.return_value = user

        service = AuthService(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            email_service=mocker.AsyncMock(),
        )

        await service.reset_password(data)

        mock_token_repo.find_by_token_hash.assert_called_once_with(data.token)
        mock_user_repo.save.assert_called_once_with(user)
        mock_token_repo.delete.assert_called_with(mock_token_obj.id)

    async def test_reset_password_fails_if_token_not_found(
        self, mocker, create_tokens, create_reset_password_request
    ):
        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = None

        service = AuthService(
            user_repo=mocker.AsyncMock(),
            token_repo=mock_token_repo,
            email_service=mocker.AsyncMock(),
        )
        data = create_reset_password_request(count=1)[0]

        with raises(NotFoundError) as exc:
            await service.reset_password(data)

        assert 'Token not found' in exc.value.detail

    async def test_reset_password_fails_if_token_is_expired(
        self, mocker, create_tokens, create_reset_password_request
    ):
        data = create_reset_password_request(count=1)[0]

        mock_token_obj = create_tokens(count=1)[0]
        mock_token_obj.id = 99
        mocker.patch.object(
            type(mock_token_obj),
            'is_expired',
            new_callable=mocker.PropertyMock,
            return_value=True,
        )  # Simula token vencido

        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = mock_token_obj

        service = AuthService(
            user_repo=mocker.AsyncMock(),
            token_repo=mock_token_repo,
            email_service=mocker.AsyncMock(),
        )

        with raises(InvalidCredentialsError) as exc:
            await service.reset_password(data)

        assert 'expired' in exc.value.detail
        mock_token_repo.delete.assert_called_once_with(mock_token_obj.id)

    async def test_reset_password_fails_if_user_not_found(
        self, mocker, create_tokens, create_reset_password_request
    ):
        mock_token_obj = create_tokens(count=1)[0]
        mocker.patch.object(
            type(mock_token_obj),
            'is_expired',
            new_callable=mocker.PropertyMock,
            return_value=False,
        )
        mock_token_obj.user_id = 1

        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = mock_token_obj

        mock_user_repo = mocker.AsyncMock()
        mock_user_repo.find_by_id.return_value = None  

        service = AuthService(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
            email_service=mocker.AsyncMock(),
        )
        data = create_reset_password_request(count=1)[0]

        with raises(NotFoundError) as exc:
            await service.reset_password(data)

        assert 'User not found' in exc.value.detail
