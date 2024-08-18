"""
Модуль other_button содержит функции-обработчики для различных команд
и действий, связанных с управлением и взаимодействием с ботом.
Эти функции обеспечивают обработку запросов пользователей,
управление состояниями, отправку сообщений и статистику.
"""
from datetime import datetime
import logging
import json
from logging.handlers import RotatingFileHandler
import os

import aiofiles
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    BufferedInputFile,
)
from aiogram.exceptions import TelegramForbiddenError

from src.utils.collecting_all_statistics import save_all_stats_to_excel
from src.utils.connect_api import get_user_by_card_code
from src.database.process_database_message import (
    get_id_message,
    get_id_message_user_type,
    get_type_message,
    get_unique_posts_per_user_type
)
from src.utils.read_json import read_json_file, read_json_keys_as_ints
from src.telegram_bot.states_class import (
    FormAsk,
    FormProduct,
    FormDiscontCard,
    FormSendingAdv,
    UserStates,
)
from src.utils.check import find_user_id, rate_limit
from src.database.process_database import (
    count_button,
    count_button_not_card,
    count_button_to_card,
    count_search_done_to_code_photo,
    count_search_done_to_code_product,
    count_search_done_to_code_text,
    count_search_done_to_name,
    count_users,
    count_users_agreed,
    count_users_not_card,
    count_users_to_card,
    count_users_unagreed,
    insert_data,
    popular_search_query,
    time_serch_popular,
)
from src.telegram_bot.menus import general_menu
from configs import config

logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/other_button_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('other_button_logger')
logger.addHandler(file_handler)

