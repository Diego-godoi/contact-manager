from pytest import mark, raises
import hashlib
from tests.factories import PasswordResetTokenFactory


@mark.asyncio
class TestTokenRepositorySave:
    async def test_save_token_persists_data_correctly(
        self,
        token_repository,
    ):
        token = PasswordResetTokenFactory.build(user_id=1)
        saved_token = await token_repository.save(token)

        assert saved_token.id is not None
        assert saved_token.token_hash == token.token_hash
        assert saved_token.expires_at == token.expires_at

    async def test_save_fails_with_email_already_exists(
        self,
        token_repository,
    ):
        tokens = PasswordResetTokenFactory.build_batch(
            size=2, token_hash='sample_tokens'
        )
        for token in tokens:
            token.user_id = id

        await token_repository.save(tokens[0])

        with raises(ValueError) as exc_info:
            await token_repository.save(tokens[1])

        assert 'Error saving password reset token to database' in str(exc_info.value)


@mark.asyncio
class TestTokenRepositoryDelete:
    async def test_delete_token_successfully(
        self,
        token_repository,
    ):
        token = await PasswordResetTokenFactory.create()

        result = await token_repository.delete(token.id)

        assert result is True
        found = await token_repository.find_by_token_hash(token.token_hash)
        assert found is None

    async def test_delete_non_existent_token_returns_false(self, token_repository):
        result = await token_repository.delete(999)
        assert result is False


@mark.asyncio
class TestTokenRepositoryFindByTokenHash:
    async def test_find_by_token_hash_successfully(
        self,
        token_repository,
    ):
        raw_token = 'meu-token-secreto-123'
        target_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        token = await PasswordResetTokenFactory.create(token_hash=target_hash)

        found_token = await token_repository.find_by_token_hash(raw_token)

        assert found_token is not None
        assert found_token.token_hash == target_hash
        assert found_token.user_id == token.user_id

    async def test_find_by_token_hash_returns_none_if_not_found(self, token_repository):
        result = await token_repository.find_by_token_hash('token-inexistente')
        assert result is None
