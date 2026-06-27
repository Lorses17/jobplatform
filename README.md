Клонирование репозитория
git clone https://github.com/username/jobplatform-backend.git
cd jobplatform-backend

Установка зависимостей
pip install -r requirements.txt

Настройка переменных окружения
DATABASE_URL=postgresql://postgres:password@localhost:5432/jobplatform
SECRET_KEY=your_secret_key
и тд

Запуск миграций  
alembic upgrade head

Запуск проекта
uvicorn app.main:app --reload

Изменения приватности бакета через контейнер

mc alias set myminio http://minio:9000 ACCESS_KEY SECRET_KEY

mc anonymous set download myminio/resumes

mc anonymous list myminio/resumes
