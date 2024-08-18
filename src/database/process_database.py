"""
Модуль для асинхронной работы с базой данных SQLite и логирования операций.
Этот модуль предоставляет функции для создания таблиц, вставки данных,
подсчета статистики и анализа активности пользователей. Он также настраивает
логирование для отслеживания выполнения функций и возникающих ошибок.
"""
import logging
from logging.handlers import RotatingFileHandler
import os

import asyncio
from datetime import datetime, timedelta
import aiosqlite


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/process_database_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('process_database_logger')
logger.addHandler(file_handler)


# Создание таблицы
async def create_table() -> None:
    """
    Асинхронная функция для создания таблицы в базе данных SQLite.

    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и создает таблицу 'user_events', если она еще не существует. Таблица содержит следующие столбцы:
    - id (INTEGER PRIMARY KEY): Уникальный идентификатор записи.
    - user_id (INTEGER): Идентификатор пользователя.
    - type_user (TEXT): Тип пользователя.
    - event_name (TEXT): Название события.
    - event_type (TEXT): Тип события.
    - event_time (DATE): Время события.
    - event_query (TEXT): Запрос, связанный с событием.
    - event_result (TEXT): Результат события.

    Возвращает:
    None
    """
    try:
        logger.info("Попытка выполнения функции create_table")
        db_path = 'data/statisctics/user_database.db'
        if not os.path.exists(db_path):
            async with aiosqlite.connect('data/statisctics/user_database.db') as db:
                # Создание таблицы
                await db.execute('''
                    CREATE TABLE user_events (
                        id INTEGER PRIMARY KEY, 
                        user_id INTEGER,
                        type_user INTEGER,
                        event_name INTEGER,
                        event_type INTEGER,
                        event_time DATE,
                        event_query TEXT,
                        event_result INTEGER
                    )
                ''')
                await db.commit()
                logger.info("В create_table_message функции база данных user_database создана")
        else:
            # База данных существует, проверяем наличие таблицы
            async with aiosqlite.connect(db_path) as db:
                async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='user_events'"
                    ) as cursor:
                    if await cursor.fetchone() is None:
                        # Создание таблицы
                        await db.execute('''
                            CREATE TABLE user_events (
                                id INTEGER PRIMARY KEY, 
                                user_id INTEGER,
                                type_user INTEGER,
                                event_name INTEGER,
                                event_type INTEGER,
                                event_time DATE,
                                event_query TEXT,
                                event_result INTEGER
                            )
                        ''')
                        await db.commit()
                        logger.info(
                            "В create_table_message функции в базе данных user_database"
                            "была создана таблица user_events"
                            )

    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции create_table: %s", e)
        return None

