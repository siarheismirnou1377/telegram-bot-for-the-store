"""
Модуль для асинхронного чтения и обновления JSON-файлов.
Этот модуль предоставляет функции для асинхронного чтения и обновления JSON-файлов.
Он также настраивает логирование для отслеживания выполнения функций и возникающих ошибок.
"""
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Any

import aiofiles


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/read_json_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('read_json_logger')
logger.addHandler(file_handler)

async def read_json_file(filename: str) -> Any:
    """
    Асинхронно читает JSON-файл и возвращает его содержимое в виде объекта Python.

    :param filename: Путь к JSON-файлу.
    :return: Объект Python, содержащий данные из JSON-файла.
    """
    logger.info(
        "Выполнение функции read_json_file, c полученными данными - %s",
        filename
        )
    # Открываем файл для асинхронного чтения
    async with aiofiles.open(filename, 'r', encoding='utf-8') as file:
        logger.info(
            "Открытие файла в read_json_file, c полученными данными - %s",
            filename
            )
        # Читаем содержимое файла
        contents = await file.read()
        # Десериализуем содержимое в объект Python
        data = json.loads(contents)
    logger.info(
        "Получены данные в read_json_file, c полученными данными - %s",
        filename
        )
    return data

async def update_json_file(new_data: dict, filename: str) -> None:
    """
    Асинхронно обновляет JSON-файл новыми данными.

    :param new_data: Словарь с новыми данными для обновления.
    :param filename: Путь к JSON-файлу.
    """
    logger.info(
        "Выполнение функции update_json_file, c полученными данными -new_data и %s",
        filename
        )
    existing_data = {}

    # Пытаемся открыть и прочитать файл
    try:
        logger.info(
            "Попытка чтения фала в update_json_file,"
            "c полученными данными - new_data и %s",
            filename
            )
        async with aiofiles.open(filename, 'r', encoding='utf-8') as f:
            contents = await f.read()
            # Если файл не пустой, пытаемся загрузить данные JSON
            if contents:
                logger.info(
                    "Получение из файла %s в update_json_file, данных contents",
                    filename
                    )
                existing_data = json.loads(contents)
    except FileNotFoundError as e:
        logger.error(
            "Получение ошибки %s в update_json_file, Если файл %s не существует, "
            "он будет создан при первой записи",
            e, filename
            )

    except json.JSONDecodeError as e:
        # Если файл содержит некорректные данные JSON, логируем сообщение об ошибке
        logger.error(
            "Получение ошибки %s: Файл %s содержит некорректные данные JSON.",
            e, filename
            )

    # Обновляем словарь новыми данными
    existing_data.update(new_data)
    logger.info(
        "Обновляем словаря новыми данными в update_json_file, "
        "c полученными данными - new_data и %s",
        filename
        )
    # Записываем обновленные данные обратно в файл
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(existing_data, ensure_ascii=False, indent=4))
        logger.info(
            "Запись данных в update_json_file по пути %s , c полученными данными - %s",
            filename, existing_data
            )

async def read_json_keys_as_ints(file_path: str) -> list[int]:
    """
    Асинхронно открываем файл и считываем JSON-объект.
    
    :param file_path: Путь к JSON-файлу.
    """
    try:
        logger.info(
            "Выполнение функции update_json_file, c полученными данными -new_data и %s",
            file_path
            )
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            contents = await file.read()
            data = json.loads(contents)

        # Получаем список ключей и преобразуем их в целые числа
        keys_as_ints = [int(key) for key in data.keys()]
        return keys_as_ints
    except FileNotFoundError as e:
        logger.error(
            "Получение ошибки %s в update_json_file, Если файл %s не существует, "
            "он будет создан при первой записи",
            e, file_path
            )
        return None
    except json.JSONDecodeError as e:
        # Если файл содержит некорректные данные JSON, логируем сообщение об ошибке
        logger.error(
            "Получение ошибки %s: Файл %s содержит некорректные данные JSON.",
            e, file_path
            )
        return None
