"""
Модуль collecting_all_statistics предназначен для сбора и сохранения статистики работы бота.
Он включает в себя функции для сбора различных метрик, таких как количество пользователей,
нажатия на кнопки, запросы поиска товаров и другие.
Статистика собирается асинхронно и сохраняется в Excel-файл.
"""

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import pandas as pd

from src.database.process_database import (
    count_search_done_to_code_photo,
    count_search_done_to_code_product,
    count_search_done_to_code_text,
    count_search_done_to_name,
    count_users_agreed,
    count_users_to_card,
    count_users_unagreed,
    count_button,
    count_button_not_card,
    count_button_to_card,
    count_users,
    count_users_not_card,
    popular_search_query,
    time_serch_popular,
)
from src.database.process_database_message import (
    get_id_message,
    get_id_message_user_type,
    get_type_message,
    get_unique_posts_per_user_type,
)

logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/collecting_all_statistics_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('collecting_all_statistics_logger')
logger.addHandler(file_handler)


# Функция для форматирования даты и времени
def format_datetime() -> str | None:
    """
    Функция для форматирования текущей даты и времени.
    Функция использует модуль datetime для получения текущей даты и времени, 
    а затем форматирует их в строку в формате '%Y-%m-%d-%H_%M'.

    Возвращает:
    str: Отформатированная строка даты и времени в формате 'ГГГГ-ММ-ДД-ЧЧ_ММ'.

    Пример:
    >>> format_datetime()
    '2022-03-15-14_30'
    """
    try:
        logger.info("Попытка выполнения функции format_datetime")
        date_string = datetime.now()
        formatted_dt = date_string.strftime('%Y-%m-%d-%H_%M')
        logger.info("Функция format_datetime выполнилась")
        return formatted_dt
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error(
            "Произошла ошибка в функции format_datetime при"
           "форматировании даты и времени: %s", e
           )
        return None

# Запуск бота
async def collecting_stats_start_bot() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о пользователях, которые дали
    согласие на обработку персональных данных и запустили бота.
    Функция асинхронно вызывает три асинхронные функции:
    1. `count_users_agreed()` - для подсчета количества пользователей,
    которые дали согласие на обработку персональных данных.
    2. `count_users_unagreed()` - для подсчета количества пользователей,
    которые не дали согласие на обработку персональных данных.
    Функция возвращает список словарей, где каждый словарь
    содержит наименование статистики и ее значение.

    Возвращает:
    list: Список словарей со статистикой о пользователях,
    которые дали согласие на обработку персональных данных и запустили бота.
    """
    try:
        logger.info("Попытка выполнения функции collecting_stats_start_bot")
        users_agreed = await count_users_agreed()
        users_unagreed = await count_users_unagreed()
        logger.info("Функция collecting_stats_start_bot выполнилась")
        data = [
            {
                'Наименование': 
                    'Пользователей дали согласие на обработку '
                    'персональных данных и запустили бота',
                'Значение': users_agreed
                },
            {
                'Наименование': 
                    'Была нажата кнопка "Не соглашаться" на обработку '
                    'персональных данных',
                'Значение': users_unagreed
                },
        ]
        return data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_stats_start_bot: %s", e)
        return None

# Нажатия на кнопки
async def collecting_stats_click_button_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о нажатиях на кнопки.
    Функция асинхронно подсчитывает количество нажатий на каждую кнопку
    из списка `button_list`, используя асинхронную функцию `count_button(button)`.
    Функция возвращает список словарей, где каждый словарь содержит
    наименование кнопки и количество ее нажатий.

    Возвращает:
    list: Список словарей со статистикой о нажатиях на кнопки.
    """
    try:
        logger.info("Попытка выполнения функции collecting_stats_click_button_stat")
        button_list = {
            "Поиск товара": 2,
            "Информация": 3,
            "Посетить магазин": 4,
            "Добавить карту": 5,
            "Баланс д.к. Мастер": 6,
            }
        all_data = []
        for button_key, button_value in button_list.items():
            click_button = await count_button(button_value)
            all_data.append({
                'Наименование': f'Кнопка "{button_key}" была нажата (раз)',
                'Значение': click_button
            })
        logger.info("Функция collecting_stats_click_button_stat выполнилась")
        print(all_data)
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_stats_click_button_stat: %s", e)
        return None

