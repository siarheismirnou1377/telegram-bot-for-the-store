"""
Модуль предоставляет асинхронные функции для обработки данных, включая проверку
существования изображения,форматирование атрибутов продукта, получение статуса
и количества товара, поиск совпадающих ключей,добавление данных в JSON-файл,
поиск идентификатора пользователя и цензурирование нежелательных слов.
"""

import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler

import aiofiles
import aiohttp
from check_swear import SwearingCheck
from cachetools import TTLCache

logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/check_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('check_logger')
logger.addHandler(file_handler)

sch = SwearingCheck()

# Создаем кэш и блокировку по умолчанию
default_rate_limit_cache = TTLCache(maxsize=1000, ttl=60)
default_cache_lock = asyncio.Lock()

async def check_image_exists(image_url: str) -> bool:
    """
    Асинхронно проверяет, существует ли удаленное изображение по заданному URL.

    :param image_url: URL изображения.
    :return: True, если изображение существует, иначе False.
    """
    logger.info("Выполнение функции check_image_exists, c полученными данными - image_url")
    async with aiohttp.ClientSession() as session:
        async with session.head(image_url) as response:
            return response.status == 200

async def format_product_attributes(product_attributes_to_id: list[dict]) -> str:
    """
    Асинхронно форматирует атрибуты продукта и возвращает их в виде строки.

    :param product_attributes_to_id: Список словарей, содержащих атрибуты продукта.
    :return: Отформатированные атрибуты продукта в виде строки.
    """
    logger.info(
        "Выполнение функции format_product_attributes"
        "c полученными данными - product_attributes_to_id"
        )
    answ_text_att = '<strong>Характеристики:</strong>\n'

    if product_attributes_to_id:
        logger.info(
            "Полученные данные в format_product_attributes "
            "- product_attributes_to_id начали обрабатываться в первом условии")
        for i in product_attributes_to_id[0]['attribute']:
            text_at = f'{i["name"]} - {i["text"]}\n'
            answ_text_att += text_at
    else:
        logger.info(
            "Полученные данные в format_product_attributes - "
            "product_attributes_to_id начали обрабатываться во втором условии")
        answ_text_att += 'Данных нет.'

    if product_attributes_to_id and len(product_attributes_to_id) > 1:
        logger.info(
            "Полученные данные в format_product_attributes - "
            "product_attributes_to_id начали обрабатываться втретьем условии")
        for j in product_attributes_to_id[1]['attribute']:
            text_at2 = f'{j["name"]} - {j["text"]}\n'
            answ_text_att += text_at2
    logger.info("Обработанные данные в format_product_attributes - answ_text_att возвращены")
    return answ_text_att

async def get_product_status_quantity(product_information_to_id: dict) -> str:
    """
    Асинхронно получает информацию о количестве товара и возвращает статус товара.

    :param product_information_to_id: Словарь с информацией о товаре, включая количество.
    :return: Статус товара в виде строки, указывающей на его наличие или отсутствие.
    """
    logger.info(
        "Выполнение функции get_product_status_quantity "
        "c полученными данными - product_information_to_id"
        )
    product_quatnity = float(product_information_to_id['quantity'])
    #product_status = product_information_to_id['stock_status']

    # Имитация асинхронной операции с помощью asyncio.sleep
    await asyncio.sleep(0)  # Это необходимо, чтобы функция была асинхронной

    if int(product_quatnity) > 0:
        logger.info(
            "Выполнение первого условия в get_product_status_quantity "
            "c полученными данными - product_information_to_id. Возвращено - %s",
            product_quatnity
            )
        return f'В наличии - {int(product_quatnity)} шт.'
    else:
        logger.info(
            "Выполнение первого условия в get_product_status_quantity "
            "c полученными данными - product_information_to_id. "
            "Возвращено - 'Нет в наличии.'"
            )
        return 'Нет в наличии.'

