from fastapi import UploadFile
from pathlib import Path
import shutil
from fastapi.concurrency import run_in_threadpool


class ImageRepository:
    def __init__(self, base_dir: Path, img_dir: str):
        self.base_dir = base_dir.resolve()
        self.img_storage = Path(img_dir).resolve()
        self.img_storage.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile, filename: str, extension: str) -> str:
        final_name = f'{filename}{extension}'
        file_path = self.img_storage / final_name

        def sync_write():
            with file_path.open(
                'wb'
            ) as buffer:  # Criar um arquivo e escrever em codigo binario
                shutil.copyfileobj(file.file, buffer)

            return str(file_path.relative_to(self.base_dir / 'app'))

        return await run_in_threadpool(
            sync_write
        )  # roda processo em outra thread sem bloquear o event loop

    async def delete_file(self, db_path: str | None) -> None:
        if not db_path:
            return
        full_path = await self._get_full_path(db_path)
        await run_in_threadpool(full_path.unlink, missing_ok=True)

    async def _get_full_path(self, db_path: str) -> Path:
        # Reconstrói de forma simétrica: Base + app + caminho do banco
        return self.base_dir / 'app' / db_path
