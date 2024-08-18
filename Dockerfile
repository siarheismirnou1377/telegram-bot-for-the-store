# Используем официальный образ Python в качестве базового
FROM python:3.12.2-slim

# Устанавливаем рабочую директорию в /app
WORKDIR /app

# Копируем файл requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы в рабочую директорию
COPY . .

# Экспортируем переменные окружения из файла .env
ARG ENV_FILE=configs.env
ENV $(grep -v '^#' ${ENV_FILE} | xargs)

# Устанавливаем необходимые пакеты
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app

# Запускаем бота
CMD ["python", "src/telegram_bot/main.py"]