# Вставка новых данных в таблицу и создание таблицы
async def insert_data(
    user_id: int,
    type_user: int,
    event_name: int,
    event_type:int,
    event_time: datetime,
    event_query: str,
    event_result: int
    ) -> None:
    """
    Асинхронная функция для вставки новых данных в таблицу 'user_events' базы данных SQLite.

    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и вставляет новую запись в таблицу 'user_events' с указанными данными.
    Если базы данных нет, она создаст её, а так же и таблицу в бд создаст.
    
    Параметры:
    user_id (int): Идентификатор пользователя.
    type_user (int): Тип пользователя.
    event_name (int): Название события.
    event_type (int): Тип события.
    event_time (datetime): Время события.
    event_query (str): Запрос, связанный с событием.
    event_result (int): Результат события.

    Возвращает:
    None
    """
    try:
        logger.info("Попытка выполнения функции insert_data")
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # Проверка наличия таблицы user_events
            cursor = await db.execute('''
                SELECT name FROM sqlite_master WHERE type='table' AND name='user_events'
            ''')
            table_exists = await cursor.fetchone()

            if not table_exists:
                # Создание таблицы user_events
                await db.execute('''
                    CREATE TABLE user_events (
                        id INTEGER PRIMARY KEY, 
                        user_id INTEGER,
                        type_user INTEGER,
                        event_name INTEGER,
                        event_type INTEGER,
                        event_time DATE,
                        event_query TEXT,
                        event_result INTEGER
                    )
                ''')
                await db.commit()

        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # Вставка данных в таблицу user_events
            await db.execute('''
                INSERT INTO user_events (user_id, type_user, event_name, event_type, event_time, event_query, event_result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                type_user,
                event_name,
                event_type,
                event_time,
                event_query,
                event_result
                )
            )
            await db.commit()
        logger.info("Функция insert_data выполнилась")
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции insert_data: %s", e)
        return None

# Сколько дали согласие и запустили бота
async def count_users_agreed() -> int | None:
    """
    Асинхронная функция для подсчета количества пользователей, давших согласие.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета уникальных пользователей,
    которые согласились на обработку персональных данных.

    Возвращает:
    int: Количество пользователей, давших согласие.
    """
    try:
        logger.info("Попытка выполнения функции count_users_agreed")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета пользователей, дали согласие и запустили бота
            query = """
            SELECT COUNT(DISTINCT user_id)
            FROM user_events
            WHERE event_name = '0' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_users_agreed выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_users_agreed: %s", e)
        return None

# Сколько раз не дали согласие
async def count_users_unagreed() -> int | None:
    """
    Асинхронная функция для подсчета количества пользователей, не давших согласие.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета уникальных пользователей, 
    которые не согласились на обработку персональных данных.

    Возвращает:
    int: Количество пользователей, не давших согласие.
    """
    try:
        logger.info("Попытка выполнения функции count_users_unagreed")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета сколько раз не дали согласие
            query = """
            SELECT COUNT(DISTINCT user_id)
                FROM user_events AS e1
                WHERE event_name = '1' AND event_result = '1'
                AND NOT EXISTS (
                SELECT 1
                FROM user_events AS e2
                WHERE e1.user_id = e2.user_id AND event_result = '0'
            )
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_users_unagreed выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_users_unagreed: %s", e)
        return None

# Сколько нажали раз кнопку
async def count_button(name_button: int) -> int | None:
    """
    Асинхронная функция для подсчета количества нажатий на определенную кнопку.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества нажатий на кнопку с указанным именем.

    Параметры:
    name_button (str): Название кнопки, для которой необходимо подсчитать количество нажатий.

    Возвращает:
    int: Количество нажатий на указанную кнопку.
    """
    try:
        logger.info("Попытка выполнения функции count_button")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета сколько раз нажали раз кнопку
            query = f"""
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '{name_button}' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_button выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_button: %s", e)
        return None

#Сколько нажали кнопку юзерами по картам
async def count_button_to_card(name_button: int, type_card: int) -> int | None:
    """
    Асинхронная функция для подсчета количества нажатий определенной кнопки 
    пользователями определенного типа карты.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества нажатий на кнопку с указанным именем,
    сделанных пользователями определенного типа карты.

    Параметры:
    name_button (str): Название кнопки, для которой необходимо подсчитать количество нажатий.
    type_card (str): Тип карты, нажатия на кнопку которой необходимо подсчитать.

    Возвращает:
    int: Количество нажатий на указанную кнопку пользователями определенного типа карты.
    """
    try:
        logger.info("Попытка выполнения функции count_button_to_card")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько нажали кнопку юзерами по картам
            query = f"""
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '{name_button}' AND type_user = '{type_card}' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_button_to_card выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_button_to_card: %s", e)
        return None

# Сколько нажали кнопку юзерами без карты
async def count_button_not_card(name_button: int) -> int | None:
    """
    Асинхронная функция для подсчета количества нажатий определенной кнопки 
    пользователями без карты.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества нажатий на кнопку с указанным именем,
    сделанных пользователями без карты.

    Параметры:
    name_button (str): Название кнопки, для которой необходимо подсчитать количество нажатий.

    Возвращает:
    int: Количество нажатий на указанную кнопку пользователями без карты.
    """
    try:
        logger.info("Попытка выполнения функции count_button_not_card")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько нажали кнопку юзерами без карты
            query = f"""
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '{name_button}' AND type_user IS NULL AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_button_not_card выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_button_not_card: %s", e)
        return None

# Сколько всего юзеров
async def count_users() -> int | None:
    """
    Асинхронная функция для подсчета количества всех пользователей.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета уникальных пользователей,
    которые согласились на обработку персональных данных.

    Возвращает:
    int: Количество всех пользователей, согласившихся на обработку персональных данных.
    """
    try:
        logger.info("Попытка выполнения функции count_users")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько всего юзеров
            query = """
            SELECT COUNT(DISTINCT user_id)
            FROM user_events
            WHERE event_name = '0' AND event_result = '1' 
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_users выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_users: %s", e)
        return None

# Сколько всего юзеров по карте
async def count_users_to_card(type_users: int) -> int | None:
    """
    Асинхронная функция для подсчета количества всех пользователей определенного типа карты.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета уникальных пользователей, которые относятся
    к определенному типу карты.

    Параметры:
    type_users (str): Тип карты, для которого необходимо подсчитать количество пользователей.

    Возвращает:
    int: Количество всех пользователей, относящихся к указанному типу карты.
    """
    try:
        logger.info("Попытка выполнения функции count_users_to_card")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько всего юзеров по карте
            query = f"""
            SELECT COUNT(DISTINCT user_id)
            FROM user_events
            WHERE type_user = '{type_users}'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_users_to_card выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_users_to_card: %s", e)
        return None

# Сколько всего юзеров без карт
async def count_users_not_card() -> int | None:
    """
    Асинхронная функция для подсчета количества всех пользователей без карты.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета уникальных пользователей, которые не имеют карты.

    Возвращает:
    int: Количество всех пользователей, не имеющих карты.
    """
    try:
        logger.info("Попытка выполнения функции count_users_not_card")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько всего юзеров без карт
            query = """
            SELECT COUNT(DISTINCT user_id)
            FROM user_events
            WHERE user_id NOT IN (
                SELECT user_id
                FROM user_events
                WHERE type_user IS NOT NULL
            ) AND type_user IS NULL
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info("Функция count_users_not_card выполнилась с данными %s", result[0])
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_users_not_card: %s", e)
        return None

# Сколько успешно-выполненных запросов по поиску товара по названию
async def count_search_done_to_name() -> int | None:
    """
    Асинхронная функция для подсчета количества успешно выполненных запросов
    по поиску товара по названию.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества успешно выполненных запросов
    по поиску товара по названию.

    Возвращает:
    int: Количество успешно выполненных запросов по поиску товара по названию.
    """
    try:
        logger.info("Попытка выполнения функции count_search_done_to_name")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько успешно-выполненных
            # запросов по поиску товара по названию
            query = """
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '30' AND event_type = '1' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info(
                    "Функция count_search_done_to_name выполнилась с данными %s",
                    result[0]
                    )
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_search_done_to_name: %s", e)
        return None

# Сколько успешно-выполненных запросов по поиску товара по коду товара
async def count_search_done_to_code_product() -> int | None:
    """
    Асинхронная функция для подсчета количества успешно выполненных запросов
    по поиску товара по коду товра.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества успешно выполненных запросов 
    по поиску товара по коду товара.

    Возвращает:
    int: Количество успешно выполненных запросов по поиску товара по коду товара.
    """
    try:
        logger.info("Попытка выполнения функции count_search_done_to_code_product")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            query = """
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '31' AND event_type = '1' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info(
                    "Функция count_search_done_to_code_product выполнилась с данными %s",
                    result[0]
                    )
                # Вывод
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_search_done_to_code_product: %s", e)
        return None

# Сколько успешно-выполненных запросов по поиску товара по тексту штрихкода
async def count_search_done_to_code_text() -> int | None:
    """
    Асинхронная функция для подсчета количества успешно выполненных запросов 
    по поиску товара по тексту штрихкода.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества успешно выполненных запросов
    по поиску товара по тексту штрихкода.

    Возвращает:
    int: Количество успешно выполненных запросов по поиску товара по тексту штрихкода.
    """
    try:
        logger.info("Попытка выполнения функции count_search_done_to_code_text")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько успешно-выполненных
            # запросов по поиску товара по тексту штрихкода
            query = """
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '32' AND event_type = '1' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info(
                    "Функция count_search_done_to_code_text выполнилась с данными %s",
                    result[0]
                    )
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_search_done_to_code_text: %s", e)
        return None

# Сколько успешно-выполненных запросов по поиску товара по фото штрихкода товара
async def count_search_done_to_code_photo() -> int | None:
    """
    Асинхронная функция для подсчета количества успешно выполненных запросов
    по поиску товара по фото штрихкода.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для подсчета количества успешно выполненных запросов по поиску
    товара по фото штрихкода.

    Возвращает:
    int: Количество успешно выполненных запросов по поиску товара по фото штрихкода.
    """
    try:
        logger.info("Попытка выполнения функции count_search_done_to_code_photo")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета Сколько успешно-выполненных
            # запросов по поиску товара по фото штрихкода товара
            query = """
            SELECT COUNT(event_name)
            FROM user_events
            WHERE event_name = '33' AND event_type = '1' AND event_result = '1'
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                result = await cursor.fetchone()
                logger.info(
                    "Функция count_search_done_to_code_photo выполнилась с данными %s",
                    result[0]
                    )
                # Вывод количества пользователей
                return result[0]
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции count_search_done_to_code_photo: %s", e)
        return None

# Самые частые запросы по поиску по слову
async def popular_search_query() -> list | None:
    """
    Асинхронная функция для получения списка самых частых запросов по поиску по слову.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для выбора самых частых запросов по поиску по слову.

    Возвращает:
    list: Список строк, каждая из которых содержит самый частый запрос и количество его вхождений.
    """
    try:
        logger.info("Попытка выполнения функции popular_search_query")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # SQL-запрос для подсчета самых частых запросов
            query = """
            SELECT event_query, COUNT(*) as count
            FROM user_events
            WHERE event_query IS NOT NULL 
            AND event_name = '30'
            GROUP BY event_query
            ORDER BY count DESC
            LIMIT 5
            """
            # Выполнение запроса
            async with db.execute(query) as cursor:
                # Получение результата
                results = await cursor.fetchall()
                # Вывод результатов
                result_list = []
                for result in results:
                    result_list.append(f"Запрос: {result[0]}\nКоличество: {result[1]}")
                logger.info("Функция popular_search_query выполнилась с данными %s", result_list)
                return result_list
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции popular_search_query: %s", e)
        return None

# Функция для определения периода суток
async def get_time_of_day(hour: int) -> str | None:
    """
    Асинхронная функция для определения периода суток на основе переданного часа.
    Функция использует асинхронную задержку (asyncio.sleep) для имитации асинхронной операции,
    но в данном случае это необходимо, так как синтаксис async/await
    требует наличия хотя бы одной асинхронной операции.

    Параметры:
    hour (int): Час дня в 24-часовом формате.

    Возвращает:
    str: Строка, указывающая на период суток в соответствии с переданным часом.
    """
    try:
        logger.info("Попытка выполнения функции get_time_of_day")
        await asyncio.sleep(0)
        if 5 <= hour < 12:
            logger.info("Функция get_time_of_day выполнилась с данными с 5:00 до 12:00")
            return 'с 5:00 до 12:00'
        elif 12 <= hour < 18:
            logger.info("Функция get_time_of_day выполнилась с данными с 12:00 до 18:00")
            return 'с 12:00 до 18:00'
        elif 18 <= hour < 22:
            logger.info("Функция get_time_of_day выполнилась с данными с 18:00 до 22:00")
            return 'с 18:00 до 22:00'
        elif 22 <= hour < 5:
            logger.info("Функция get_time_of_day выполнилась с данными с 22:00 до 5:00")
            return 'с 22:00 до 5:00'
    except (IndexError, ValueError) as e:
        logger.error("Произошла ошибка в функции get_time_of_day: %s", e)
        return None

# Функция для определения дня недели
async def get_day_of_week(day_number: int) -> str | None:
    """
    Асинхронная функция для определения дня недели на основе переданного номера дня.

    Функция использует асинхронную задержку (asyncio.sleep) для имитации асинхронной операции,
    но в данном случае это необходимо, так как синтаксис async/await требует наличия 
    хотя бы одной асинхронной операции.

    Параметры:
    day_number (int): Номер дня недели, где 0 - это понедельник,
    1 - вторник, и т.д. до 6 - воскресенье.

    Возвращает:
    str: Строка, представляющая день недели, соответствующий переданному номеру дня.
    """
    try:
        logger.info("Попытка выполнения функции get_day_of_week")
        await asyncio.sleep(0)
        days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        logger.info("Функция get_day_of_week выполнилась с данными %s", days[day_number])
        return days[day_number]
    except (IndexError, ValueError) as e:
        logger.error("Произошла ошибка в функции get_day_of_week: %s", e)
        return None

# Часы активности
async def time_serch_popular() -> list | None:
    """
    Асинхронная функция для получения часов активности поисковых запросов от пользователей.
    Функция асинхронно устанавливает соединение с базой данных 'data\\statisctics\\user_database.db'
    и выполняет SQL-запрос для выбора самых частых запросов по поиску за последний год.

    Возвращает:
    list: Список строк, каждая из которых содержит день недели, период суток и количество запросов,
    которые были наиболее частыми за последний год.
    """
    try:
        logger.info("Попытка выполнения функции time_serch_popular")
        # Подключение к базе данных
        async with aiosqlite.connect('data/statisctics/user_database.db') as db:
            # Вычисление даты начала последнего года
            last_year = datetime.now() - timedelta(days=365)
            # SQL-запрос для подсчета самых частых запросов за последний год
            query = """
            SELECT strftime('%w', event_time) as day_of_week, strftime('%H', event_time) as hour, COUNT(*) as count
            FROM user_events
            WHERE event_result = '1'
            AND (event_name = '30' OR event_name = '31' OR event_name = '32' OR event_name = '33')
            AND event_time >= ?
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, count DESC
            """
            # Выполнение запроса с параметром для даты начала последнего года
            async with db.execute(query, (last_year,)) as cursor:
                # Получение результата
                results = await cursor.fetchall()
                # Вывод результатов
                day_of_week_results = {}
                list_result_popular = []
                for result in results:
                    day_of_week = await get_day_of_week(int(result[0]))
                    hour = int(result[1])

                    time_of_day = await get_time_of_day(hour)
                    if (day_of_week not in day_of_week_results) or \
                        (day_of_week_results[day_of_week][2] < result[2]):
                        day_of_week_results[day_of_week] = (time_of_day, hour, result[2])

                for day_of_week, (time_of_day, hour, count) in day_of_week_results.items():
                    list_result_popular.append(
                        f"{day_of_week} \n{time_of_day}\nКоличество запросов: {count}"
                        )
                logger.info(
                    "Функция time_serch_popular выполнилась с данными %s",
                    list_result_popular
                    )
                print(list_result_popular)
                return list_result_popular
    except aiosqlite.Error as e:
        logger.error("Произошла ошибка в функции time_serch_popular: %s", e)
        return None

asyncio.run(create_table())
