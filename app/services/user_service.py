from app.errors.exceptions import ConflictError, NotFoundError, FileError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.img_repository import ImageRepository
from app.schemas.schemas import UserRequest
from fastapi import UploadFile


class UserService:
    def __init__(self, repository: UserRepository, img_repository: ImageRepository):
        self.repository = repository
        self.img_repository = img_repository

    async def create_user(self, data: UserRequest) -> User:
        if await self.repository.exists_by_email(data.email):
            raise ConflictError(detail='Email already exists')

        user: User = User(name=data.name, email=data.email, password='')
        await user.set_password(data.password)
        return await self.repository.save(user)

    async def update_user(self, id: int, data: UserRequest) -> User:
        user: User = await self.repository.find_by_id(id)

        if user is None:
            raise NotFoundError(detail='User not found')

        if user.email != data.email:
            if await self.repository.exists_by_email(data.email):
                raise ConflictError(detail='Email already exists')

            user.email = data.email

        user.name = data.name
        await user.set_password(data.password)

        return await self.repository.save(user)

    async def delete_user(self, id: int) -> bool:
        user: User = await self.repository.find_by_id(id)
        if user is None:
            raise NotFoundError(detail='User not found')

        await self.img_repository.delete_file(user.profile_picture_path)
        return await self.repository.delete(id)

    async def get_all_users(self, page: int, per_page: int):
        items, total = await self.repository.get_all(page, per_page)
        pages = (total + per_page - 1) // per_page
        return items, total, pages

    async def set_profile_picture(self, user_id: int, picture: UploadFile) -> str:
        user: User = await self.repository.find_by_id(user_id)
        if user is None:
            raise NotFoundError(detail='User not found')

        valid_ext: str = await self._validate_image(picture)

        old_db_path = user.profile_picture_path

        new_file_path = await self.img_repository.save(
            file=picture, filename=str(user_id), extension=valid_ext
        )

        if old_db_path:
            await self.img_repository.delete_file(old_db_path)

        user.profile_picture_path = new_file_path
        await self.repository.save(user)

        return new_file_path

    @staticmethod
    async def _validate_image(file: UploadFile):
        MAX_FILE_SIZE = 2 * 1024 * 1024
        ALLOWED_TYPES = {
            'image/jpeg': {'header': b'\xff\xd8\xff', 'ext': '.jpg'},
            'image/png': {'header': b'\x89\x50\x4e\x47', 'ext': '.png'},
        }
        file_size = file.size if file.size is not None else 0
        if file_size > MAX_FILE_SIZE:
            raise FileError(detail='The file is too large. The limit is 2 MB')

        if file.content_type not in ALLOWED_TYPES:
            raise FileError(detail='The file type is not allowed')

        header = await file.read(4)
        await file.seek(0)

        expected_header = ALLOWED_TYPES[file.content_type]['header']
        if not header.startswith(expected_header):
            raise FileError(detail='The file content does not match its extension')

        return ALLOWED_TYPES[file.content_type]['ext']
