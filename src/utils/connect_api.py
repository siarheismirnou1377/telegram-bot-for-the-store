"""
Модуль для взаимодействия с API и обработки данных
Этот модуль предоставляет набор асинхронных функций для
взаимодействия с внешним API, обработки данных и логирования.
Он включает функции для получения токена авторизации,
поиска продуктов, получения информации о продуктах и пользователях,
а также для извлечения атрибутов продуктов и количества товара.
"""

import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import re
import requests

import aiohttp
from bs4 import BeautifulSoup
from cachetools import TTLCache

from configs import config


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/connect_api_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('connect_api_logger')
logger.addHandler(file_handler)

cache = TTLCache(maxsize=1, ttl=3600)  # Кеш на 1 элемент с временем жизни 1 час
cache_lock = asyncio.Lock()

async def get_token() -> str:
    """
    Асинхронно получает токен авторизации от сервера.
    Если токен получен ранее, использует кеш.

    :return: Токен авторизации, полученный от сервера.
    """
    async with cache_lock:
        token = cache.get('token')
        if token is not None:
            return token

        try:
            response = requests.post(
                config.URL_API_LOGIN,
                data={
                    'username': config.USERNAME_API,
                    'key': config.KEY_API
                },
                timeout=30
            )
            response_json = response.json()
            if 'token' in response_json:
                logger.info("В функции get_token Токен получен.")
                cache['token'] = response_json['token']
                return response_json['token']
            else:
                logger.error("В функции get_token Токен не получен.")
                raise KeyError("В ответе на запрос авторизации нет поля 'token'")
        except TimeoutError:
            logger.error("В функции get_token запрос превысил таймаут")
            return None

async def connect_search(text_p: str) -> dict:
    """
    Асинхронно выполняет поиск продуктов на сервере.

    :param text_p: Текст для поиска продуктов.
    :return: Словарь с найденными продуктами и их данными.
    """
    logger.info("Выполнение функции connect_search.")
    token =  await get_token()
    if token is None:
        return None
    search_url = config.URL_API_SEARCH
    params = {'search': text_p, 'token': token}
    await asyncio.sleep(0)
    try:
        response = requests.get(search_url, params=params, timeout=30)
        if response.status_code == 200:
            search_data = response.json()
            logger.info("В функции connect_search response.status_code == 200, данные получены")
        else:
            logger.warning(
                "В функции connect_search response.status_code != 200, "
                "данные НЕ получены"
                )
            return None
    except TimeoutError:
        logger.error("В функции connect_search запрос превысил таймаут")
        return None

    current_product = {}
    count = 0
    sentence_pattern = r"[^.!?]*[.!?]"
    await asyncio.sleep(0)
    for value in search_data.values():
        product_id = value.get('product_id')
        name = value.get('name')
        image = value.get('image')
        description = value.get('description')
        product_url = value.get('url')
        if description is not None:
            soup = BeautifulSoup(description, 'html.parser')
            soup = soup.find('div').text
            match = re.match(sentence_pattern, soup)
            if match:
                clean_description = match.group(0)
            else:
                clean_description = "Описания нет."
        else:
            clean_description = "Описания нет."

        current_product[f'product_{count}'] = {
            'product_id': product_id,
            'name': name,
            'image': image,
            'description': clean_description,
            'url': product_url,
        }
        count += 1
    logger.info(
        "В функции connect_search response.status_code == 200, "
        "данные получены и функция успешно завершилась"
        )
    return current_product

async def get_product_info(token: str, product_id: str) -> dict | None:
    """
    Асинхронно получает информацию о продукте с сервера.

    :param token: Токен авторизации для доступа к API.
    :param product_id: Идентификатор продукта.
    :return: Информация о продукте в виде словаря, если запрос выполнен успешно, иначе None.
    """
    logger.info(
        "Выполнение функции get_product_info"
        "c полученными данными %s.", product_id
        )
    url = config.URL_API_PRODUCT
    params = {
        'id': product_id,
        'token': token
    }
    await asyncio.sleep(0)
    async with aiohttp.ClientSession() as session:
        logger.info(
            "Выполнение запроса в функции get_product_info "
            "c полученными данными %s.", product_id
            )
        async with session.get(url, params=params) as response:
            if response.status == 200:
                product_info = await response.json()
                logger.info(
                    "Запрос выполнен успешно %s, получены данные product_info "
                    "в функции get_product_info c полученными данными %s.",
                    response.status, product_id
                    )
                return product_info
            else:
                logger.error(
                    "Запрос не выполнен  в функции get_product_info - %s.",
                    response.status
                    )
                return None

