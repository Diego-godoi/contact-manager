from pytest import mark, raises


@mark.asyncio
class TestContactRepositorySave:
    async def test_save_contact_persists_data_correctly(
        self,
        contact_repository,
        create_users,
        user_repository,
        create_contacts,
        save_users,
    ):
        users = create_users(count=1)
        await save_users(users)

        contact_data = create_contacts(count=1, name='João Silva', phone='11999999999')
        saved_contact = await contact_repository.save(users[0].id, contact_data[0])

        assert saved_contact.id is not None
        assert saved_contact.user_id == users[0].id
        assert saved_contact.name == 'João Silva'
        assert saved_contact.phone == '11999999999'

    @mark.xfail  # sqlite permite o salvamento mesmo com violacao de FK
    async def test_save_contact_fails_with_invalid_user(
        self, contact_repository, create_contacts
    ):
        # Tenta salvar um contato para um user_id que não existe no banco (violação de FK)
        contacts = create_contacts(count=1)

        with raises(ValueError) as exc_info:
            await contact_repository.save(9999, contacts[0])

        assert 'Error saving contact to database' in str(exc_info.value)


@mark.asyncio
class TestContactRepositoryDelete:
    async def test_deletes_contact_correctly(
        self,
        contact_repository,
        create_users,
        user_repository,
        create_contacts,
        save_users,
    ):
        users = create_users(count=1)
        await save_users(users)

        contact = await contact_repository.save(
            users[0].id, create_contacts(count=1)[0]
        )

        result = await contact_repository.delete(contact.id)

        assert result is True
        found = await contact_repository.find_by_id(contact.id)
        assert found is None

    async def test_delete_non_existent_contact_returns_false(self, contact_repository):
        assert await contact_repository.delete(9999) is False


@mark.asyncio
class TestContactRepositoryGetAll:
    async def test_get_all_returns_only_contacts_from_specific_user(
        self,
        contact_repository,
        user_repository,
        create_users,
        create_contacts,
        save_users,
    ):
        # 1. Criamos dois usuários
        users = create_users(count=2)
        await save_users(users)

        # 2. Criamos e salvamos os contatos vinculando aos IDs
        contacts = create_contacts(count=3)
        await contact_repository.save(users[0].id, contacts[0])
        await contact_repository.save(users[1].id, contacts[1])
        await contact_repository.save(users[0].id, contacts[2])

        contacts_user1, total = await contact_repository.get_all(
            user_id=users[0].id, page=1, per_page=10
        )

        assert len(contacts_user1) == 2
        assert total == 2
        assert all(c.user_id == users[0].id for c in contacts_user1)

    async def test_get_all_returns_empty_list_when_no_contacts(
        self, contact_repository
    ):
        contacts, total = await contact_repository.get_all(
            user_id=999, page=1, per_page=10
        )

        assert contacts == []
        assert total == 0


@mark.asyncio
class TestContactRepositoryExistsAndFind:
    async def test_exists_by_id_returns_correct_bool(
        self,
        contact_repository,
        user_repository,
        create_users,
        create_contacts,
        save_users,
    ):
        users = create_users(count=1)
        await save_users(users)
        contact = await contact_repository.save(
            users[0].id, create_contacts(count=1)[0]
        )

        assert await contact_repository.exists_by_id(contact.id) is True
        assert await contact_repository.exists_by_id(9999) is False

    async def test_find_by_id_returns_contact_with_details(
        self,
        contact_repository,
        user_repository,
        create_users,
        create_contacts,
        save_users,
    ):
        users = create_users(count=1)
        await save_users(users)

        contact = await contact_repository.save(
            users[0].id, create_contacts(count=1, name='Maria')[0]
        )

        found = await contact_repository.find_by_id(contact.id)

        assert found is not None
        assert found.name == 'Maria'
        assert found.user_id == users[0].id