# "Без карты"
async def collecting_activity_not_card_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о неактивных кнопках.
    Функция асинхронно проверяет, какие кнопки из списка `button_list`
    не были нажаты, используя асинхронную функцию `count_button_not_card(button)`.
    Функция возвращает список словарей, где каждый словарь содержит наименование 
    кнопки и информацию о том, была ли она нажата.

    Возвращает:
    list: Список словарей со статистикой о неактивных кнопках.
    """
    try:
        logger.info("Попытка выполнения функции collecting_activity_not_card_stat")
        button_list = {
            "Поиск товара": 2,
            "Информация": 3,
            "Посетить магазин": 4,
            "Добавить карту": 5,
            "Баланс д.к. Мастер": 6,
            }
        all_data = []
        for button_key, button_value in button_list.items():
            click_buttnon = await count_button_not_card(button_value)
            all_data.append({
                'Наименование': f'Кнопка "{button_key}" была нажата (раз)',
                'Значение': click_buttnon
            })
        logger.info("Функция collecting_activity_not_card_stat выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_activity_not_card_stat: %s", e)
        return None

# С картой
async def collecting_activity_card_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о кнопках, нажатых пользователями
    с определенными типами карт. Функция асинхронно подсчитывает количество
    нажатий на каждую кнопку из списка `button_list` для каждого типа пользователя
    из списка `type_users`, используя асинхронную функцию `count_button_to_card(button, tp)`.
    Функция возвращает список словарей, где каждый словарь содержит наименование кнопки,
    тип пользователя и количество нажатий этой кнопки этим пользователем.

    Возвращает:
    list: Список словарей со статистикой о кнопках, нажатых пользователями
    с определенными типами карт.
    """
    try:
        logger.info("Попытка выполнения функции collecting_activity_card_stat")
        button_list = {
            "Поиск товара": 2,
            "Информация": 3,
            "Посетить магазин": 4,
            "Добавить карту": 5,
            "Баланс д.к. Мастер": 6,
            }
        type_users = {
            "ЦУ0000001": 1,
            "Р00000002": 2,
            "ЦУ0000004": 3,
            "ЦУ0000005": 4,
            "ЦУ0000003": 5
            }
        all_data = []
        for tp_key, tp_value in type_users.items():
            for button_key, button_value in button_list.items():
                click_buttnon = await count_button_to_card(button_value, tp_value)
                all_data.append({
                    'Наименование': f'Кнопка "{button_key}" была нажата (раз), '
                    f'пользователем с картой {tp_key}',
                    'Значение': click_buttnon
                })
        logger.info("Функция collecting_activity_card_stat выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_activity_card_stat: %s", e)
        return None

# Всего публикаций
async def collecting_all_posts_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о всех отправленных постах.
    Функция асинхронно собирает различную статистику о постах:
    1. Общее количество отправленных публикаций.
    2. Количество отправленных публикаций для каждого типа пользователей.
    3. Количество отправленных публикаций каждого типа.
    4. Количество уникальных публикаций для каждого типа пользователей и типа публикаций.
    Функция возвращает список словарей, где каждый словарь содержит
    наименование статистики и ее значение.

    Возвращает:
    list: Список словарей со статистикой о всех отправленных постах.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_posts_stat")
        all_posts = str(await get_id_message())
        all_data = []
        type_users = {
            "ЦУ0000001": 1,
            "Р00000002": 2,
            "ЦУ0000004": 3,
            "ЦУ0000005": 4,
            "ЦУ0000003": 5
            }
        all_data.append({
                'Наименование': 'Всего отправлено публикаций',
                'Значение': int(all_posts)
            })

        for tp_key, tp_value in type_users.items():
            count = await get_id_message_user_type(tp_value)
            all_data.append({
                'Наименование': f'Пользователям с типом {tp_key}, отправлено публикаций (кол-во)',
                'Значение': count
            })

        type_posts = {"text":1, "photo":2, "video":3, "photo/video/text/":4}

        for ty_ps_key, ty_ps_value  in type_posts.items():
            count = await get_type_message(ty_ps_value)
            all_data.append({
                'Наименование': f'Публикаций типа {ty_ps_key}, отправлено',
                'Значение': count
            })

        unique_posts = await get_unique_posts_per_user_type()
        for row in unique_posts:
            # Ищем ключ в type_users, который соответствует значению row[0]
            user_type_key = next(
                (key for key, value in type_users.items() if value == row[0]),
                None
                )
            # Ищем ключ в type_posts, который соответствует значению row[1]
            post_type_key = next(
                (key for key, value in type_posts.items() if value == row[1]),
                None
                )

            all_data.append({
                'Наименование': f'Тип пользователя: {user_type_key if user_type_key else row[0]}, '
                f'Тип публикации: {post_type_key if post_type_key else row[1]}, '
                f'Количество уникальных публикаций',
                'Значение': row[2]
            })
        logger.info("Функция collecting_all_posts_stat выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_posts_stat: %s", e)
        return None

