from pytest import mark, raises
from app.models.password_reset_token import PasswordResetToken
from app.errors.exceptions import NotFoundError, InvalidCredentialsError
from app.services.auth_service import AuthService
from tests.factories import (
    UserFactory,
    LoginFactory,
    EmailSchemaFactory,
    PasswordResetTokenFactory,
    ResetPasswordRequestFactory,
)


@mark.asyncio
class TestAuthServiceLoginUser:
    async def test_login_user_successfully(
        self,
        mocker,
    ):
        data = LoginFactory.build(email='test@example.com', password='pass1234')

        mock_user = UserFactory.build(email='test@example.com', password='pass1234')
        mock_user.check_password = mocker.AsyncMock(return_value=True)

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_email.return_value = mock_user

        mock_token_repository = mocker.AsyncMock()

        result_access_token, result_refresh_token = await AuthService(
            token_repo=mock_token_repository,
            user_repo=mock_user_repository,
        ).login_user(data)

        assert result_access_token is not None
        assert result_refresh_token is not None

        mock_user_repository.find_by_email.assert_called_once_with(data.email)

    async def test_login_user_fails_with_invalid_password(
        self,
        mocker,
    ):
        data = LoginFactory.build(email='test@example.com', password='pass1234')

        mock_user = UserFactory.build(email='test@example.com', password='')
        mock_user.check_password = mocker.AsyncMock(return_value=False)  # senha errada

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_email.return_value = mock_user

        mock_token_repository = mocker.AsyncMock()

        with raises(InvalidCredentialsError) as exc_info:
            await AuthService(
                token_repo=mock_token_repository,
                user_repo=mock_user_repository,
            ).login_user(data)

        assert exc_info.value.detail == 'Invalid email or password'

        mock_user_repository.find_by_email.assert_called_once_with(data.email)

    async def test_login_user_fails_when_user_not_found(self, mocker):
        data = LoginFactory.build()

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_email.return_value = None

        mock_token_repository = mocker.AsyncMock()

        with raises(InvalidCredentialsError) as exc_info:
            await AuthService(
                token_repo=mock_token_repository,
                user_repo=mock_user_repository,
            ).login_user(data)

        assert exc_info.value.detail == 'Invalid email or password'

        mock_user_repository.find_by_email.assert_called_once_with(data.email)


@mark.asyncio
class TestAuthServiceGetUser:
    async def test_get_user_successfully(self, mocker):
        id = 1
        mock_user = UserFactory.build(id=id)

        mock_user_repository = mocker.AsyncMock()
        mock_user_repository.find_by_id.return_value = mock_user

        mock_token_repository = mocker.AsyncMock()

        result = await AuthService(
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

        mock_token_repository = mocker.AsyncMock()

        with raises(NotFoundError) as exc_info:
            await AuthService(
                token_repo=mock_token_repository,
                user_repo=mock_user_repository,
            ).get_user(id)

        assert exc_info.value.detail == 'User not found'

        mock_user_repository.find_by_id.assert_called_once_with(id)


@mark.asyncio
class TestAuthServicePreparePasswordReset:
    async def test_prepare_password_reset_success(
        self,
        mocker,
    ):
        user = UserFactory.build()

        data = EmailSchemaFactory.build(email=user.email)

        mock_user_repo = mocker.AsyncMock()
        mock_token_repo = mocker.AsyncMock()

        mock_user_repo.find_by_email.return_value = user
        mock_token_repo.replace_all_by_user_id.return_value = None

        result = await AuthService(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
        ).prepare_password_reset(data)

        result_user, result_token = result

        assert result is not None

        mock_user_repo.find_by_email.assert_called_once_with(user.email)
        mock_token_repo.replace_all_by_user_id.assert_called_once()

    async def test_prepare_password_reset_with_user_not_found(
        self,
        mocker,
    ):

        mock_user_repo = mocker.AsyncMock()
        mock_token_repo = mocker.AsyncMock()

        mock_user_repo.find_by_email.return_value = None
        data = EmailSchemaFactory.build()

        result = await AuthService(
            token_repo=mock_token_repo,
            user_repo=mock_user_repo,
        ).prepare_password_reset(data)

        assert result is None


@mark.asyncio
class TestAuthServiceResetPassword:
    async def test_reset_password_successfully(
        self,
        mocker,
    ):
        user = UserFactory.build()
        data = ResetPasswordRequestFactory.build()

        expected_hash = await PasswordResetToken.hash_token(data.token)

        mock_token_obj = PasswordResetTokenFactory.build(id=1, user_id=user.id)

        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = mock_token_obj

        mock_user_repo = mocker.AsyncMock()
        mock_user_repo.find_by_id.return_value = user

        service = AuthService(
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
        )

        await service.reset_password(data)

        mock_token_repo.find_by_token_hash.assert_called_once_with(expected_hash)
        mock_user_repo.save.assert_called_once_with(user)
        mock_token_repo.delete_all_by_user_id.assert_called_with(user.id)

    async def test_reset_password_fails_if_token_not_found(
        self,
        mocker,
    ):
        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = None

        service = AuthService(
            user_repo=mocker.AsyncMock(),
            token_repo=mock_token_repo,
        )
        data = ResetPasswordRequestFactory.build()

        with raises(NotFoundError) as exc:
            await service.reset_password(data)

        assert 'Token not found' in exc.value.detail

    async def test_reset_password_fails_if_token_is_expired(
        self,
        mocker,
    ):
        data = ResetPasswordRequestFactory.build()

        mock_token_obj = PasswordResetTokenFactory.build(expired=True)

        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = mock_token_obj

        service = AuthService(
            user_repo=mocker.AsyncMock(),
            token_repo=mock_token_repo,
        )

        with raises(InvalidCredentialsError) as exc:
            await service.reset_password(data)

        assert 'expired' in exc.value.detail
        mock_token_repo.delete_all_by_user_id.assert_called_once_with(
            mock_token_obj.user_id
        )

    async def test_reset_password_fails_if_user_not_found(
        self,
        mocker,
    ):
        mock_token_obj = PasswordResetTokenFactory.build()

        mock_token_repo = mocker.AsyncMock()
        mock_token_repo.find_by_token_hash.return_value = mock_token_obj

        mock_user_repo = mocker.AsyncMock()
        mock_user_repo.find_by_id.return_value = None

        data = ResetPasswordRequestFactory.build()

        with raises(NotFoundError) as exc:
            await AuthService(
                user_repo=mock_user_repo,
                token_repo=mock_token_repo,
            ).reset_password(data)

        assert 'User not found' in exc.value.detail
