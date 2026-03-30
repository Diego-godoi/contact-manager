from pytest import mark, raises
from tests.factories import ContactFactory, UserFactory


@mark.asyncio
class TestContactRepositorySave:
    async def test_save_contact_persists_data_correctly(
        self,
        contact_repository,
        user_repository,
    ):
        user = await UserFactory.create(with_contact=None, with_token=None)

        contact_data = ContactFactory.build(
            name='João Silva', phone='11999999999', user=user
        )
        saved_contact = await contact_repository.save(user.id, contact_data)

        assert saved_contact.id is not None
        assert saved_contact.user_id == user.id
        assert saved_contact.name == 'João Silva'
        assert saved_contact.phone == '11999999999'

    @mark.xfail  # sqlite permite o salvamento mesmo com violacao de FK
    async def test_save_contact_fails_with_invalid_user(self, contact_repository):
        # Tenta salvar um contato para um user_id que não existe no banco (violação de FK)
        contact = ContactFactory.build()

        with raises(ValueError) as exc_info:
            await contact_repository.save(9999, contact)

        assert 'Error saving contact to database' in str(exc_info.value)


@mark.asyncio
class TestContactRepositoryDelete:
    async def test_deletes_contact_correctly(
        self,
        contact_repository,
        user_repository,
    ):
        contact = await ContactFactory.create()

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
    ):
        user1 = await UserFactory.create()
        await UserFactory.create(with_contact=True, with_token=None)

        await ContactFactory.create(user=user1)
        await ContactFactory.create(user=user1)

        contacts_user1, total = await contact_repository.get_all(
            user_id=user1.id, page=1, per_page=10
        )

        assert len(contacts_user1) == 2
        assert total == 2
        assert all(c.user_id == user1.id for c in contacts_user1)

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
    ):
        contact = await ContactFactory.create()

        assert await contact_repository.exists_by_id(contact.id) is True
        assert await contact_repository.exists_by_id(9999) is False

    async def test_find_by_id_returns_contact_with_details(
        self,
        contact_repository,
        user_repository,
    ):
        contact = await ContactFactory.create(name='Maria')

        found = await contact_repository.find_by_id(contact.id)

        assert found is not None
        assert found.name == 'Maria'
        assert found.user_id == contact.user_id