# "Всего пользователей"
async def collecting_all_users_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о всех пользователях.
    Функция асинхронно подсчитывает общее количество пользователей,
    используя асинхронную функцию `count_users()`.
    Функция возвращает список словарей, где каждый словарь содержит
    наименование статистики и общее количество пользователей.

    Возвращает:
    list: Список словарей со статистикой о всех пользователях.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_users_stat")
        all_data = []
        all_user = await count_users()
        all_data.append({
                'Наименование': 'Всего пользователей',
                'Значение': all_user
            })
        logger.info("Функция collecting_all_users_stat выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_users_stat: %s", e)
        return None

# "Без программы"
async def collecting_all_users_not_card_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о пользователях, не имеющих карту клиента.
    Функция асинхронно подсчитывает количество пользователей, не имеющих карту клиента,
    используя асинхронную функцию `count_users_not_card()`.
    Функция возвращает список словарей, где каждый словарь содержит наименование
    статистики и количество пользователей, не имеющих карту клиента.

    Возвращает:
    list: Список словарей со статистикой о пользователях, не имеющих карту клиента.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_users_not_card_stat")
        all_data = []
        all_user = await count_users_not_card()
        all_data.append({
                'Наименование': 'Всего пользователей не имеющих карту клиента',
                'Значение': all_user
            })
        logger.info("Функция collecting_all_users_not_card_stat выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_users_not_card_stat: %s", e)
        return None

# "По программе"
async def collecting_all_users_card_stat() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о пользователях с определенными типами карт.
    Функция асинхронно подсчитывает количество пользователей для каждого типа карт
    из списка `type_users`, используя асинхронную функцию `count_users_to_card(card)`.
    Функция возвращает список словарей, где каждый словарь содержит наименование
    типа карты и количество пользователей с этой картой.

    Возвращает:
    list: Список словарей со статистикой о пользователях с определенными типами карт.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_users_card_stat")
        all_data = []
        type_users = {
            "ЦУ0000001": 1,
            "Р00000002": 2,
            "ЦУ0000004": 3,
            "ЦУ0000005": 4,
            "ЦУ0000003": 5
            }
        for tp_u_key, tp_u_value in type_users.items():
            text = await count_users_to_card(tp_u_value)
            all_data.append({
                'Наименование': f'Пользователей с картой {tp_u_key}',
                'Значение': text
            })
        logger.info("Функция collecting_all_users_card_stat выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_users_card_stat: %s", e)
        return None

# "Всего запросов"
async def collecting_all_requests() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о всех успешно выполненных
    запросах по поиску товаров от пользователей.
    Функция асинхронно подсчитывает количество успешно выполненных запросов:
    1. По имени товара (`count_search_done_to_name()`).
    2. По штрих-коду товара в виде текста (`count_search_done_to_code_text()`).
    3. По штрих-коду товара в виде фотографии (`count_search_done_to_code_photo()`).
    Функция возвращает список словарей, где каждый словарь содержит наименование
    статистики и общее количество успешно выполненных запросов.

    Возвращает:
    list: Список словарей со статистикой о всех успешно выполненных запросах
    по поиску товаров от пользователей.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_requests")
        all_data = []
        all_req_name = await count_search_done_to_name()
        all_req_bar_text = await count_search_done_to_code_text()
        all_req_bar_photo = await count_search_done_to_code_photo()
        all_req = all_req_name + all_req_bar_text + all_req_bar_photo
        all_data.append({
            'Наименование': 'Всего успешно выполнено запросов по поиску товаров от пользователей',
            'Значение': all_req
        })
        logger.info("Функция collecting_all_requests выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_requests: %s", e)
        return None