async def find_matching_key(card_field_two: str, data_id_card: dict) -> str | None:
    """
    Асинхронно ищет совпадающий ключ в словаре data_id_card,
    соответствующий значению card_field_two.

    :param card_field_two: Значение, которому должен соответствовать ключ в словаре.
    :param data_id_card: Словарь, в котором производится поиск совпадающего ключа.
    :return: Совпадающий ключ, если он найден, иначе None.
    """
    logger.info(
        "Выполнение функции find_matching_key c полученными данными "
        "- card_field_two  и data_id_card."
        )
    # Инициализируем переменную для хранения совпадающего ключа
    # Итерируем по ключам в словаре data_id_card
    for key in data_id_card:
        await asyncio.sleep(0)
        logger.info(
            "Цикл проверки в find_matching_key c полученными данными - "
            "card_field_two  и data_id_card."
            )
        # Если ключ совпадает с card_field_two, сохраняем его и выходим из цикла
        if key == str(card_field_two):
            logger.info(
                "Первое условие цикла проверки в find_matching_key c полученными данными "
                "- card_field_two  и data_id_card. Возвращено key."
                )
            return key
    logger.info(
        "В find_matching_key c полученными данными "
        "- card_field_two  и data_id_card. Возвращено - %s.", None
        )
    return None

async def add_data_to_json(file_path: str, key: str, data: dict):
    """
    Асинхронно добавляет данные в JSON-файл.

    :param file_path: Путь к JSON-файлу.
    :param key: Ключ, по которому будут добавлены данные.
    :param data: Данные, которые нужно добавить в JSON-файл.
    """
    logger.info(
        "Выполнение функции add_data_to_json c полученными данными -"
        "%s, %s, %s.", file_path, key, data
        )
    # Асинхронно открываем файл и загружаем данные
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        contents = await file.read()
        json_data = json.loads(contents)
        logger.info(
            "Открытие файла %s в add_data_to_json c полученными данными - "
            "%s, %s. Вывод json_data.", file_path, key, data
            )
    # Проверяем, существует ли уже ключ в словаре
    if key in json_data:
        logger.info(
            "Первое условие проверки json_data в add_data_to_json, "
            "на существование %s в json_data.", key
            )
        # Если ключ существует, проверяем, есть ли данные в списке
        if data not in json_data[key]:
            logger.info(
                "Первое условие проверки %s в add_data_to_json, на существование %s в %s. "
                "Добавляем %s в список.", json_data[key], data, json_data[key], data
                )
            # Если данных нет, добавляем их в список
            json_data[key].append(data)
    else:
        # Если ключа нет, создаем новый список с данными
        json_data[key] = [data]
        logger.info(
            "Второе условие проверки json_data в add_data_to_json, "
            "на существование %s в json_data. Записываем в %s данные %s.",
            key, json_data[key], [data]
            )

    # Асинхронно записываем обновленные данные обратно в файл
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
        logger.info("Записываем данные json_data в файл %s в add_data_to_json.", file_path)

async def find_user_id(user_id: int, file_path: str) -> int | None:
    """
    Асинхронная функция для поиска идентификатора пользователя в файле JSON.
    Функция асинхронно открывает файл по указанному пути, читает его содержимое,
    десериализует JSON в Python-объект, ищет идентификатор пользователя в полученных данных.

    Параметры:
    user_id (int): Идентификатор пользователя, который необходимо найти.
    file_path (str): Путь к файлу JSON, в котором производится поиск.

    Возвращает:
    str или None: Если идентификатор пользователя найден,
    функция возвращает соответствующий ключ из JSON-файла.
    Если пользователь не найден, функция возвращает None.
    """
    logger.info(
        "Начало выполнения функции find_user_id с данными user_id = %s, file_path = %s",
        user_id, file_path
        )
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        contents = await file.read()
        data = json.loads(contents)
        for key, value in data.items():
            if int(user_id) in value:
                if key == "ЦУ0000001":
                    return 1
                elif key == "Р00000002":
                    return 2
                elif key == "ЦУ0000003":
                    return 3
                elif key == "ЦУ0000004":
                    return 4
                elif key == "ЦУ0000005":
                    return 5
        logger.info(
            "Функция find_user_id выполнилась с данными user_id = %s, file_path = %s",
            user_id, file_path
            )
    return None

async def censor_swear_words(text: str) -> str:
    """
    Асинхронно обрабатывает текст, заменяя нежелательные слова звездочками.

    Эта функция разбивает входной текст на слова, проверяет каждое слово на предмет
    нежелательного содержания с использованием модели `sch.predict`, и заменяет
    такие слова звездочками.

    :param text: Входной текст для цензуры.
    :type text: str
    :return: Текст с замененными нежелательными словами звездочками.
    :rtype: str

    Пример использования:
    >>> await censor_swear_words("This is a bad word")
    'This is a **** word'
    """
    words = text.split()
    asyncio.sleep(0.0001)
    for i, word in enumerate(words):
        if sch.predict([word])[0] == 1:
            words[i] = '*' * len(word)
    return ' '.join(words)