async def handle_privacy_agreement(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки запроса согласия на
    обработку персональных данных пользователя.

    Функция отправляет пользователю сообщение с информацией о политике
    конфиденциальности и запрос согласия на обработку персональных данных.
    После этого создается клавиатура с кнопками "Согласиться" и "Не соглашаться",
    которая отправляется пользователю.
    Функция также устанавливает состояние `UserStates.privacy_agreement` для
    пользователя и вызывает функцию `insert_data` для сохранения информации о согласии пользователя.

    
    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "В функции handle_privacy_agreement Пользователь id = %s name = %s "
        "получил меню согласия на обработку данных.", 
        message.from_user.id, message.from_user.full_name
        )
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Политика конфиденциальности",
            url='https://example.com/politiks.pdf'
            )
        )

    # Создание клавиатуры с кнопками "Согласиться" и "Не соглашаться"
    kb = [
        [KeyboardButton(text="Согласиться")],
        [KeyboardButton(text="Не соглашаться")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    # Отправка сообщения с запросом согласия и клавиатурой
    await bot.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMfyNmlSYzYXn-yZd4Qxo6Dm2abZ1_OQAC6A0AAsd86FCeNgGtJlhU-jUE"
        )
    await message.answer(
        "Привет меня зовут gemma_bot!\n" 
        "Я 🤖-помощник одного из крупнейших строительных магазинов Гродно.\n"
        "Рад приветствовать вас в этом чате😊\n"
        "Нажимая на кнопку 'Согласиться', вы даёте своё согласие "
        "на обработку персональных данных.\n",
        reply_markup=keyboard
    )
    # Отправка сообщения с информацией о политике конфиденциальности
    # и запрос согласия на обработку персональных данных
    await message.answer(
        "Узнать об обработке персональных данных",
        reply_markup=builder.as_markup()
    )
    await state.set_state(UserStates.privacy_agreement)

async def handle_privacy_agreement_if_not(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки запроса согласия на обработку
    персональных данных пользователя.
    Функция отправляет пользователю сообщение с информацией о политике
    конфиденциальности и запрос согласия на обработку персональных данных.
    После этого создается клавиатура с кнопками "Согласиться" и "Не соглашаться",
    которая отправляется пользователю.
    Функция также устанавливает состояние `UserStates.privacy_agreement` для пользователя
    и вызывает функцию `insert_data` для сохранения информации о согласии пользователя.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "В функции handle_privacy_agreement_if_not Пользователь id = %s name = %s "
        "получил меню согласия на обработку данных.", 
        message.from_user.id, message.from_user.full_name
        )
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Политика конфиденциальности",
            url='https://example.com/politiks.pdf'
            )
        )

    # Создание клавиатуры с кнопками "Согласиться" и "Не соглашаться"
    kb = [
        [KeyboardButton(text="Согласиться")],
        [KeyboardButton(text="Не соглашаться")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    # Отправка сообщения с запросом согласия и клавиатурой
    await message.answer(
        "Нажимая на кнопку 'Согласиться', вы даёте своё согласие "
        "на обработку персональных данных.\n",
        reply_markup=keyboard
    )
    # Отправка сообщения с информацией о политике конфиденциальности
    # и запрос согласия на обработку персональных данных
    await message.answer(
        "Узнать об обработке персональных данных",
        reply_markup=builder.as_markup()
    )
    await bot.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMf9hmlgcBXPluLycSsFrrxmteZZ9cDAACWQsAAoCCcVF1UQ_CXb6s9jUE"
        )
    await state.set_state(UserStates.privacy_agreement)

async def product_search(message: Message, state: FSMContext, bot: Bot) -> None:  # pylint: disable=unused-argument
    """
    Асинхронная функция для обработки запроса на поиск товара. 
    Устанавливает состояние для ожидания ввода названия товара.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """

    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json")
    await insert_data(message.from_user.id, user_type, 2, 0, datetime.now(), None, 1)

    logger.info(
        "В функции product_search Пользователь id = %s name = %s вызвал команду "
        "- Поиск товара",
        message.from_user.id, message.from_user.full_name
        )
    await state.set_state(FormProduct.product)
    await message.answer(
        "Отправьте мне сообщение с наименованием товара, кодом, "
        "штрихкодом или фото штрихкода, который вас интересует."
        )

async def information(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Информация".
    Отправляет пользователю текст с информацией, определенный в конфигурационном файле.

    :param message: Объект сообщения пользователя, содержащий команду "Информация".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции information Пользователь id = %s name = %s вызвал команду "
        "- Информация",
        message.from_user.id, message.from_user.full_name
        )
    text = config.TEXT_INFORMATION_SEARCH
    text_2 = config.TEXT_INFORMATION_CARD
    text_3 = config.TEXT_INFORMATION_RESTART
    await message.answer(text)
    await message.answer(text_2)
    await message.answer(text_3)

    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    await insert_data(message.from_user.id, user_type, 3, 0, datetime.now(), None, 1)

async def visit_the_store(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Посетить магазин".
    Отправляет пользователю ссылку на сайт магазина и контактные телефоны.

    :param message: Объект сообщения пользователя, содержащий команду "Посетить магазин".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции visit_the_store для пользователя id = %s name = %s вызвал команду "
        "- Посетить магазин", 
        message.from_user.id, message.from_user.full_name
        )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="ГЕММА", url=config.URL_SHOP)
    )

    await message.answer(
        'Посетить интернет-магазин',
        reply_markup=builder.as_markup(),
    )

    await message.answer(config.TEXT_VISIT_TO_STORE)
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    await insert_data(message.from_user.id, user_type, 4, 0, datetime.now(), None, 1)

