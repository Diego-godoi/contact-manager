from pytest import mark, raises


@mark.asyncio
class TestUserRepositorySave:
    async def test_save_user_persists_data_correctly(
        self, user_repository, create_users
    ):
        user = create_users(count=1)
        saved_user = await user_repository.save(user[0])

        assert saved_user.id is not None
        assert saved_user.name == user[0].name
        assert saved_user.email == user[0].email
        assert saved_user.password == user[0].password

    async def test_save_fails_with_email_already_exists(
        self, user_repository, create_users
    ):
        users = create_users(count=2, email='duplicate@example.com')
        await user_repository.save(users[0])

        with raises(ValueError) as exc_info:
            await user_repository.save(users[1])

        assert 'Error saving user to database' in str(exc_info.value)


@mark.asyncio
class TestUserRepositoryDelete:
    async def test_deletes_user_correctly(self, user_repository, create_users):
        user = create_users(count=1)
        saved_user = await user_repository.save(user[0])

        result = await user_repository.delete(saved_user.id)

        assert result is True

        deleted_user = await user_repository.find_by_id(saved_user.id)
        assert deleted_user is None

    async def test_delete_non_existent_user_returns_false(self, user_repository):
        assert await user_repository.delete(9999) is False


@mark.asyncio
class TestUserRepositoryGetAll:
    async def test_get_all_returns_paginated_users(
        self, user_repository, create_users, save_users
    ):
        await save_users(create_users(count=5))

        # Busca primeira página com 3 itens
        result_users, total = await user_repository.get_all(page=1, per_page=3)

        assert len(result_users) == 3
        assert total == 5

    async def test_get_all_returns_second_page_correctly(
        self, user_repository, create_users, save_users
    ):
        await save_users(create_users(count=5))

        # Busca segunda página com 3 itens
        result_users, total = await user_repository.get_all(page=2, per_page=3)

        assert len(result_users) == 2  # Restam apenas 2 usuários na segunda página
        assert total == 5

    async def test_get_all_returns_empty_list_when_no_users(self, user_repository):
        users, total = await user_repository.get_all(page=1, per_page=10)

        assert len(users) == 0
        assert total == 0


@mark.asyncio
class TestUserRepositoryExistsByEmail:
    async def test_exists_by_email_returns_true_when_user_exists(
        self, user_repository, create_users
    ):
        user = create_users(count=1, email='exists@example.com')
        await user_repository.save(user[0])

        exists = await user_repository.exists_by_email('exists@example.com')

        assert exists is True

    async def test_exists_by_email_is_case_insensitive(
        self, user_repository, create_users
    ):
        await user_repository.save(create_users(count=1, email='test@example.com')[0])

        exists = await user_repository.exists_by_email('TEST@EXAMPLE.COM')

        assert exists is True

    async def test_exists_by_email_returns_false_when_user_not_exists(
        self, user_repository
    ):
        exists = await user_repository.exists_by_email('nonexistent@example.com')

        assert exists is False


@mark.asyncio
class TestUserRepositoryExistsById:
    async def test_exists_by_id_returns_true_when_user_exists(
        self, user_repository, create_users
    ):
        saved_user = await user_repository.save(create_users(count=1)[0])

        exists = await user_repository.exists_by_id(saved_user.id)

        assert exists is True

    async def test_exists_by_id_returns_false_when_user_not_exists(
        self, user_repository
    ):
        assert await user_repository.exists_by_id(9999) is False


@mark.asyncio
class TestUserRepositoryFindById:
    async def test_find_by_id_returns_user_when_exists(
        self, user_repository, create_users
    ):
        user = create_users(count=1)
        saved_user = await user_repository.save(user[0])

        found_user = await user_repository.find_by_id(saved_user.id)

        assert found_user is not None
        assert found_user.id == saved_user.id
        assert found_user.name == user[0].name
        assert found_user.email == user[0].email.lower()

    async def test_find_by_id_returns_none_when_user_not_found(self, user_repository):
        assert await user_repository.find_by_id(9999) is None


@mark.asyncio
class TestUserRepositoryFindByEmail:
    async def test_find_by_email_returns_user_when_exists(
        self, user_repository, create_users
    ):
        user = create_users(count=1, email='find@example.com')
        saved_user = await user_repository.save(user[0])

        found_user = await user_repository.find_by_email('find@example.com')

        assert found_user is not None
        assert found_user.id == saved_user.id
        assert found_user.name == user[0].name
        assert found_user.email == user[0].email.lower()

    async def test_find_by_email_returns_none_when_user_not_found(
        self, user_repository
    ):
        assert await user_repository.find_by_email('nonexistent@example.com') is None

    async def test_find_by_email_returns_correct_user_with_exact_email(
        self, user_repository, create_users, save_users
    ):
        users = create_users(count=3)

        users[0].email = 'user1@example.com'
        users[1].email = 'user2@example.com'
        users[2].email = 'user3@example.com'

        saved_users = await save_users(users)

        found_user = await user_repository.find_by_email('user2@example.com')

        assert found_user is not None
        assert found_user.id == saved_users[1].id
        assert found_user.email == 'user2@example.com'
