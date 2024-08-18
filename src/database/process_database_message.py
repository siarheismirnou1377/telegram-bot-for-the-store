"""
Модуль для асинхронной работы с базой данных SQLite и логирования операций.
Этот модуль предоставляет функции для создания таблиц, вставки данных,
получения статистики и анализа сообщений. Он также настраивает
логирование для отслеживания выполнения функций и возникающих ошибок.
"""
import logging
import asyncio
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os

import aiosqlite


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/process_database_message_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('process_database_message_logger')
logger.addHandler(file_handler)

# Создание таблицы
async def create_table_message() -> None:
    """
    Асинхронная функция для создания таблицы в базе данных 'data\\statisctics\\message_database.db'.

    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для создания таблицы 'message_id_db', если она еще не существует.

    Таблица 'message_id_db' содержит следующие столбцы:
    - id: Первичный ключ, целочисленный идентификатор записи.
    - id_message: Целочисленный идентификатор сообщения.
    - type_message: Тип сообщения, представленный в виде текста.
    - type_user: Тип пользователя, представленный в виде текста.
    - id_user: Целочисленный идентификатор пользователя.
    - time_message: Дата и время отправки сообщения, представленные в виде даты.

    Возвращает:
    None
    """
    try:
        logger.info("Попытка выполнения функции create_table_message")
        db_path = 'data/statisctics/message_database.db'
        if not os.path.exists(db_path):
            async with aiosqlite.connect(db_path) as db:
                # Создание таблицы
                await db.execute('''
                    CREATE TABLE message_id_db (
                                id INTEGER PRIMARY KEY, 
                                id_message INTEGER,
                                type_message INTEGER,
                                type_user INTEGER,
                                id_user INTEGER,
                                time_message DATE
                    )
                ''')
                await db.commit()
                logger.info("В create_table_message функции база данных message_database создана")
        else:
            # База данных существует, проверяем наличие таблицы
            async with aiosqlite.connect(db_path) as db:
                async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='message_id_db'"
                    ) as cursor:
                    if await cursor.fetchone() is None:
                        await db.execute('''
                            CREATE TABLE message_id_db (
                                        id INTEGER PRIMARY KEY, 
                                        id_message INTEGER,
                                        type_message INTEGER,
                                        type_user INTEGER,
                                        id_user INTEGER,
                                        time_message DATE
                            )
                        ''')
                await db.commit()
                logger.info(
                    "В create_table_message функции в базе данных message_database "
                    "была создана таблица message_id_db"
                    )
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции create_table_message: %s", e)
        return None