async def add_discont_card(
    message: Message,
    state: FSMContext,
    bot: Bot # pylint: disable=unused-argument
    ) -> None:
    """
    Обработчик команды "Добавить карту".
    Устанавливает состояние FormDiscontCard.number_card для пользователя 
    и предлагает отправить ему фото дисконтной карты или её номер.

    :param message: Объект сообщения пользователя, содержащий команду "Добавить карту".
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    await insert_data(message.from_user.id, user_type, 5, 0, datetime.now(), None, 1)
    logger.info(
        "В функции add_discont_card Пользователь id = %s name = %s вызвал команду "
        "- Добавить карту",
        message.from_user.id, message.from_user.full_name
        )
    await state.set_state(FormDiscontCard.number_card)
    await message.answer("Отправьте мне номер или фото штрихкода вашей дисконтной карты.")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Дисконтные карты", url=config.URL_INFORMATION_DISCONT_CARD)
    )

    await message.answer(
        'Для ознакомления с программой дисконтных карт в магазине ГЕММА, перейдите по ссылке ниже.',
        reply_markup=builder.as_markup(),
    )

async def balance_discont_card(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Баланс д.к. Мастер".
    Отправляет пользователю информацию о балансе дисконтной карты.

    :param message: Объект сообщения пользователя, содержащий команду "Баланс д.к. Мастер".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции balance_discont_card Пользователь id = %s name = %s вызвал команду "
        "- Баланс д.к. Мастер",
        message.from_user.id, message.from_user.full_name
        )
    filename = 'data/user_data_json/user_id_and_number_card_master.json'
    user_id = message.from_user.id
    if not await rate_limit(user_id):
        await message.answer(
            "Вы отправили слишком много запросов. Пожалуйста, подождите немного."
            )
        logger.warning(
            "Пользователь id=%s username=%s, превысил частоту запросов в balance_discont_card",
            message.from_user.id, message.from_user.full_name
            )
        return
    else:
        try:
            data_id = await read_json_file(filename) # id:номеркарты данные
            id_usr = str(message.from_user.id)
            number_card = data_id[id_usr] # Номер карты
            # Данные о пользователе из базы данных
            customer_info = await get_user_by_card_code(number_card)
            custom_fifeld = json.loads(customer_info['custom_field']) # Поле кастом филд
            balance = custom_fifeld['4'] # Накопленная сумма на карте
            if balance is None or balance == '':
                balance = '0'

            await message.answer(f"Ваш баланс составляет: {balance} р.")

            user_type = await find_user_id(
                message.from_user.id,
                "data/user_data_json/user_id_to_discont_card.json"
                )
            await insert_data(message.from_user.id, user_type, 6, 0, datetime.now(), None, 1)
        except Exception as e:  # pylint: disable=broad-exception-caught
            await insert_data(message.from_user.id, user_type, 6, 0, datetime.now(), None, 0)
            logger.error(
                "В функции balance_discont_card Пользователь id = %s name = %s вызвал команду "
                "- Баланс д.к. Мастер и получил ошибку %s",
                message.from_user.id, message.from_user.full_name, e
                )

async def ask_question(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Задать вопрос оператору".
    Даёт возможность задать вопрос оператору.

    :param message: Объект сообщения пользователя, содержащий команду "Задать вопрос оператору".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции ask_question Пользователь id = %s name = %s вызвал команду "
        "- Задать вопрос оператору",
        message.from_user.id, message.from_user.full_name
        )
    try:
        await message.answer("Задайте ваш вопрос.")
        await state.set_state(FormAsk.ask_question)
        user_type = await find_user_id(
            message.from_user.id,
            "data/user_data_json/user_id_to_discont_card.json"
            )
        await insert_data(message.from_user.id, user_type, 37, 0, datetime.now(), None, 1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        await insert_data(message.from_user.id, user_type, 37, 0, datetime.now(), None, 0)
        logger.error(
            "В функции ask_question Пользователь id = %s name = %s вызвал команду "
            "- Задать вопрос оператору и получил ошибку %s",
            message.from_user.id, message.from_user.full_name, e
            )

async def answer_question(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Ответить на вопросы".
    Даёт возможность выбирать вопросы пользователей и отвечать на них.

    :param message: Объект сообщения пользователя, содержащий команду "Ответить на вопросы".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции answer_question Пользователь id = %s name = %s вызвал команду "
        "- Ответить на вопросы",
        message.from_user.id, message.from_user.full_name
        )
    try:
        await message.answer(
            "Выберите сообщение пользователя, на которое хотите ответить, "
            "и нажмите 'Ответить', затем введите текст вашего ответа и отправьте "
            "пользователю ответ."
            )
        await state.set_state(FormAsk.answer_questions)
        user_type = await find_user_id(
            message.from_user.id,
            "data/user_data_json/user_id_to_discont_card.json"
            )
        await insert_data(message.from_user.id, user_type, 38, 0, datetime.now(), None, 1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        await insert_data(message.from_user.id, user_type, 38, 0, datetime.now(), None, 0)
        logger.error(
            "В функции answer_question Пользователь id = %s name = %s вызвал команду "
            "-  Ответить на вопросы и получил ошибку %s",
            message.from_user.id, message.from_user.full_name, e
            )

async def stats_start_bot(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Запуск бота".
    Отправляет пользователю статистику сколько было запусков бота.

    :param message: Объект сообщения пользователя, содержащий команду "Запуск бота".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_start_bot Пользователь id = %s name = %s вызвал команду "
        "- Запуск бота",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        users_agreed = await count_users_agreed()
        user_unagreed = await count_users_unagreed()
        await message.answer(
            f"{users_agreed} - пользователей дали согласие на обработку персональных данных\n"
            f"{user_unagreed} - пользователей не дали согласие на обработку персональных данных\n"
            )
        await insert_data(message.from_user.id, user_type, 7, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 7, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции stats_start_bot Пользователю id = %s name = %s отказано "
            "в достпупе команды - Запуск бота, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def click_button_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Нажатия на кнопки".
    Отправляет пользователю статистику сколько были раз нажаты кнопки бота.

    :param message: Объект сообщения пользователя, содержащий команду "Нажатия на кнопки".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции click_button_stat Пользователь id = %s name = %s вызвал команду "
        "- Нажатия на кнопки",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        button_list = {
            "Поиск товара": 2,
            "Информация": 3,
            "Посетить магазин": 4,
            "Добавить карту": 5,
            "Баланс д.к. Мастер": 6,
            }
        for button_key, button_value in button_list.items():
            click_button = await count_button(button_value)
            await message.answer(f"{click_button} раз - была нажата кнопка {button_key}.")
        await insert_data(message.from_user.id, user_type, 8, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 8, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции click_button_stat  Пользователю id = %s name = %s отказано "
            "в достпупе команды - Нажатия на кнопки, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def activity_not_card_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Без карты".
    Отправляет статистику сколько раз были нажаты кнопки пользователями без карты

    :param message: Объект сообщения пользователя, содержащий команду "Без карты".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции activity_not_card_stat Пользователь id = %s name = %s "
        "вызвал команду - Без карты",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        button_list = {
            "Поиск товара": 2,
            "Информация": 3,
            "Посетить магазин": 4,
            "Добавить карту": 5,
            "Баланс д.к. Мастер": 6,
            }
        for button_key, button_value in button_list.items():
            click_buttnon = await count_button_not_card(button_value)
            await message.answer(
                f"{click_buttnon} раз - была нажата кнопка {button_key},"
                f" пользователями без карты."
                )
        await insert_data(message.from_user.id, user_type, 9, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 9, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции activity_not_card_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - Без карты, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def activity_card_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "С картой".
    Отправляет статистику сколько раз были нажаты кнопки пользователями с картой

    :param message: Объект сообщения пользователя, содержащий команду "С картой".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции activity_card_stat Пользователь id = %s name = %s "
        "вызвал команду - С картой", 
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
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
        all_data = ''
        for tp_key, tp_value in type_users.items():
            for button_key, button_value in button_list.items():
                click_buttnon = await count_button_to_card(button_value, tp_value)
                text = (
                    f"{click_buttnon} раз - была нажата кнопка {button_key},"
                    f"пользователями с кортой {tp_key}.\n"
                    )
                all_data += text
        await message.answer(all_data)
        await insert_data(message.from_user.id, user_type, 10, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 10, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции activity_card_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - С картой, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_posts_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всего публикаций".
    Отправляет статистику по количеству публикаций отправленных пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Всего публикаций".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_posts_stat Пользователь id = %s name = %s "
        "вызвал команду - Всего публикаций",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_posts = str(await get_id_message())

        type_users = {
            "ЦУ0000001": 1,
            "Р00000002": 2,
            "ЦУ0000004": 3,
            "ЦУ0000005": 4,
            "ЦУ0000003": 5
            }

        await message.answer(f"Всего отправлено публикаций - {all_posts}")

        for tp_key, tp_value in type_users.items():
            count = await get_id_message_user_type(tp_value)
            await message.answer(
                f"Пользователям с типом {tp_key},"
                f"отправлено  - {count} публикаций."
                )

        type_posts = {
            "text":1,
            "photo":2,
            "video":3,
            "photo/video/text/":4
            }

        for ty_ps_key, ty_ps_value  in type_posts.items():
            count = await get_type_message(ty_ps_value)
            await message.answer(f"Публикаций типа {ty_ps_key}, отправлено  - {count}.")

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
            await message.answer(
                f"Тип пользователя: {user_type_key if user_type_key else row[0]},\n"
                f"Тип публикации: {post_type_key if post_type_key else row[1]},\n"
                f"Количество уникальных публикаций: {row[2]}"
                )

        await insert_data(message.from_user.id, user_type, 11, 0, datetime.now(), None, 1)
    else:

        await insert_data(message.from_user.id, user_type, 11, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_posts_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - Всего публикаций, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_users_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всего пользователей".
    Отправляет статистику сколько всего пользователей в боте.

    :param message: Объект сообщения пользователя, содержащий команду "Всего пользователей".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_users_stat Пользователь id = %s name = %s "
        "вызвал команду - Всего пользователей",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_user = await count_users()
        await message.answer(f"Всего пользователей - {all_user}.")
        await insert_data(message.from_user.id, user_type, 12, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 12, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_users_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - Всего пользователей, "
            "так как его нет в %s", 
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_users_not_card_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Без программы".
    Отправляет статистику сколько всего пользователей в боте без карты.

    :param message: Объект сообщения пользователя, содержащий команду "Без программы".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_users_not_card_stat Пользователь id = %s name = %s "
        "вызвал команду - Без программы",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_user = await count_users_not_card()
        await message.answer(f"Всего пользователей не имеющих карту клиента - {all_user}.")
        await insert_data(message.from_user.id, user_type, 13, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 13, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_users_not_card_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - Без программы так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_users_card_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "По программе".
    Отправляет статистику сколько всего пользователей в боте с картами.

    :param message: Объект сообщения пользователя, содержащий команду "По программе".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_users_card_stat Пользователь id = %s name = %s "
        "вызвал команду - По программе",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        type_users = {
            "ЦУ0000001": 1,
            "Р00000002": 2,
            "ЦУ0000004": 3,
            "ЦУ0000005": 4,
            "ЦУ0000003": 5
            }
        for tp_u_key, tp_u_value in type_users.items():
            text = await count_users_to_card(tp_u_value)
            await message.answer(f"{text} пользователей с картой {tp_u_key}")
        await insert_data(message.from_user.id, user_type, 14, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 14, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_users_card_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - По программе, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def bot_ban_stat(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "Заблокирован".
    Отправляет статистику по блокировакам бота от пользователей.

    :param message: Объект сообщения пользователя, содержащий команду "Заблокирован".
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции bot_ban_stat Пользователь id = %s name = %s "
        "вызвал команду - Заблокирован",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        count = 0
        user_id = await read_json_keys_as_ints("data/user_data_json/user_id_and_username.json")
        if user_id is not None:
            for i in user_id:
                try:
                    await bot.send_message(chat_id=i, text="Здравстуйте! Мы рады, что вы с нами!")
                except TelegramForbiddenError as bl:
                    logger.info(
                        "В функции bot_ban_stat Пользователь id = %s name = %s "
                        "вызвал команду - Заблокирован и получил ошибку "
                        "TelegramForbiddenError - %s.",
                        message.from_user.id, message.from_user.full_name, bl
                        )
                    count += 1

            await message.answer(f"Бот заблокировало {count} пользователей.")
            logger.error(
                "В функции bot_ban_stat Пользователь id = %s name = %s вызвал команду "
                "- Заблокирован и получил данные по количеству блокировок бота.",
                message.from_user.id, message.from_user.full_name
                )
            await insert_data(message.from_user.id, user_type, 15, 0, datetime.now(), None, 1)
        else:
            logger.info(
                "В функции bot_ban_stat Пользователь id = %s name = %s вызвал команду "
                "- Заблокирован и не получил данные по количеству блокировок бота. "
                "Список id = None",
                message.from_user.id, message.from_user.full_name
                )
            await insert_data(message.from_user.id, user_type, 15, 0, datetime.now(), None, 0)
    else:
        await insert_data(message.from_user.id, user_type, 15, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции bot_ban_stat Пользователю id = %s name = %s "
            "отказано в достпупе команды - Заблокирован, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_requests(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всего запросов".
    Отправляет статистику сколько всего успешно-выполненных запросов.

    :param message: Объект сообщения пользователя, содержащий команду "Всего запросов".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_requests Пользователь id = %s name = %s "
        "вызвал команду - Всего запросов",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_req_name = await count_search_done_to_name()
        all_req_bar_text = await count_search_done_to_code_text()
        all_req_bar_photo = await count_search_done_to_code_photo()
        all_req_code = await count_search_done_to_code_product()
        all_req = all_req_name + all_req_bar_text + all_req_bar_photo + all_req_code
        await message.answer(
            f"Всего успешно выполнено запросов по поиску товаров "
            f"от пользователей - {all_req}"
            )
        await insert_data(message.from_user.id, user_type, 16, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 16, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_requests Пользователю id = %s name = %s отказано в достпупе команды "
            "- Всего запросов, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def popular_requests(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Самые частые".
    Отправляет статистику по самым частым запросам от пользователейв поиске
    'По названию' включая не выполненные.

    :param message: Объект сообщения пользователя, содержащий команду "Самые частые".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции popular_requests Пользователь id = %s name = %s "
        "вызвал команду - Самые частые",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        list_popular_rq = await popular_search_query()
        for i in list_popular_rq:
            await message.answer(i)
        await insert_data(message.from_user.id, user_type, 17, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 17, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции popular_requests Пользователю id = %s name = %s отказано "
            "в достпупе команды - Самые частые, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_requests_to_word(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Кол-во по слову".
    Отправляет статистику сколько всего успешно-выполненных запросов по словам.

    :param message: Объект сообщения пользователя, содержащий команду "Кол-во по слову".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_requests_to_word Пользователь id = %s name = %s вызвал команду "
        "- Кол-во по слову",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_req_name = await count_search_done_to_name()
        await message.answer(
            f"Всего успешно выполнено запросов по поиску товаров от пользователей, "
            f"по словам - {all_req_name}"
            )
        await insert_data(message.from_user.id, user_type, 18, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 18, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_requests_to_word Пользователю id = %s name = %s отказано "
            "в достпупе команды - Кол-во по слову, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_requests_to_barcode(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Кол-во по штрихкоду".
    Отправляет статистику сколько всего успешно-выполненных запросов по штрихкоду, в том числе фото.

    :param message: Объект сообщения пользователя, содержащий команду "Кол-во по штрихкоду".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_requests_to_barcode Пользователь id = %s name = %s "
        "вызвал команду - Кол-во по штрихкоду",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_req_bar_text = await count_search_done_to_code_text()
        all_req_bar_photo = await count_search_done_to_code_photo()
        all_req = all_req_bar_text + all_req_bar_photo
        await message.answer(
            f"Всего успешно выполнено запросов по поиску товаров от пользователей по штрихкоду, "
            f"в том числе и по коду с фото - {all_req}"
            )
        await insert_data(message.from_user.id, user_type, 19, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 19, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_requests_to_barcode Пользователю id = %s name = %s "
            "отказано в достпупе команды - Кол-во по штрихкоду, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def all_requests_to_code(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Кол-во по коду товара".
    Отправляет статистику сколько всего успешно-выполненных запросов по коду товра.

    :param message: Объект сообщения пользователя, содержащий команду "Кол-во по коду товара".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции all_requests_to_code Пользователь id = %s name = %s "
        "вызвал команду - Кол-во по коду товара",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        all_req_bar_text = await count_search_done_to_code_product()
        await message.answer(
            f"Всего успешно выполнено запросов по поиску товаров "
            f"от пользователей по коду товара {all_req_bar_text}"
            )
        await insert_data(message.from_user.id, user_type, 20, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 20, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции all_requests_to_code Пользователю id = %s name = %s отказано в достпупе "
            "команды - Кол-во по коду товара, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def time_search_popular(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Часы активности".
    Отправляет статистику наиболее активного времени пользователей день недели/время суток за месяц.

    :param message: Объект сообщения пользователя, содержащий команду "Часы активности".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции time_search_popular Пользователь id = %s name = %s "
        "вызвал команду - Часы активности",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        list_time_popular = await time_serch_popular()
        for i in list_time_popular:
            await message.answer(i)
        await insert_data(message.from_user.id, user_type, 21, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 21, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции time_search_popular Пользователю id = %s name = %s отказано в достпупе "
            "команды - Часы активности, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def stats_all(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "Вся статистика".
    Отправляет excel файл всей получаемой статистики.

    :param message: Объект сообщения пользователя, содержащий команду "Вся статистика".
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_all Пользователь id = %s name = %s "
        "вызвал команду - Вся статистика",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        count_bl = 0
        user_id = await read_json_keys_as_ints("data/user_data_json/user_id_and_username.json")
        if user_id is not None:
            for i in user_id:
                try:
                    await bot.send_message(chat_id=i, text="Здравстуйте! Мы рады, что вы с нами!")
                except TelegramForbiddenError:
                    count_bl += 1

        path_file_excel = await save_all_stats_to_excel(count_bl)
        # Читаем файл и сохраняем его содержимое в буфер

        async with aiofiles.open(path_file_excel, 'rb') as file:
            file_data = await file.read()

        # Создаем объект BufferedInputFile
        excel_file = BufferedInputFile(file_data, filename=path_file_excel)

        # Теперь вы можете использовать excel_file в качестве аргумента для send_document
        await bot.send_document(chat_id=message.chat.id, document=excel_file)
        os.remove(path_file_excel)
        await insert_data(message.from_user.id, user_type, 22, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 22, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции stats_all Пользователю id = %s name = %s отказано в достпупе команды "
            "- Вся статистика, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_all(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Рассылка всем".
    Устанавливает состояние FormSendingAdv.send_all для пользователя и предлагает
    отправить ему акцию для рассылки всем пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Рассылка всем".
    :param state: Объект состояния пользователя.
    :return: None
    """
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    logger.info(
        "В функции send_advertisements_all Пользователь id = %s name = %s "
        "вызвал команду - Рассылка всем",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_all)
        await message.answer("Отправьте мне акцию для всех пользователей.")
        await insert_data(message.from_user.id, user_type, 23, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 23, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_all Пользователю id = %s name = %s "
            "отказано в достпупе команды - Рассылка всем, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_family(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Семейная".
    Устанавливает состояние FormSendingAdv.send_family для пользователя и предлагает
    отправить ему акцию для рассылки пользователям с картой "Семейная".

    :param message: Объект сообщения пользователя, содержащий команду "Семейная".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции send_advertisements_family Пользователь id = %s name = %s "
        "вызвал команду - Семейная",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id, "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_family)
        await message.answer("Отправьте мне акцию для всех пользователей карты 'Семейная'.")
        await insert_data(message.from_user.id, user_type, 24, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 24, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_family Пользователю id = %s name = %s "
            "отказано в достпупе команды - Семейная, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_master(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Мастер".
    Устанавливает состояние FormSendingAdv.send_master для пользователя и предлагает
    отправить ему акцию для рассылки пользователям с картой "Мастер".

    :param message: Объект сообщения пользователя, содержащий команду "Мастер".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции send_advertisements_master Пользователь id = %s name = %s "
        "вызвал команду - Мастер",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_master)
        await message.answer("Отправьте мне акцию для всех пользователей карты 'Мастер'.")
        await insert_data(message.from_user.id, user_type, 25, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 25, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_master Пользователю id = %s name = %s "
            "отказано в достпупе команды - Мастер, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_home(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Домовёнок".
    Устанавливает состояние FormSendingAdv.send_home для пользователя и предлагает
    отправить ему акцию для рассылки пользователям с картой "Домовёнок".

    :param message: Объект сообщения пользователя, содержащий команду "Домовёнок".
    :param state: Объект состояния пользователя.
    :return: None
    """

    logger.info(
        "В функции send_advertisements_home Пользователь id = %s name = %s "
        "вызвал команду - Домовёнок",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_home)
        await message.answer("Отправьте мне акцию для всех пользователей карты 'Домовёнок'.")
        await insert_data(message.from_user.id, user_type, 26, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 26, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_home Пользователю id = %s name = %s "
            "отказано в достпупе команды - Домовёнок, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_employee(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Сотрудники".
    Устанавливает состояние FormSendingAdv.send_employee для пользователя и предлагает
    отправить ему акцию для рассылки пользователям с картой "Сотрудники".

    :param message: Объект сообщения пользователя, содержащий команду "Сотрудники".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции send_advertisements_employee Пользователь id = %s name = %s "
        "вызвал команду - Сотрудники",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_employee)
        await message.answer("Отправьте мне акцию для всех пользователей карты 'Сотрудники'.")
        await insert_data(message.from_user.id, user_type, 27, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 27, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_employee Пользователю id = %s name = %s "
            "отказано в достпупе команды - Сотрудники, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_vip(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "VIP-8%".
    Устанавливает состояние FormSendingAdv.send_vip для пользователя и предлагает
    отправить ему акцию для рассылки пользователям с картой "VIP-8%".

    :param message: Объект сообщения пользователя, содержащий команду "VIP-8%".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции send_advertisements_vip Пользователь id = %s name = %s "
        "вызвал команду - VIP-8%%%%",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_vip)
        await message.answer("Отправьте мне акцию для всех пользователей карты 'VIP-8%'.")
        await insert_data(message.from_user.id, user_type, 28, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 28, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_vip Пользователю id = %s name = %s "
            "отказано в достпупе команды - VIP-8%%%%, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_advertisements_family_and_home(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Семейная+Домовёнок".
    Устанавливает состояние FormSendingAdv.send_family_and_home для пользователя
    и предлагает отправить ему акцию для рассылки пользователям с картами
    "Семейная" и "Домовёнок".

    :param message: Объект сообщения пользователя, содержащий команду "Семейная+Домовёнок".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции send_advertisements_family_and_home Пользователь id = %s name = %s "
        "вызвал команду - Семейная+Домовёнок",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_family_and_home)
        await message.answer(
            "Отправьте мне акцию для всех пользователей карт 'Семейная' и 'Домовёнок'."
            )
        await insert_data(message.from_user.id, user_type, 29, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 29, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_advertisements_family_and_home  пользователю id = %s name = %s "
            "отказано в достпупе команды - Семейная+Домовёнок, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def send_all_without_master(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всем кроме Мастер".
    Устанавливает состояние FormSendingAdv.send_family_and_home для пользователя
    и предлагает отправить ему акцию для рассылки пользователям
    с картами "Семейная" и "Домовёнок".

    :param message: Объект сообщения пользователя, содержащий команду "Всем кроме Мастер".
    :param state: Объект состояния пользователя.
    :return: None
    """
    logger.info(
        "В функции send_all_without_master  Пользователь id = %s name = %s "
        "вызвал команду - Всем кроме Мастер",
        message.from_user.id, message.from_user.full_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if message.from_user.id in config.USER_ADMIN:
        await state.set_state(FormSendingAdv.send_all_withot_master)
        await message.answer("Отправьте мне акцию для всех пользователей кроме карты 'Мастер'.")
        await insert_data(message.from_user.id, user_type, 36, 0, datetime.now(), None, 1)
    else:
        await insert_data(message.from_user.id, user_type, 36, 0, datetime.now(), None, 0)
        logger.warning(
            "В функции send_all_without_master Пользователю id = %s name = %s "
            "отказано в достпупе команды - Всем кроме Мастер, так как его "
            "нет в %s", message.from_user.id, message.from_user.full_name,
            config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)