async def connect_product_to_id(product_id: str) -> dict | None:
    """
    Асинхронно получает информацию о продукте по его идентификатору.

    :param product_id: Идентификатор продукта.
    :return: Информация о продукте в виде словаря, если запрос выполнен успешно, иначе None.
    """
    logger.info(
        "Выполнение функции connect_product_to_id"
        "c полученными данными %s.", product_id
        )
    token = await get_token()
    logger.info(
        "Получение токена в функции connect_product_to_id "
        "c полученными данными %s.", product_id
        )
    product_info = await get_product_info(token, product_id)
    logger.info(
        "Получение данных product_info в функции "
        "connect_product_to_id c полученными данными %s.",
        product_id
        )
    if product_info:
        logger.info(
            "Возвращены данные product_info в функции "
            "connect_product_to_id c полученными данными %s.",
            product_id
            )
        return product_info
    else:
        logger.error(
            "Данные не получены - product_info в функции "
            "connect_product_to_id c полученными данными %s.",
            product_id
            )
        return None

async def get_product_attributes(token: str, product_id: str) -> dict | None:
    """
    Асинхронно получает атрибуты продукта с сервера.

    :param token: Токен авторизации для доступа к API.
    :param product_id: Идентификатор продукта.
    :return: Атрибуты продукта в виде словаря, если запрос выполнен успешно, иначе None.
    """
    logger.info(
        "Выполнение функции get_product_attributes "
        "c полученными данными %s.", product_id
        )
    url = config.URL_API_PRODUCT_ATTRIBUTES
    params = {
        'id': product_id,
        'token': token
    }
    await asyncio.sleep(0)
    async with aiohttp.ClientSession() as session:
        logger.info(
            "Выполнение запроса в функции get_product_attributes "
            "c полученными данными %s.", product_id
            )
        async with session.get(url, params=params) as response:
            if response.status == 200:
                product_info = await response.json()
                logger.info(
                    "Запрос выполнен успешно %s, получены данные product_info "
                    "в функции get_product_attributes c полученными данными %s.",
                    response.status, product_id
                    )
                return product_info
            else:
                logger.error(
                    "Запрос не выполнен в функции get_product_attributes %s.",
                    response.status
                    )
                return None

async def connect_product_attributes_to_id(product_id: str) -> dict | None:
    """
    Асинхронно получает атрибуты продукта по его идентификатору.

    :param product_id: Идентификатор продукта.
    :return: Атрибуты продукта в виде словаря, если запрос выполнен успешно, иначе None.
    """
    logger.info(
        "Выполнение функции connect_product_attributes_to_id "
        "c полученными данными %s.", product_id
        )
    token = await get_token()
    logger.info(
        "Получение токена в функции connect_product_attributes_to_id "
        "c полученными данными %s.", product_id
        )
    product_info = await get_product_attributes(token, product_id)
    logger.info(
        "Получение данных product_info в функции "
        "connect_product_attributes_to_id c полученными данными %s.",
        product_id
        )
    if product_info:
        logger.info(
            "Возвращены данные product_info в функции "
            "connect_product_attributes_to_id c полученными данными %s.",
            product_id
            )
        return product_info
    else:
        logger.error(
            "Данные не получены - product_info в функции "
            "connect_product_attributes_to_id c полученными данными %s.",
            product_id
            )
        return None