# "Самые частые 5 "
async def collecting_popular_requests() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о самых популярных запросах пользователей.
    Функция асинхронно получает список самых популярных запросов,
    используя асинхронную функцию `popular_search_query()`.
    Функция возвращает список словарей, где каждый словарь содержит порядковый
    номер популярности и самый популярный запрос.

    Возвращает:
    list: Список словарей со статистикой о самых популярных запросах пользователей.
    """
    try:
        logger.info("Попытка выполнения функции collecting_popular_requests")
        all_data = []
        count = 1
        list_popular_rq = await popular_search_query()
        for polpular_rq in list_popular_rq:
            all_data.append({
                'Наименование': f'{count}-й самый частый запрос',
                'Значение': polpular_rq 
            })
            count += 1
        logger.info("Функция collecting_popular_requests выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_popular_requests: %s", e)
        return None

# "Кол-во по слову"
async def collecting_requests_to_word() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о успешно выполненных запросах
    по поиску товаров от пользователей по словесному запросу.
    Функция асинхронно подсчитывает количество успешно выполненных запросов
    по словесному запросу, используя асинхронную функцию `count_search_done_to_name()`.
    Функция возвращает список словарей, где каждый словарь содержит наименование
    статистики и общее количество успешно выполненных запросов по словесному запросу.
    Возвращает:
    list: Список словарей со статистикой о успешно выполненных запросах по поиску
    товаров от пользователей по словесному запросу.
    """
    try:
        logger.info("Попытка выполнения функции collecting_requests_to_word")
        all_data = []
        all_req_name = await count_search_done_to_name()
        all_data.append({
                'Наименование': 
                    'Всего успешно выполнено запросов по поиску '
                    'товаров от пользователей, по словесному запросу',
                'Значение': all_req_name
            })
        logger.info("Функция collecting_requests_to_word выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_requests_to_word: %s", e)
        return None

# "Кол-во по коду товара"
async def collecting_all_requests_to_code() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о успешно выполненных запросах
    по поиску товаров от пользователей по коду товра.
    Функция асинхронно подсчитывает количество успешно выполненных запросов
    по коду товра товара.
    Возвращает:
    list: Список словарей со статистикой о успешно выполненных запросах по
    поиску товаров от пользователей по коду товара.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_requests_to_code")
        all_data = []
        all_req_code = await count_search_done_to_code_product()
        all_data.append({
                'Наименование': 
                    'Всего успешно выполнено запросов по поиску '
                    'товаров от пользователей по коду товра',
                'Значение': all_req_code
            })
        logger.info("Функция collecting_all_requests_to_code выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_requests_to_code: %s", e)
        return None

