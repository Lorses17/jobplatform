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
        """Асинхронно загружает файл в S3 и принудительно возвращает правильные заголовки для просмотра."""
        async with self.session.client("s3", **self.config) as s3:
            # Сбрасываем указатель файла в начало
            await file.seek(0)

            # Читаем содержимое загруженного файла
            file_content = await file.read()

            # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Если имя файла или объекта заканчивается на .pdf,
            # мы ЖЕСТКО заставляем MinIO сохранить его как PDF и разрешить просмотр (inline)
            if object_name.lower().endswith('.pdf') or (file.filename and file.filename.lower().endswith('.pdf')):
                content_type = "application/pdf"
                content_disposition = "inline"
            else:
                # Для всех остальных типов файлов (картинки и т.д.) оставляем стандартные заголовки
                content_type = file.content_type or "application/octet-stream"
                content_disposition = "inline"

            # Загружаем в бакет с жесткими заголовками
            await s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=object_name,
                Body=file_content,
                ContentType=content_type,
                ContentDisposition=content_disposition
            )

            # Формируем ссылку на файл
            return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{object_name}"


s3_service = S3Service()