import aioboto3
from fastapi import UploadFile
from app.core.config import settings


class S3Service:
    def __init__(self):
        self.session = aioboto3.Session()
        self.config = {
            "endpoint_url": settings.S3_ENDPOINT_URL,
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
        }

    async def upload_file(self, file: UploadFile, object_name: str) -> str:
        """Асинхронно загружает файл в S3 и возвращает его URL."""
        async with self.session.client("s3", **self.config) as s3:
            # Читаем содержимое загруженного файла
            file_content = await file.read()

            # Загружаем в бакет
            await s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=object_name,
                Body=file_content,
                ContentType=file.content_type
            )

            # Формируем ссылку на файл (для локального MinIO или AWS S3)
            return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{object_name}"


s3_service = S3Service()