# Создание таблицы и Вставка новых данных в таблицу
async def insert_message_data(
    id_message: int,
    type_message: int,
    type_user: int,
    id_user: int,
    time_message: datetime
    ) -> None:
    """
    Асинхронная функция для вставки данных в таблицу 'message_id_db'
    в базе данных 'data\\statisctics\\message_database.db'.
    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для вставки данных в таблицу 'message_id_db'.
    Если базы данных нет, она создаст её, а так же и таблицу в бд создаст.
    
    Параметры:
    id_message (int): Целочисленный идентификатор сообщения.
    type_message (int): Тип сообщения, представленный в виде целого числа.
    type_user (int): Тип пользователя, представленный в виде целого числа.
    id_user (int): Целочисленный идентификатор пользователя.
    time_message (data): Дата и время отправки сообщения, представленные в виде даты.

    Возвращает:
    None
    """
    try:
        logger.info("Попытка выполнения функции insert_message_data")
        async with aiosqlite.connect('data/statisctics/message_database.db') as db:
            # Проверка наличия таблицы message_id_db
            cursor = await db.execute('''
                SELECT name FROM sqlite_master WHERE type='table' AND name='message_id_db'
            ''')
            table_exists = await cursor.fetchone()

            if not table_exists:
                # Создание таблицы message_id_db
                await db.execute('''
                    CREATE TABLE message_id_db (
                        id INTEGER PRIMARY KEY, 
                        id_message INTEGER,
                        type_message INTEGER,
                        type_user INTEGER,
                        id_user INTEGER,
                        time_message DATE
                    )
                ''')
                await db.commit()

            # Вставка данных в таблицу message_id_db
            await db.execute('''
                INSERT INTO message_id_db (id_message, type_message, type_user, id_user, time_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_message, type_message, type_user, id_user, time_message))
            await db.commit()
            logger.info("Функция insert_message_data выполнилась")
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции insert_message_data: %s", e)
        return None

# Получение всех уникальных id_message
async def get_id_message() -> int | None:
    """
    Асинхронная функция для получения количества уникальных значений 
    'id_message' из таблицы 'message_id_db' в базе данных 'data\\statisctics\\message_database.db'.
    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для подсчета уникальных значений 'id_message' в таблице 'message_id_db'.

    Возвращает:
    int: Количество уникальных значений 'id_message' в таблице 'message_id_db'.
    """
    try:
        logger.info("Попытка выполнения функции get_id_message")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/message_database.db') as db:
            async with db.execute('SELECT COUNT(DISTINCT id_message) FROM message_id_db') as cursor:
                rows = await cursor.fetchall()
                unique_ids = [row[0] for row in rows]
                logger.info("Функция get_id_message выполнилась с данными %s", unique_ids[0])
                return unique_ids[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции get_id_message: %s", e)
        return None

# Сколько отправлено публикаций всего по типу юзеров
async def get_id_message_user_type(type_card: int) -> int | None:
    """
    Асинхронная функция для подсчета количества уникальных сообщений
    по определенному типу пользователей в таблице 'message_id_db'
    в базе данных 'data\\statisctics\\message_database.db'.
    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для подсчета уникальных значений 'id_message' в таблице 'message_id_db',
    отфильтрованных по типу пользователя.

    Параметры:
    type_card (str): Тип пользователя, по которому производится фильтрация.

    Возвращает:
    int: Количество уникальных сообщений, отправленных пользователями заданного типа.
    """
    try:
        logger.info("Попытка выполнения функции get_id_message_user_type")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/message_database.db') as db:
            query = f"""
            SELECT COUNT(DISTINCT id_message)
            FROM message_id_db
            WHERE type_user = '{type_card}'
            """
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция get_id_message_user_type выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции get_id_message_user_type: %s", e)
        return None

# Получение количества по виду публикации
async def get_type_message(type_post: int) -> int | None:
    """
    Асинхронная функция для подсчета количества уникальных сообщений
    по определенному типу публикации в таблице 'message_id_db' в базе данных
    'data\\statisctics\\message_database.db'.
    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для подсчета уникальных значений 'id_message' в таблице 'message_id_db',
    отфильтрованных по типу публикации.

    Параметры:
    type_post (str): Тип публикации, по которому производится фильтрация.

    Возвращает:
    int: Количество уникальных сообщений заданного типа публикации.
    """
    try:
        logger.info("Попытка выполнения функции get_type_message")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/message_database.db') as db:
            query = f"""
            SELECT COUNT(DISTINCT id_message)
            FROM message_id_db
            WHERE type_message = '{type_post}'
            """
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                # Вывод количества пользователей
                logger.info("Функция get_type_message выполнилась с данными %s", result[0])
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции get_type_message: %s", e)
        return None

# Всего публикаций для каждого типа пользователя по типам публикаций
async def get_unique_posts_per_user_type() -> list | None:
    """
    Асинхронная функция для получения количества уникальных публикаций для каждого типа пользователя
    по типам публикаций в таблице 'message_id_db' в базе данных 'data\\statisctics\\message_database.db'.
    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для подсчета уникальных значений 'id_message' в таблице 'message_id_db', 
    группируя их по типам пользователей и типам публикаций.

    Возвращает:
    list: Список кортежей, где каждый кортеж содержит тип пользователя,
    тип публикации и количество уникальных публикаций.
    """
    try:
        logger.info("Попытка выполнения функции get_unique_posts_per_user_type")
        async with aiosqlite.connect('data/statisctics/message_database.db') as db:
            async with db.execute("""
                SELECT type_user, type_message, COUNT(DISTINCT id_message) as unique_posts
                FROM message_id_db
                GROUP BY type_user, type_message;
            """) as cursor:
                results = await cursor.fetchall()
                logger.info(
                    "Функция get_unique_posts_per_user_type выполнилась с данными %s",
                    results
                    )
                return results
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции get_unique_posts_per_user_type: %s", e)
        return None

# Получение последнего id_message
async def get_last_id_message() -> int | None:
    """
    Асинхронная функция для получения последнего значения 'id_message' из таблицы 'message_id_db'
    в базе данных 'data\\statisctics\\message_database.db'.

    Функция асинхронно устанавливает соединение с базой данных и выполняет SQL-запрос
    для выбора уникальных значений 'id_message' в таблице 'message_id_db'.

    Возвращает:
    int: Последнее значение 'id_message' в таблице 'message_id_db'.
    """
    try:
        logger.info("Попытка выполнения функции get_last_id_message")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/message_database.db') as db:
            async with db.execute('SELECT DISTINCT id_message FROM message_id_db') as cursor:
                rows = await cursor.fetchall()
                unique_ids = [row[0] for row in rows]
                logger.info("Функция get_last_id_message выполнилась с данными %s", unique_ids[-1])
                return unique_ids[-1]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции get_last_id_message: %s", e)
        return None

asyncio.run(create_table_message())
