from pytest import mark, raises
from tests.factories import PasswordResetTokenFactory, UserFactory
from app.models.password_reset_token import PasswordResetToken


@mark.asyncio
class TestTokenRepositorySave:
    async def test_save_token_persists_data_correctly(
        self,
        token_repository,
    ):
        token = PasswordResetTokenFactory.build()
        saved_token = await token_repository.save(token)

        assert saved_token.id is not None
        assert saved_token.token_hash == token.token_hash
        assert saved_token.expires_at == token.expires_at

    async def test_save_fails_with_email_already_exists(self, token_repository):
        tokens = PasswordResetTokenFactory.build_batch(
            size=2, token_hash='sample_tokens'
        )

        await token_repository.save(tokens[0])

        with raises(ValueError) as exc_info:
            await token_repository.save(tokens[1])

        assert 'Error saving password reset token to database' in str(exc_info.value)


@mark.asyncio
class TestTokenRepositoryDeleteAllByUserId:
    async def test_delete_all_token_successfully(
        self, token_repository, setup_factory_session
    ):
        user = await UserFactory.create()
        tokens = await PasswordResetTokenFactory.create_batch(size=2, user=user)

        result = await token_repository.delete_all_by_user_id(tokens[0].user_id)

        assert result == 2
        found = await token_repository.find_by_token_hash(tokens[0].token_hash)
        assert found is None

    async def test_delete_token_with_non_existent_user_returns_0(
        self, token_repository
    ):
        result = await token_repository.delete_all_by_user_id(999)
        assert result == 0


@mark.asyncio
class TestTokenRepositoryFindByTokenHash:
    async def test_find_by_token_hash_successfully(
        self, token_repository, setup_factory_session
    ):
        raw_token: str = 'meu-token-secreto-123'
        target_hash: str = await PasswordResetToken.hash_token(raw_token)

        token = await PasswordResetTokenFactory.create(token_hash=target_hash)

        found_token = await token_repository.find_by_token_hash(target_hash)

        assert found_token is not None
        assert found_token.token_hash == target_hash
        assert found_token.user_id == token.user_id

    async def test_find_by_token_hash_returns_none_if_not_found(self, token_repository):
        result = await token_repository.find_by_token_hash('token-inexistente')
        assert result is None


@mark.asyncio
class TestTokenRepositoryReplaceAllByUserId:
    async def test_replace_all_by_user_id_successfully(
        self, token_repository, setup_factory_session
    ):
        user = await UserFactory.create()
        old_tokens = await PasswordResetTokenFactory.create_batch(size=2, user=user)

        raw_token = 'novo-token-secreto'
        target_hash = await PasswordResetToken.hash_token(raw_token)

        new_token = PasswordResetTokenFactory.build(
            user_id=user.id, token_hash=target_hash
        )

        result = await token_repository.replace_all_by_user_id(user.id, new_token)

        assert result is not None
        assert await token_repository.find_by_token_hash(target_hash) is not None
        assert (
            await token_repository.find_by_token_hash(old_tokens[0].token_hash) is None
        )
        assert (
            await token_repository.find_by_token_hash(old_tokens[1].token_hash) is None
        )
