import io
from fastapi import UploadFile
from pytest import mark


@mark.asyncio
class TestImageRepositorySave:
    async def test_save_image_successfully(self, image_repo):
        content = b'\x89PNG\r\n\x1a\n'
        fake_file = UploadFile(filename='avatar.png', file=io.BytesIO(content))

        db_path = await image_repo.save(fake_file, 'user_1', '.png')

        # O retorno deve ser exatamente o caminho relativo, sem 'app/' no início
        assert db_path == 'static/profile-picture/user_1.png'

        full_disk_path = image_repo.img_storage / 'user_1.png'
        assert full_disk_path.exists()
        assert full_disk_path.read_bytes() == content


@mark.asyncio
class TestImageRepositoryDelete:
    async def test_delete_file_successfully(self, image_repo):
        file_name = 'to_delete.png'
        (image_repo.img_storage / file_name).write_bytes(b'data')

        db_path = f'static/profile-picture/{file_name}'

        await image_repo.delete_file(db_path)

        assert not (image_repo.img_storage / file_name).exists()

    async def test_delete_non_existent_file_does_not_raise_error(self, image_repo):
        await image_repo.delete_file('static/profile-picture/ghost.png')