# "Кол-во по штрихкоду"
async def collecting_all_requests_to_barcode() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о успешно выполненных запросах
    по поиску товаров от пользователей по штрихкоду, в том числе и по штрихкоду с фото.
    Функция асинхронно подсчитывает количество успешно выполненных запросов:
    1. По штрих-коду товара в виде текста (`count_search_done_to_code_text()`).
    2. По штрих-коду товара в виде фотографии (`count_search_done_to_code_photo()`).
    Функция возвращает список словарей, где каждый словарь содержит наименование
    статистики и общее количество успешно выполненных запросов по штрихкоду,
    в том числе и по штрихкоду с фото.

    Возвращает:
    list: Список словарей со статистикой о успешно выполненных запросах
    по поиску товаров от пользователей по штрихкоду, в том числе и по штрихкоду с фото.
    """
    try:
        logger.info("Попытка выполнения функции collecting_all_requests_to_barcode")
        all_data = []
        all_req_bar_text = await count_search_done_to_code_text()
        all_req_bar_photo = await count_search_done_to_code_photo()
        all_req = all_req_bar_text + all_req_bar_photo
        all_data.append({
                'Наименование': 
                    'Всего успешно выполнено запросов по поиску товаров '
                    'от пользователей по штрихкоду, в том числе и по штрихкоду с фото',
                'Значение': all_req
            })
        logger.info("Функция collecting_all_requests_to_barcode выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_all_requests_to_barcode: %s", e)
        return None

# "Часы активности"
async def collecting_time_search_popular() -> list[dict] | None:
    """
    Асинхронная функция для сбора статистики о наиболее
    популярном времени поисковых запросов. Функция асинхронно
    получает список наиболее популярных времен поисковых запросов,
    используя асинхронную функцию `time_serch_popular()`.
    Функция возвращает список словарей, где каждый словарь
    содержит наименование статистики и наиболее популярное
    время поисковых запросов.

    Возвращает:
    list: Список словарей со статистикой о наиболее популярном времени поисковых запросов.
    """
    try:
        logger.info("Попытка выполнения функции collecting_time_search_popular")
        all_data = []
        list_time_popular = await time_serch_popular()
        for time_popular in list_time_popular:
            all_data.append({
                    'Наименование': 'Наиболее популярное время поисковых запросов',
                    'Значение': time_popular
                })
        logger.info("Функция collecting_time_search_popular выполнилась")
        return all_data
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции collecting_time_search_popular: %s", e)
        return None

# Функция для сохранения всех данных в один файл Excel
async def save_all_stats_to_excel(count: int) -> str | None:
    """
    Асинхронная функция для сохранения статистики в Excel-файл.
    
    Функция собирает статистику из различных асинхронных функций,
    которые собирают информацию о статистике бота, такую как количество
    стартов бота, количество нажатий на кнопки, активность пользователей
    без карты, активность пользователей с картой, отправленные публикации,
    общее количество пользователей, количество пользователей без карты,
    количество пользователей с картой, общее количество запросов,
    популярные запросы, запросы по словесному запросу, запросы по коду,
    популярное время поиска и количество заблокированных пользователей.
    Функция форматирует дату и время, объединяет все данные в один DataFrame,
    сохраняет его в Excel-файл и возвращает путь к сохраненному файлу.

    Параметры:
    count (int): Количество пользователей, заблокировавших бота.

    Возвращает:
    str: Путь к сохраненному Excel-файлу.
    """
    try:
        logger.info("Попытка выполнения функции save_all_stats_to_excel")
        formatted_dt = format_datetime()
        start_bot_data = await collecting_stats_start_bot()
        click_button_data = await collecting_stats_click_button_stat()
        click_button_not_card_data = await collecting_activity_not_card_stat()
        click_button_card_data = await collecting_activity_card_stat()
        send_public = await collecting_all_posts_stat()
        count_all_users = await collecting_all_users_stat()
        count_all_users_not_card = await collecting_all_users_not_card_stat()
        count_all_users_card = await collecting_all_users_card_stat()
        count_all_requests = await collecting_all_requests()
        popular_requests = await collecting_popular_requests()
        requests_to_word = await collecting_requests_to_word()
        requests_to_code = await collecting_all_requests_to_code()
        requests_to_barcode = await collecting_all_requests_to_barcode()
        time_search_popular = await collecting_time_search_popular()
        count_blocked = [{
                    'Наименование': 'Количетсво пользователей, заблокировавших бота',
                    'Значение': count
                }]
        # Объединяем данные
        data_variables = [
            start_bot_data,
            click_button_data,
            click_button_not_card_data,
            click_button_card_data,
            send_public,
            count_all_users,
            count_all_users_not_card,
            count_all_users_card,
            count_all_requests,
            popular_requests,
            requests_to_word,
            requests_to_code,
            requests_to_barcode,
            time_search_popular,
            count_blocked
        ]

        all_data = []
        for data in data_variables:
            all_data.extend(data)

        # Создаем DataFrame из всех данных
        df = pd.DataFrame(all_data)
        file_path = f'all_stats_{formatted_dt}.xlsx'
        # Сохраняем DataFrame в файл Excel
        df.to_excel(file_path, index=False)
        logger.info("Функция save_all_stats_to_excel выполнилась")
        return file_path
    except (
        ValueError,
        TypeError,
        IndexError,
        KeyError,
        AttributeError,
        AssertionError,
        TimeoutError
        ) as e:
        logger.error("Произошла ошибка в функции save_all_stats_to_excel: %s", e)
        return None