def quatity_discount(product_data_quantity: list[dict]) -> list:
    """
    Форматирует количества товаров из списка словарей и возвращает их в виде списка строк.

    Эта функция принимает список словарей, каждый из которых содержит информацию о количестве товара
    для двух разных мест хранения (например, "космонавтов" и "дзержинского"). Количество товара
    форматируется в зависимости от того, является ли оно целым числом или числом 
    с плавающей запятой. Результат форматирования добавляется в список,
    который затем возвращается.

    :param product_data_quantity: Список словарей, содержащих информацию о количестве товара.
                                 Каждый словарь должен содержать ключ 'quantity'.
    :type product_data_quantity: list[dict]
    :return: Список строк, содержащих отформатированные количества товара.
    :rtype: list
    """

    list_product_data_quantity_store = []
    if len(product_data_quantity) != 0:
        quantity_1 = float(product_data_quantity[0].get('quantity'))
        quantity_2 = float(product_data_quantity[1].get('quantity'))

        product_data_quantity_store_1 = (
            f"{quantity_1:,.0f}" if quantity_1.is_integer() else f"{quantity_1:,.3f}"
        ).replace('.', ',')  # Количество на космонавтов

        product_data_quantity_store_2 = (
            f"{quantity_2:,.0f}" if quantity_2.is_integer() else f"{quantity_2:,.3f}"
        ).replace('.', ',')  # Количество на дзержинского

        list_product_data_quantity_store.append(product_data_quantity_store_1)
        list_product_data_quantity_store.append(product_data_quantity_store_2)
    else:
        list_product_data_quantity_store = [0, 0]

    return list_product_data_quantity_store

def format_product_text(product_data: dict,
                        product_information_to_id: dict,
                        product_data_quantity_store_1: int,
                        product_data_quantity_store_2: int
                        ) -> str:
    """
    Форматирует информацию о продукте в виде HTML-текста.

    Эта функция принимает данные о продукте, информацию о продукте по ID,
    а также количества продукта в двух разных магазинах, и возвращает отформатированную
    строку с HTML-тегами для отображения информации о продукте.

    :param product_data: Словарь с данными о продукте, содержащий ключи 'name' и 'description'.
    :type product_data: dict
    :param product_information_to_id: Словарь с информацией о продукте по ID,
    содержащий ключи 'sku' и 'upc'.
    :type product_information_to_id: dict
    :param product_data_quantity_store_1: Количество продукта в первом магазине.
    :type product_data_quantity_store_1: int
    :param product_data_quantity_store_2: Количество продукта во втором магазине.
    :type product_data_quantity_store_2: int
    :return: Отформатированная строка с HTML-тегами, содержащая информацию о продукте.
    :rtype: str
    """
    product_text = (
        f"<strong>{product_data.get('name')}</strong>\n"
        f"<strong>Цена:</strong> {product_information_to_id['sku']} р.\n"
        f"{product_data.get('description')}\n"
        f"<strong>В наличии:</strong>\n"
        f"Гродно, пр. Космонавтов 2Г - {product_data_quantity_store_1} "
        f"{product_information_to_id['upc'].replace('/','')}\n"
        f"Гродно, ул. Дзержинского 118 - {product_data_quantity_store_2} "
        f"{product_information_to_id['upc'].replace('/','')}\n"
        )
    return product_text

async def rate_limit(
    user_id: int,
    limit: int = 10,
    rate_limit_cache: TTLCache = default_rate_limit_cache, 
    cache_lock: asyncio.Lock = default_cache_lock
    ):
    """
    Ограничение частоты запросов для пользователя.
    :param user_id: ID пользователя.
    :param limit: Максимальное количество запросов за период.
    :param rate_limit_cache: Кэш для хранения количества запросов.
    :param cache_lock: Блокировка для синхронизации доступа к кэшу.
    :return: True, если лимит не превышен, иначе False.
    """
    async with cache_lock:
        # Получаем текущее количество запросов для пользователя или 0,
        # если пользователь еще не делал запросов
        current_count = rate_limit_cache.get(user_id, 0)

        # Если лимит превышен
        if current_count >= limit:
            return False

        # Увеличиваем счетчик запросов для пользователя
        rate_limit_cache[user_id] = current_count + 1
        return True