async def get_user_by_card_code(number: str) -> dict | None:
    """
    Асинхронно получает информацию о пользователе по номеру карты.

    :param number: Номер карты.
    :return: Информация о пользователе в виде словаря, 
    если запрос выполнен успешно и пользователь найден, иначе None.
    """
    logger.info(
        "Выполнение функции get_user_by_card_code c полученными данными %s.",
        number
        )
    url = config.URL_API_CUSTOMER_BY_CARD
    params = {
        'card': number,
        'token': await get_token()
    }
    await asyncio.sleep(0)
    async with aiohttp.ClientSession() as session:
        logger.info(
            "Выполнение запроса в функции get_user_by_card_code "
            "c полученными данными %s.", number
            )
        async with session.get(url, params=params) as response:
            if response.status == 200:
                info = await response.json()
                logger.info(
                    "Запрос выполнен успешно %s, получены данные info "
                    "в функции get_user_by_card_code c полученными данными %s.",
                    response.status, number
                    )
                if list(info.values())[0] == 'Customer not found':
                    logger.error(
                        "По успешному запросу %s в функции get_user_by_card_code "
                        "не получено данных %s", response.status, list(info.values())[0]
                        )
                    return None
                else:
                    logger.info(
                        "По успешному запросу %s в функции get_user_by_card_code "
                        "получены данные info", response.status
                        )
                    return info
            else:
                logger.error(
                    "Ошибка при получении данных в функции get_user_by_card_code - %s",
                    response.status
                    )
                return None

async def get_card_field_two(number: str) -> dict | None:
    """
    Асинхронно получает информацию о пользователе по номеру карты и извлекает определенное поле.

    :param number: Номер карты.
    :return: Значение поля '2' из информации о пользователе,
    если запрос выполнен успешно и пользователь найден, иначе None.
    """
    logger.info(
        "Выполнение функции get_card_field_two c полученными данными %s.",
        number
        )
    url = config.URL_API_CUSTOMER_BY_CARD
    params = {
        'card': number,
        'token': await get_token()
    }
    await asyncio.sleep(0)
    async with aiohttp.ClientSession() as session:
        logger.info(
            "Выполнение запроса в функции get_card_field_two c полученными данными %s.",
            number
            )
        async with session.get(url, params=params) as response:
            if response.status == 200:
                info = await response.json()
                logger.info(
                    "Запрос выполнен успешно %s, получены данные info в функции get_card_field_two "
                    "c полученными данными %s.", response.status, number
                    )
                if list(info.values())[0] == 'Customer not found':
                    logger.error(
                        "По успешному запросу %s в функции get_card_field_two "
                        "не получено данных %s", response.status, list(info.values())[0]
                        )
                    return None
                else:
                    info = info['custom_field']
                    info = json.loads(info)
                    logger.info(
                        "По успешному запросу %s  в функции get_card_field_two получены данные %s",
                        response.status, info['2']
                        )
                    return info['2']
            else:
                logger.error(
                    "Ошибка при получении данныхв функции get_card_field_two - %s",
                    response.status
                    )
                return None

async def get_product_quatity(product_id: str) -> dict | None:
    """
    Асинхронно получает информацию о количестве товара по его идентификатору.

    Эта функция отправляет запрос к API для получения информации
    о количестве товара по указанному идентификатору.
    Она использует токен аутентификации, полученный из функции `get_token`, для выполнения запроса.

    Параметры:
    - product_id (str): Идентификатор товара, для которого нужно получить информацию о количестве.

    Возвращает:
    - dict | None: Словарь с информацией о количестве товара, если запрос был успешным (статус 200).
                  Возвращает None, если запрос завершился с ошибкой.

    Логирование:
    - Информационное сообщение при начале выполнения функции.
    - Информационное сообщение при выполнении запроса.
    - Информационное сообщение, если запрос был успешным.
    - Сообщение об ошибке, если запрос завершился с ошибкой.
    """

    logger.info(
        "Начало выполнения функции get_product_quatity c полученными данными %s.",
        product_id
        )

    url = config.URL_API_QUATITY_BY_PRODUCT_ID
    token = await get_token()
    params = {
        'id': product_id,
        'token': token
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            logger.info(
                "Выполнение запроса в функции get_product_quatity c полученными данными %s.",
                product_id
                )
            if response.status == 200:
                logger.info(
                    "В функции get_product_quatity c полученными данными %s "
                    "response.status == 200", product_id
                    )
                product_info = await response.json()
                return product_info
            else:
                logger.error(
                    "Ошибка при получении данныхв функции get_product_quatity - %s",
                    response.status
                    )
                return None
