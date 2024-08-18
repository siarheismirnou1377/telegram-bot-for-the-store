"""
Этот модуль предназначен для обработки различных типов сообщений 
и действий, инициируемых пользователями в Telegram боте, для поиска 
товара,добавления дискотных карт, рассылки сообщений, 
показа статистики и др.
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import os
import json
import re
from datetime import datetime

from aiohttp import TooManyRedirects
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from configs import config
from src.utils.barcod_ import generate_barcode, return_barcode
from src.utils.check import (
    add_data_to_json,
    censor_swear_words,
    check_image_exists,
    find_matching_key,
    format_product_attributes,
    find_user_id,
    format_product_text,
    quatity_discount,
    rate_limit,
)
from src.utils.connect_api import (
    connect_product_attributes_to_id,
    connect_product_to_id,
    connect_search,
    get_card_field_two,
    get_product_quatity,
    get_user_by_card_code,
)
from src.utils.read_json import read_json_file, update_json_file
from src.database.process_database import insert_data
from src.database.process_database_message import insert_message_data
from src.telegram_bot.menus import general_menu, start_bot
from src.telegram_bot.other_button import handle_privacy_agreement_if_not
from src.telegram_bot.states_class import FormAsk




logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/process_bot_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('process_bot_logger')
logger.addHandler(file_handler)


async def process_privacy_agreement(message: Message, state: FSMContext, bot:Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    обновления состояния и запуска бота, через функцию start_bot.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "В функции process_privacy_agreement Пользователь "
        "id = %s name = %s прислал сообщение - %s",
        message.from_user.id, (message.from_user.full_name), message.text
        )
    privacy_state = message.text
    await state.update_data(privacy_agreement=privacy_state)
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if privacy_state == "Согласиться":
        logger.info(
            "В функции process_privacy_agreement Пользователь "
            "id = %s name = %s дал согласие на обработку данных",
            message.from_user.id, (message.from_user.full_name)
            )
        await state.clear()
        await start_bot(message)
        await insert_data(message.from_user.id, user_type, 0, 1, datetime.now(), message.text, 1)
    else:
        logger.info(
            "В функции process_privacy_agreement  Пользователь "
            "id = %s name = %s не дал согласие на обработку данных %s",
            message.from_user.id, (message.from_user.full_name), message.text
            )
        await insert_data(message.from_user.id, user_type, 1, 1, datetime.now(), message.text, 1)
        await message.answer(
            "К сожалению, я не могу начать работу, пока вы не нажмёте 'Согласиться'."
            )
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMf9pmlgghC9ZP_LQ2LqPFzo3TiJeEWQACMAwAAjbo6VCo9f_fxCJ3GTUE"
            )
        await handle_privacy_agreement_if_not(message, state, bot)

async def process_search_general(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки общего поискового запроса пользователя.

    Функция определяет тип сообщения (текст или фото) и вызывает
    соответствующую функцию для обработки:
    Если сообщение содержит фото, вызывается функция `process_barcode` для обработки штрихкода.
    Если сообщение содержит текст, функция анализирует текст и вызывает соответствующую функцию:
    Если текст является числом и не соответствует формату штрихкода
    (8 или 13 символов), вызывается функция `process_code_search` для поиска по коду товара.
    Если текст не является числом, вызывается функция `process_search`
    для поиска по словесному описанию.
    Если текст является числом и соответствует формату штрихкода, вызывается функция
    `process_input_barcode` для обработки штрихкода.
    Если сообщение не соответствует ни одному из вышеперечисленных типов, 
    пользователю отправляется сообщение с просьбой отправить корректные данные для поиска.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Выполнение функциии process_search_general для пользователя "
        "id = %s name = %s",
        message.from_user.id, (message.from_user.full_name)
        )
    user_id = message.from_user.id
    if not await rate_limit(user_id):
        await message.answer("Вы отправили слишком много запросов. Пожалуйста, подождите немного.")
        logger.warning(
            "Пользователь id=%s username=%s, превысил частоту запросов в process_search_general",
            message.from_user.id, message.from_user.full_name
            )
        return
    else:
        if message.photo:
            await process_barcode(message, state, bot)
            logger.info(
                "Выполнение функциии process_search_general для пользователя "
                "id = %s name = %s по фото",
                message.from_user.id, (message.from_user.full_name)
                )
        elif message.text:
            logger.info(
                "Выполнение функциии process_search_general для пользователя "
                "id = %s name = %s по тексту",
                message.from_user.id, (message.from_user.full_name)
                )
            len_message = len(message.text)
            if (
                message.text is not None and  message.text.isdigit()
                and len_message != 8 and len_message != 13
                ):
                logger.info(
                    "Выполнение функциии process_search_general для пользователя "
                    "id = %s name = %s по коду товара",
                    message.from_user.id, (message.from_user.full_name)
                    )
                await process_code_search(message, state, bot)
            elif not message.text.isdigit() and message.text is not None:
                logger.info(
                    "Выполнение функциии process_search_general для пользователя "
                    "id = %s name = %s по коду словесному описанию",
                    message.from_user.id, (message.from_user.full_name)
                    )
                await process_search(message, state, bot)
            elif ((message.text is not None) and  message.text.isdigit()
                and (len_message == 8 or len_message == 13)):
                logger.info(
                    "Выполнение функциии process_search_general для пользователя "
                    "id = %s name = %s по номеру штрихкода",
                    message.from_user.id, (message.from_user.full_name)
                    )
                await process_input_barcode(message, state, bot)
            else:
                logger.info(
                    "Выполнение функциии process_search_general для пользователя "
                    "id = %s name = %s -  ничего не найдено",
                    message.from_user.id, (message.from_user.full_name)
                    )
                await message.answer(
                    "К сожалению, по вашему запросу ничего не найдено. "
                    "Пожалуйста, попробуйте еще раз отправить данные для поиска."
                    )
                await bot.send_sticker(
                    chat_id=message.chat.id,
                    sticker=(
                        "CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgj"
                        "YWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA")
                    )
        else:
            # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
            await message.answer(
                "Пожалуйста, отправьте мне наименование, код, "
                "штрихкод или фотографию штрихкода товара."
                )
            return
        await asyncio.sleep(0.1)

async def process_search(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    обновления состояния и выполнения поиска продукта.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    product_name = message.text
    await state.update_data(product=product_name)
    logger.info(
        "В функции process_search Пользователь id = %s name = %s "
        "прислал сообщение - %s",
        message.from_user.id, (message.from_user.full_name), product_name
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    await message.answer(f"Идет поиск по запросу 🔍 '{product_name}'.")
    await bot.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMfyVmlSY5oE0km2nNvj5ke33RL_1t_gAC6wwAAg2m6VDUyl6qMEbwuzUE"
        )
    if not product_name.isdigit():
        try:
            logger.info(
                "В функции process_search Попытка поиска товара "
                "по сообщению пользователя id = %s name = %s - запрос = %s",
                message.from_user.id, (message.from_user.full_name), product_name
                )
            product_information = await connect_search(product_name)

            all_product_text = ""
            builder_all = InlineKeyboardBuilder()

            if len(product_information) == 1:
                product_data_1 = product_information.get('product_0')

                # Цена
                product_information_to_id_1 = await connect_product_to_id(
                    product_data_1.get('product_id')
                    )
                img_url = f'{config.IMAGE_URL}{product_information_to_id_1['image']}'

                await bot.send_sticker(
                    chat_id=message.chat.id,
                    sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0"
                    "Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                    )

                if await check_image_exists(img_url):
                    await message.answer(img_url) # картинка
                else:
                    await message.answer('Изображение не найдено.')
                # Количество по магазинам
                product_id_1 = product_data_1.get('product_id')
                product_data_1_quantity = await get_product_quatity(product_id_1)
                product_data_1_quantity = quatity_discount(product_data_1_quantity)
                product_data_1_quantity_store_1 =  product_data_1_quantity[0]
                product_data_1_quantity_store_2 = product_data_1_quantity[1]

                product_text_1 = format_product_text(
                    product_data_1,
                    product_information_to_id_1,
                    product_data_1_quantity_store_1,
                    product_data_1_quantity_store_2
                    )

                all_product_text = product_text_1

                await message.answer("Возможно вы искали эти товары:")
                builder_all.row(
                    InlineKeyboardButton(
                        text=product_data_1.get('name'),
                        url=product_data_1.get('url')
                        )
                    )
                builder_all.row(
                    InlineKeyboardButton(
                        text="Искать на сайте",
                        url=f"https://example.com/search={product_name}"
                        )
                    )

                await insert_data(
                    message.from_user.id,
                    user_type, 30, 1, datetime.now(),
                    message.text, 1
                    )
                await message.answer(all_product_text, reply_markup=builder_all.as_markup())
                logger.info(
                    "В функции process_search Пользователю id = %s name = %s "
                    "отправлено сообщение - all_product_text количество товаров = 1",
                    message.from_user.id, (message.from_user.full_name)
                    )
            elif len(product_information) == 2:
                for i in range(2):
                    product_data = product_information.get(f'product_{i}')
                    # Цена
                    product_information_to_id = await connect_product_to_id(
                        product_data.get('product_id')
                        )
                    # Количество по магазинам
                    product_id = product_data.get('product_id')
                    product_data_quantity = await get_product_quatity(product_id)
                    product_data_quantity = quatity_discount(product_data_quantity)
                    product_data_quantity_store_1 = product_data_quantity[0]
                    product_data_quantity_store_2 = product_data_quantity[1]

                    product_text = format_product_text(
                        product_data,
                        product_information_to_id,
                        product_data_quantity_store_1,
                        product_data_quantity_store_2
                        )
                    all_product_text += f"{product_text}\n"

                    builder_all.row(
                        InlineKeyboardButton(
                            text=product_data.get('name'),
                            url=product_data.get('url')
                            )
                        )

                await bot.send_sticker(
                    chat_id=message.chat.id,
                    sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0L"
                    "n2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                    )
                await message.answer("Возможно вы искали эти товары:")
                builder_all.row(
                    InlineKeyboardButton(
                        text="Искать на сайте",
                        url=f"https://example.com/search={product_name}"
                        )
                    )
                await message.answer(all_product_text, reply_markup=builder_all.as_markup())

                await insert_data(
                    message.from_user.id, user_type, 30, 1,
                    datetime.now(), message.text, 1
                    )

                logger.info(
                    "В функции process_search Пользователю id = %s name = %s "
                    "отправлено сообщение - all_product_text  количество товаров = 2",
                    message.from_user.id, (message.from_user.full_name)
                    )
            else:
                for i in range(1, 4):  # Цикл от 1 до 3
                    product_data = product_information.get(f'product_{i}')
                    # Цена
                    product_information_to_id = await connect_product_to_id(
                        product_data.get('product_id')
                        )
                    # Количество по магазинам
                    product_id = product_data.get('product_id')
                    product_data_quantity = await get_product_quatity(product_id)
                    product_data_quantity = quatity_discount(product_data_quantity)
                    product_data_quantity_store_1 = product_data_quantity[0]
                    product_data_quantity_store_2 = product_data_quantity[1]

                    product_text = format_product_text(
                        product_data,
                        product_information_to_id,
                        product_data_quantity_store_1,
                        product_data_quantity_store_2
                        )
                    all_product_text += f"{product_text}\n"

                    builder_all.row(
                        InlineKeyboardButton(
                            text=product_data.get('name'),
                            url=product_data.get('url')
                            )
                        )

                await bot.send_sticker(
                    chat_id=message.chat.id,
                    sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj"
                    "0Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                    )
                await message.answer("Возможно вы искали эти товары:")
                builder_all.row(
                    InlineKeyboardButton(
                        text="Искать на сайте",
                        url=f"https://example.com/search={product_name}"
                        )
                    )
                await message.answer(all_product_text, reply_markup=builder_all.as_markup())
                logger.info(
                    "В функции process_search Пользователю id = %s name = %s "
                    "отправлено сообщение - all_product_text  количество товаров = 3",
                    message.from_user.id, (message.from_user.full_name)
                    )
                await insert_data(
                    message.from_user.id, user_type, 30, 1,
                    datetime.now(), message.text, 1
                    )
        except (TooManyRedirects, AttributeError, TypeError) as e:
            logger.error(
                "В функции process_search Пользователь id = %s name = %s "
                "по запросу = %s получил ошибку: - %s",
                message.from_user.id, (message.from_user.full_name), product_name, e
                )
            await message.answer(
                "К сожалению, по вашему запросу ничего не найдено. "
                " Пожалуйста, попробуйте ввести другое название товара."
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                )
            await insert_data(
                message.from_user.id, user_type,
                30, 1, datetime.now(), message.text, 0
                )
    else:
        logger.error(
            "В функции process_search Пользователь id = %s name = %s "
            "по запросу = %s ввёл цифры.", 
            message.from_user.id, (message.from_user.full_name), product_name
            )
        await message.answer(
            "К сожалению, по вашему запросу ничего не найдено. "
            " Пожалуйста, попробуйте ввести другое название товара."
            )
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
            )
        await insert_data(message.from_user.id, user_type, 30, 1, datetime.now(), message.text, 0)

async def process_code_search(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    обновления состояния и выполнения поиска продукта  по коду.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    code_product = message.text
    await state.update_data(product=code_product)
    logger.info(
        "В функции process_code_search Пользователь id = %s name = %s "
        "прислал сообщение - %s",
        message.from_user.id, (message.from_user.full_name), code_product
        )
    await message.answer(f"Идет поиск по запросу 🔍 '{code_product}'.")
    await bot.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMfyVmlSY5oE0km2nNvj5ke33RL_1t_gAC6wwAAg2m6VDUyl6qMEbwuzUE"
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    len_product = len(code_product)
    if code_product.isdigit() and len_product != 8 and len_product != 13:
        try:
            logger.info(
                "В функции process_code_search  Попытка поиска товара по сообщению "
                "пользователя id = %s name = %s - запрос = %s",
                message.from_user.id, (message.from_user.full_name), code_product
                )
            product_information = await connect_search(code_product)

            all_product_text = ""
            builder_all = InlineKeyboardBuilder()

            product_data_1 = product_information.get('product_0')

            # Цена
            product_information_to_id_1 = await connect_product_to_id(
                product_data_1.get('product_id')
                )
            img_url = f'{config.IMAGE_URL}{product_information_to_id_1['image']}'

            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                )

            if await check_image_exists(img_url):
                await message.answer(img_url) # картинка
            else:
                await message.answer('Изображение не найдено.')
            # Количество по магазинам
            product_id_1 = product_data_1.get('product_id')
            product_data_1_quantity = await get_product_quatity(product_id_1)
            product_data_1_quantity = quatity_discount(product_data_1_quantity)
            product_data_1_quantity_store_1 =  product_data_1_quantity[0]
            product_data_1_quantity_store_2 = product_data_1_quantity[1]

            product_text_1 = format_product_text(
                product_data_1,
                product_information_to_id_1,
                product_data_1_quantity_store_1,
                product_data_1_quantity_store_2
                )

            all_product_text = product_text_1

            await message.answer("Возможно вы искали этот товар:")
            builder_all.row(
                InlineKeyboardButton(
                    text=product_data_1.get('name'),
                    url=product_data_1.get('url')
                    )
                )
            builder_all.row(
                InlineKeyboardButton(
                    text="Искать на сайте",
                    url=f"https://example.com/search={code_product}"
                    )
                )
            await message.answer(all_product_text, reply_markup=builder_all.as_markup())

            await insert_data(
                message.from_user.id, user_type, 31, 1,
                datetime.now(), message.text, 1
                )

            logger.info(
                "В функции process_code_search  Пользователю id = %s name = %s "
                "отправлено сообщение - all_product_text количество товаров = 1",
                message.from_user.id, (message.from_user.full_name)
                )
        except (TooManyRedirects, AttributeError, TypeError) as e:
            logger.error(
                "В функции process_code_search Пользователь id = %s name = %s "
                "по запросу = %s получил ошибку: - %s",
                message.from_user.id, (message.from_user.full_name), code_product, e
                )
            await message.answer(
                "К сожалению, по вашему запросу ничего не найдено. "
                " Пожалуйста, попробуйте ввести другой код товара или "
                "воспользуйтесь другим видом поиска товаров."
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                )
            await insert_data(
                message.from_user.id, user_type, 31, 1,
                datetime.now(), message.text, 0
                )
    else:
        logger.error(
            "В функции process_code_search Пользователь id = %s name = %s "
            "по запросу = %s ввёл не код товара.",
            message.from_user.id, (message.from_user.full_name), code_product
            )
        await message.answer(
            "К сожалению, по вашему запросу ничего не найдено. "
            "Пожалуйста, попробуйте ввести другой код товара или "
            "воспользуйтесь другим видом поиска товаров."
            )
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
            )
        await insert_data(message.from_user.id, user_type, 31, 1, datetime.now(), message.text, 0)

async def process_input_barcode(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    обновления состояния и выполнения поиска продукта по штрихкоду.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_input_barcode для пользователя "
        "id = %s name = %s",
        message.from_user.id, (message.from_user.full_name)
        )
    await state.update_data(text_barcode=message.text)
    barcode_name = message.text
    logger.info(
        "В функции process_input_barcode Пользователь id = %s name = %s "
        "прислал сообщение - %s",
        message.from_user.id, (message.from_user.full_name), barcode_name
        )
    await message.answer(f"Идет поиск по запросу 🔍 '{barcode_name}'.")
    await bot.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMfyVmlSY5oE0km2nNvj5ke33RL_1t_gAC6wwAAg2m6VDUyl6qMEbwuzUE"
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if (
        (barcode_name is not None and barcode_name.isdigit())
        and (len(barcode_name) == 8 or len(barcode_name) == 13)
        ):
        try:
            logger.info(
                "В функции process_input_barcode Попытка поиска товара по сообщению "
                "пользователя id = %s name = %s - запрос по поиску штрихкода = %s",
                message.from_user.id, (message.from_user.full_name), barcode_name
                )
            product_information = await connect_search(barcode_name)

            product_data_1 = product_information.get('product_0')
            # Количество по магазинам
            product_id_1 = product_data_1.get('product_id')
            product_data_1_quantity = await get_product_quatity(product_id_1)
            product_data_1_quantity = quatity_discount(product_data_1_quantity)
            product_data_1_quantity_store_1 =  product_data_1_quantity[0]
            product_data_1_quantity_store_2 = product_data_1_quantity[1]

            product_text_1 = (
                f"<strong>{product_data_1.get('name')}</strong>\n"
                f"{product_data_1.get('description')}\n"
                )

            product_information_to_id = await connect_product_to_id(
                product_data_1.get('product_id')
                )

            product_attributes_to_id = await connect_product_attributes_to_id(
                product_data_1.get('product_id')
                )

            all_product_text = product_text_1

            builder_all = InlineKeyboardBuilder()
            builder_all.row(
                InlineKeyboardButton(
                    text=product_data_1.get('name'),
                    url=product_data_1.get('url')
                    )
                )
            builder_all.row(
                InlineKeyboardButton(
                    text="Искать на сайте",
                    url=f"https://example.com/search={barcode_name}"
                    )
                )

            # Ответ по штрихкоду
            img_url = f'{config.IMAGE_URL}{product_information_to_id['image']}'

            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                )

            if await check_image_exists(img_url):
                await message.answer(img_url) # картинка
            else:
                await message.answer('Изображение не найдено.')

            answ_text_att = await format_product_attributes(product_attributes_to_id)

            await message.answer(
                f"{all_product_text}\n"
                f"<strong>Цена:</strong> {product_information_to_id['sku']} р.\n"
                f"\n<strong>В наличии:</strong>\n"
                f"Гродно, пр. Космонавтов 2Г - {product_data_1_quantity_store_1} "
                f"{product_information_to_id['upc'].replace('/','')}\n"
                f"Гродно, ул. Дзержинского 118 - {product_data_1_quantity_store_2} "
                f"{product_information_to_id['upc'].replace('/','')}\n"
                f"\n{answ_text_att}\n"
                f"<strong>Категория:</strong> {product_information_to_id['category']}",
                reply_markup=builder_all.as_markup()
                )
            logger.info(
                "В функции process_input_barcode Пользователю id = %s name = %s "
                "отправлено сообщение - all_product_text  количество товаров = 1",
                message.from_user.id, (message.from_user.full_name)
                )

            await insert_data(
                message.from_user.id, user_type, 32, 1,
                datetime.now(), message.text, 1
                )
        except (TooManyRedirects, AttributeError, TypeError) as e:
            logger.error(
                "В функции process_input_barcode Пользователь id = %s name = %s "
                "по запросу = %s получил ошибку: - %s",
                message.from_user.id, (message.from_user.full_name), barcode_name, e
                )
            await message.answer(
                "К сожалению, по вашему запросу ничего не найдено. "
                "Пожалуйста, попробуйте еще раз отправить мне номер штрихкода."
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                )
            await insert_data(
                message.from_user.id, user_type, 32, 1,
                datetime.now(), message.text, 0
                )
    else:
        logger.info(
            "В функции process_input_barcode Попытка поиска товара по сообщению "
            "пользователя id = %s name = %s - запрос по поиску штрихкода = %s не удалась.",
            message.from_user.id, (message.from_user.full_name), barcode_name
            )
        await message.answer(
            "К сожалению, по вашему запросу ничего не найдено. "
            "Пожалуйста, попробуйте еще раз отправить мне номер штрихкода."
            )
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
            )
        await insert_data(message.from_user.id, user_type, 32, 1, datetime.now(), message.text, 0)

async def process_barcode(
    message: Message,
    state: FSMContext,  # pylint: disable=unused-argument
    bot: Bot
    ) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фото штрихкода, обновления состояния,
    скачивание фото, распознавание штрихкода и выполнения поиска продукта.

    :param message: Объект сообщения пользователя, содержащий фото.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_barcode для пользователя "
        "id = %s name = %s",
        message.from_user.id, (message.from_user.full_name)
        )
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    logger.info("В функции process_barcode Получение пути фото от пользователя "
                "id = %s name = %s - путь для фото = %s",
                message.from_user.id, (message.from_user.full_name), file_path
                )
    # Скачиваем файл на диск
    downloaded_file = await bot.download_file(file_path)
    file_name = f"photo_{message.from_user.id}.jpg"
    logger.info(
        "В функции process_barcode Получение название фото от пользователя "
        "id = %s name = %s - для сохрания, название фото = %s",
        message.from_user.id, (message.from_user.full_name), file_path
        )

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file.read())
    logger.info(
        "В функции process_barcode Скачал файл  = %s от пользователя "
        "id = %s name = %s",
        file_name, message.from_user.id, (message.from_user.full_name)
        )

    number_burcode = await return_barcode(file_name)
    await message.answer(f"Идет поиск по запросу 🔍 '{number_burcode}'.")
    await bot.send_sticker(
        chat_id=message.chat.id,
        sticker="CAACAgQAAxkBAAEMfyVmlSY5oE0km2nNvj5ke33RL_1t_gAC6wwAAg2m6VDUyl6qMEbwuzUE"
        )

    logger.info(
        "В функции process_barcode Отсканировал файл  = %s от пользователя "
        "id = %s name = %s и получил номер штрихкода %s",
        file_name, message.from_user.id, (message.from_user.full_name), number_burcode
        )
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )

    if number_burcode is not None and number_burcode.isdigit():
        try:
            logger.info(
                "В функции process_barcode Попытка поиска товара по сообщению "
                "пользователя id = %s name = %s - запрос по поиску штрихкода = %s",
                message.from_user.id, (message.from_user.full_name), number_burcode
                )
            product_information = await connect_search(number_burcode)

            product_data_1 = product_information.get('product_0')
            # Количество по магазинам
            product_id_1 = product_data_1.get('product_id')
            product_data_1_quantity = await get_product_quatity(product_id_1)
            product_data_1_quantity = quatity_discount(product_data_1_quantity)
            product_data_1_quantity_store_1 =  product_data_1_quantity[0]
            product_data_1_quantity_store_2 = product_data_1_quantity[1]

            product_text_1 = (
                f"<strong>{product_data_1.get('name')}</strong>\n"
                f"{product_data_1.get('description')}\n"
                )

            product_information_to_id = await connect_product_to_id(
                product_data_1.get('product_id')
                )

            product_attributes_to_id = await connect_product_attributes_to_id(
                product_data_1.get('product_id')
                )

            all_product_text = product_text_1

            builder_all = InlineKeyboardBuilder()
            builder_all.row(
                InlineKeyboardButton(
                    text=product_data_1.get('name'),
                    url=product_data_1.get('url')
                    )
                )
            builder_all.row(
                InlineKeyboardButton(
                    text="Искать на сайте",
                    url=f"https://example.com/search={number_burcode}"
                    )
                )
            # Ответ по штрихкоду

            img_url = f'{config.IMAGE_URL}{product_information_to_id['image']}'
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                )

            if await check_image_exists(img_url):
                await message.answer(img_url) # картинка
            else:
                await message.answer('Изображение не найдено.')

            answ_text_att = await format_product_attributes(product_attributes_to_id)

            await message.answer(
                f"{all_product_text}\n"
                f"<strong>Цена:</strong> {product_information_to_id['sku']} р.\n"
                f"\n<strong>В наличии:</strong>\n"
                f"Гродно, пр. Космонавтов 2Г - {product_data_1_quantity_store_1} "
                f"{product_information_to_id['upc'].replace('/','')}\n"
                f"Гродно, ул. Дзержинского 118 - {product_data_1_quantity_store_2} "
                f"{product_information_to_id['upc'].replace('/','')}\n"
                f"\n{answ_text_att}\n"
                f"<strong>Категория:</strong> {product_information_to_id['category']}",
                reply_markup=builder_all.as_markup()
            )

            logger.info(
                "В функции process_barcode Пользователю id = %s name = %s "
                "отправлено сообщение - all_product_text количество товаров = 1",
                message.from_user.id, (message.from_user.full_name)
                )
            await insert_data(
                message.from_user.id, user_type, 33, 1,
                datetime.now(), message.text, 1
                )
        except (TooManyRedirects, AttributeError, TypeError) as e:
            logger.error(
                "В функции process_barcode Пользователь id = %s name = %s "
                "по запросу = %s получил ошибку: - %s",
                message.from_user.id, (message.from_user.full_name), number_burcode, e
                )
            await message.answer(
                "К сожалению, по вашему запросу ничего не найдено. "
                "Пожалуйста, попробуйте еще раз отправить мне фото штрихкода "
                "либо нажмите ввести вручную."
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                )
            await insert_data(
                message.from_user.id, user_type, 33, 1,
                datetime.now(), message.text, 0
                )
    else:
        await message.answer(
            "К сожалению, по вашему запросу ничего не найдено. "
            "Пожалуйста, попробуйте еще раз отправить мне фото "
            "штрихкода либо нажмите ввести вручную."
            )
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
            )
        await insert_data(
            message.from_user.id, user_type, 33, 1,
            datetime.now(), message.text, 0
            )
    # Удаляем файл после обработки
    os.remove(file_name)

async def process_added_card(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя
    при добавлении дисконтной карты.
    Функция определяет тип сообщения (текст или фото) и вызывает
    соответствующую функцию для обработки:
    Если сообщение содержит фото, вызывается функция `process_barcode_card`
    для обработки штрихкода дисконтной карты.
    Если сообщение содержит текст, вызывается функция `process_barcode_card_text`
    для обработки номера дисконтной карты.
    Если сообщение не соответствует ни одному из вышеперечисленных типов,
    пользователю отправляется сообщение с просьбой отправить корректные данные
    для добавления дисконтной карты.

    :param message: Объект сообщения пользователя.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_added_card для пользователя "
        "id = %s name =%s",
        message.from_user.id, (message.from_user.full_name)
        )
    user_id = message.from_user.id
    if not await rate_limit(user_id):
        await message.answer("Вы отправили слишком много запросов. Пожалуйста, подождите немного.")
        logger.warning(
            "Пользователь id=%s username=%s, превысил частоту запросов в process_search_general",
            message.from_user.id, message.from_user.full_name
            )
        return
    else:
        if message.photo:
            logger.info(
                "В функции process_added_card для пользователь id = %s name = %s "
                "выполнение process_barcode_card по фото",
                message.from_user.id, (message.from_user.full_name)
                )
            await process_barcode_card(message, state, bot)
        elif message.text:
            logger.info(
                "В функции process_added_card для пользователь id = %s name = %s "
                "выполнение process_barcode_card_text по номеру",
                message.from_user.id, (message.from_user.full_name)
                )
            await process_barcode_card_text(message, state, bot)
        else:
            # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
            await message.answer(
                "Пожалуйста, отправьте мне номер штрихкода или "
                "фотографию штрихкода вашей дисконтной карты."
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfydmlSZPuWg8dghbn9_lIbtevshr1QAC-wkAAp0i6VAWmt8OHJBnnzUE"
                )
            return
        await asyncio.sleep(0.1)

async def process_barcode_card(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фото дисконтной карты, обновления состояния,
    скачивание фото, распознавание штрихкода на карте и 
    выполнения поиска пользователя по коду дисконтной карты.

    :param message: Объект сообщения пользователя, содержащий фото.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_barcode_card "
        "для пользователя id = %s name = %s",
        message.from_user.id, (message.from_user.full_name)
        )
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    logger.info(
        "В функции process_barcode_card Получение пути фото от "
        "пользователя id = %s name = %s - путь для фото = %s",
        message.from_user.id, (message.from_user.full_name), file_path
        )
    # Скачиваем файл на диск
    downloaded_file = await bot.download_file(file_path)
    photo_card = f"photo_{message.from_user.id}.jpg"
    logger.info(
        "В функции process_barcode_card Получение название фото от "
        "пользователя id = %s name = %s - для сохрания, название фото = %s",
        message.from_user.id, (message.from_user.full_name), file_path
        )

    with open(photo_card, 'wb') as new_file:
        new_file.write(downloaded_file.read())
    # Фнукция чтения фото штрихкода возврат текстового значения
    number_card = await return_barcode(photo_card)
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    # Проверка кода
    try:
        customer_info = await get_user_by_card_code(number_card)
        logger.info(
            "В функции process_barcode_card Пользователь "
            "id = %s name = %s прислал сообщение - %s. Результат = %s",
            message.from_user.id, (message.from_user.full_name),
            number_card, customer_info
            )
        if  customer_info is not None:
            logger.info(
                "В функции process_barcode_card Первое условие проверки %s "
                "в функции process_barcode_card  id = %s name = %s.",
                customer_info, message.from_user.id, (message.from_user.full_name)
                )
            # Сохранение id пользователя по скидочным картам
            path_json = 'data/user_data_json/user_id_to_discont_card.json' # путь к jsone
            # ЦУ0000003 это из присланного сообщения
            card_field_two = await get_card_field_two(number_card)
            data_id_card = await read_json_file(path_json) # данные из файла json
            # Проверка совпадения ключа в jsone и полученного поля
            matching_key = await find_matching_key(card_field_two, data_id_card)
            custom_fifeld = json.loads(customer_info['custom_field']) # Поле кастом филд
            field_type = custom_fifeld['2']
            data_card = custom_fifeld['3'] # Срок действия карты
            name_card = ''

            if field_type == 'Р00000002':
                name_card = 'Мастер'
            elif field_type == 'ЦУ0000001':
                name_card = 'Семейная'
            elif field_type == 'ЦУ0000003':
                name_card = 'Сотрудники'
            elif field_type == 'ЦУ0000004':
                name_card = 'Домовёнок'
            elif field_type == 'ЦУ0000005':
                name_card = 'VIP -8%'

            if matching_key and field_type == 'Р00000002' :
                await add_data_to_json(path_json, matching_key, message.from_user.id)
                # Сохранение в json номер карты
                from_user_id = str(message.from_user.id)
                from_user_card = number_card
                user_data = {from_user_id:from_user_card}
                filename = 'data/user_data_json/user_id_and_number_card_master.json'
                await update_json_file(user_data, filename)
            elif  matching_key:
                await add_data_to_json(path_json, matching_key, message.from_user.id)

            number_barcode_path = (
                f"{message.from_user.id}{message.from_user.full_name}"
                f"{number_card}barcode.png"
                )
            logger.info(
                "В функции process_barcode_card Путь штрихкода %s "
                "для пользователя id = %s name = %s",
                number_barcode_path, message.from_user.id, (message.from_user.full_name)
                )
            await generate_barcode(number_card, number_barcode_path)
            text_caption = (
                    f"<strong>Карта:</strong> {name_card}\n"
                    f"<strong>Срок действия:</strong> по {data_card}\n"
                    f"Закрепил для вас, изображение штрихкода вашей дисконтной "
                    f"карты. Теперь, она всегда будет у вас под рукой."
                    )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                )
            message_with_photo = await message.answer_photo(
                FSInputFile(path=number_barcode_path),
                caption=text_caption
                )
            logger.info(
                "В функции process_barcode_card Сгенерировал изображение "
                "штрихкода = %s по пути %s от пользователя id = %s name = %s",
                number_card, number_barcode_path, message.from_user.id,
                (message.from_user.full_name)
                )
            await bot.pin_chat_message(
                chat_id=message.chat.id,
                message_id=message_with_photo.message_id
                )

            os.remove(photo_card)
            os.remove(number_barcode_path)
            await general_menu(message, state)
            await insert_data(
                message.from_user.id, user_type, 34, 1,
                datetime.now(), message.text, 1
                )
        else:
            logger.error(
                "Второе условие проверки customer_info = %s в функции "
                "process_barcode_card  id = %s name = %s.",
                None, message.from_user.id, (message.from_user.full_name)
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                )
            await message.answer(
                "Попробуйте еще раз отправить мне фото вашей дисконтной карты, "
                "возможно фото плохого качества или введите вручную код с карты - "
                "нажмите 'Ввести вручную'."
                )
            os.remove(photo_card)
            await insert_data(
                message.from_user.id, user_type, 34, 1,
                datetime.now(), message.text, 0
                )
    except (TooManyRedirects, AttributeError, TypeError) as e:
        logger.error(
            "В функции process_barcode_card Пользователь id = %s name = %s "
            "получил ошибку: - %s",
            message.from_user.id, (message.from_user.full_name), e
            )
        os.remove(photo_card)
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
            )
        await message.answer(
            "Попробуйте еще раз отправить мне фото вашей дисконтной карты, "
            "возможно фото плохого качества или введите вручную код с карты - "
            "нажмите 'Ввести вручную'."
            )
        await insert_data(message.from_user.id, user_type, 34, 1, datetime.now(), message.text, 0)

async def process_barcode_card_text(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего текстовое представление номера дисконтной карты,
    обновления состояния, поиска пользователя по коду дисконтной
    карты и выполнения дополнительных действий.

    :param message: Объект сообщения пользователя, содержащий текст номера карты.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_barcode_card_text "
        "для пользователя id = %s name = %s",
        message.from_user.id, (message.from_user.full_name)
        )
    await state.update_data(text_card=message.text)
    number_card = message.text
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    if (number_card is not None) and (number_card.isdigit()):
        try:
            customer_info = await get_user_by_card_code(number_card)
            logger.info(
                "В функции process_barcode_card_text Пользователь "
                "id = %s name = %s прислал сообщение - %s. Результат = %s",
                message.from_user.id, (message.from_user.full_name), number_card, customer_info
                )
            if customer_info is not None:
                logger.info(
                    "В функции process_barcode_card_text Проверка %s "
                    "первое условие от пользователя id = %s name = %s.",
                    customer_info, message.from_user.id, (message.from_user.full_name)
                    )
                # Сохранение id пользователя по скидочным картам
                path_json = 'data/user_data_json/user_id_to_discont_card.json' # путь к jsone
                # ЦУ0000003 это из присланного сообщения
                card_field_two = await get_card_field_two(number_card)
                data_id_card = await read_json_file(path_json) # данные из файла json
                # Проверка совпадения ключа в jsone и полученного поля
                matching_key = await find_matching_key(card_field_two, data_id_card)
                custom_fifeld = json.loads(customer_info['custom_field']) # Поле кастом филд
                field_type = custom_fifeld['2']
                data_card = custom_fifeld['3'] # Срок действия карты
                name_card = ''

                if field_type == 'Р00000002':
                    name_card = 'Мастер'
                elif field_type == 'ЦУ0000001':
                    name_card = 'Семейная'
                elif field_type == 'ЦУ0000003':
                    name_card = 'Сотрудники'
                elif field_type == 'ЦУ0000004':
                    name_card = 'Домовёнок'
                elif field_type == 'ЦУ0000005':
                    name_card = 'VIP -8%'

                if matching_key and field_type == 'Р00000002':
                    await add_data_to_json(path_json, matching_key, message.from_user.id)
                    # Сохранение в json номер карты
                    from_user_id = str(message.from_user.id)
                    from_user_card = number_card
                    user_data = {from_user_id:from_user_card}
                    filename = 'data/user_data_json/user_id_and_number_card_master.json'
                    await update_json_file(user_data, filename)
                elif  matching_key:
                    await add_data_to_json(path_json, matching_key, message.from_user.id)

                # Отправка сообщения в чат и закрепление его + генерация штрихкода по номеру
                number_barcode_path = (
                    f"{message.from_user.id}{message.from_user.full_name}"
                    f"{number_card}barcode.png"
                    )
                logger.info(
                    "В функции process_barcode_card_text Путь штрихкода %s "
                    "для пользователя id = %s name = %s",
                    number_barcode_path, message.from_user.id, (message.from_user.full_name)
                    )
                await generate_barcode(number_card, number_barcode_path)
                text_caption = (
                    f"<strong>Карта:</strong> {name_card}\n"
                    f"<strong>Срок действия:</strong> по {data_card}\n"
                    f"Закрепил для вас, изображение штрихкода вашей дисконтной карты. "
                    f"Теперь, она всегда будет у вас под рукой."
                    )
                await bot.send_sticker(
                    chat_id=message.chat.id,
                    sticker=(
                        "CAACAgQAAxkBAAEMfy1mlSaAh1BFYWCvj0"
                        "Ln2EpdIWNMSAACagsAAoPUcVFBVwGQCY7yJDUE"
                        )
                    )
                message_with_photo = await message.answer_photo(
                    FSInputFile(path=number_barcode_path), caption=text_caption
                    )
                await bot.pin_chat_message(
                    chat_id=message.chat.id,
                    message_id=message_with_photo.message_id
                    )
                os.remove(number_barcode_path)
                await general_menu(message, state)
                await insert_data(
                    message.from_user.id, user_type, 35, 1,
                    datetime.now(), message.text, 1
                    )
            else:
                logger.error(
                    "В функции process_barcode_card_text Проверка customer_info = %s "
                    "второе условие от пользователя id = %s name = %s.",
                    None, message.from_user.id, (message.from_user.full_name)
                    )
                await bot.send_sticker(
                    chat_id=message.chat.id,
                    sticker=(
                        "CAACAgQAAxkBAAEMfytmlSZ1A6vs"
                        "-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                        )
                    )
                await message.answer(
                    "Попробуйте еще раз отправить мне номер вашей дисконтной карты, "
                    "возможно вы ошиблись."
                    )
                await insert_data(
                    message.from_user.id, user_type, 35, 1,
                    datetime.now(), message.text, 0
                    )
        except (TooManyRedirects, AttributeError, TypeError) as e:
            logger.error(
                "В функции process_barcode_card_text пользователь "
                "id = %s name = %s по запросу = %s получил ошибку: - %s",
                message.from_user.id, (message.from_user.full_name), number_card, e
                )
            await bot.send_sticker(
                chat_id=message.chat.id,
                sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
                )
            await message.answer(
                "К сожалению, по вашему запросу ничего не найдено. "
                "Пожалуйста, попробуйте еще раз отправить мне номер вашей карты."
                )
            await insert_data(
                message.from_user.id, user_type, 35, 1,
                datetime.now(), message.text, 0
                )
    else:
        logger.error(
            "В функции process_barcode_card_text Проверка customer_info = %s "
            "второе условие от пользователя id = %s name = %s.",
            None, message.from_user.id, (message.from_user.full_name)
            )
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfytmlSZ1A6vs-8mvAAHW5bfgjYWjWNgAAmUNAAKQnOlQenL3YIArH3s1BA"
            )
        await message.answer(
            "Попробуйте еще раз отправить мне номер "
            "вашей дисконтной карты, возможно вы ошиблись."
            )
        await insert_data(message.from_user.id, user_type, 35, 1, datetime.now(), message.text, 0)

async def process_ask_question(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки вопроса от пользователя,
    обновления состояния.

    :param message: Объект сообщения пользователя, содержащий текст номера карты.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_ask_question "
        "для пользователя Пользователь id = %s name = %s.",
        message.from_user.id, (message.from_user.full_name)
        )
    try:
        user_type = await find_user_id(
            message.from_user.id,
            "data/user_data_json/user_id_to_discont_card.json"
            )
        messag_text = await censor_swear_words(message.text)
        full_text_message = (
            f"{message.from_user.id}, {message.message_id}, \n"
            f"сообщение: {messag_text}\n"
            f"от пользователя: {message.from_user.full_name}"
        )
        await bot.send_message(chat_id=config.OPERATOR_ID, text=full_text_message)
        await state.update_data(ask_question=FormAsk.ask_question)
        await message.answer("Ваше сообщение отправлено оператору. Ожидайте ответа.")
        await bot.send_sticker(
            chat_id=message.chat.id,
            sticker="CAACAgQAAxkBAAEMfydmlSZPuWg8dghbn9_lIbtevshr1QAC-wkAAp0i6VAWmt8OHJBnnzUE"
            )
        await insert_data(message.from_user.id, user_type, 37, 1, datetime.now(), message.text, 1)
        logger.info(
            "Пользователь id = %s name = %s прислал сообщение - %s .",
            message.from_user.id, (message.from_user.full_name), message.text
            )
    except Exception as e:  # pylint: disable=broad-exception-caught
        await insert_data(message.from_user.id, user_type, 37, 1, datetime.now(), message.text, 0)
        logger.error(
            "Пользователь id = %s name = %s вызвал команду "
            "- Задать вопрос оператору(process) и получил ошибку %s",
            message.from_user.id, (message.from_user.full_name), e
            )

async def process_answer_questions(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки ответа от оператора пользователю,
    обновления состояния.

    :param message: Объект сообщения пользователя, содержащий текст номера карты.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info(
        "Начало выполнения функции process_answer_questions "
        "для пользователя Пользователь id = %s name = %s.",
        message.from_user.id, (message.from_user.full_name)
        )
    try:
        user_type = await find_user_id(
            message.from_user.id,
            "data/user_data_json/user_id_to_discont_card.json"
            )
        await state.update_data(answ_question=FormAsk.answer_questions)
        chatid, mesid = message.reply_to_message.text.split(maxsplit=1)
        mesid = int(re.search(r'\d+', mesid).group())
        await bot.send_message(chat_id=chatid, text=message.text, reply_to_message_id=mesid)
        await insert_data(message.from_user.id, user_type, 38, 1, datetime.now(), message.text, 1)
        logger.info(
            "Пользователь id = %s name = %s отправил сообщение "
            "пользователю %s сообщение - %s .", message.from_user.id,
            (message.from_user.full_name), chatid, message.text
            )
    except Exception as e:  # pylint: disable=broad-exception-caught
        await insert_data(message.from_user.id, user_type, 38, 1, datetime.now(), message.text, 0)
        logger.error(
            "Пользователь id = %s name = %s вызвал команду "
            "-  Ответить на вопросы(process) и получил ошибку %s",
            message.from_user.id, (message.from_user.full_name), e
            )

async def process_send_advertisements_all(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фотографию, видео или текст, и отправки этого
    сообщения всем пользователям, указанным в JSON-файле.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"

    await state.update_data(send_all=path_media)
    logger.info(
        "Начало выполнения функции process_send_advertisements_all "
        "для пользователя id = %s name = %s прислал сообщение = %s %s",
        message.from_user.id, message.from_user.full_name, path_media, media_type
        )
    path_json_all = 'data/user_data_json/user_id_and_username.json'
    data_id = await read_json_file(path_json_all)
    data_id = data_id.keys()
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id in data_id:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements_all "
                "для пользователя id = %s name = %s прислал сообщение = %s %s",
                message.from_user.id, message.from_user.full_name, path_media, media_type
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id  # Айди последней публикации для всех фото
                await insert_message_data(file_photo_id, 2, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 23, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id  # Айди последней публикации для всех видео
                await insert_message_data(file_video_id, 3, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 23, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id, text=path_media)
                file_text_id = message.message_id # Айди последней публикации для всех текст
                await insert_message_data(file_text_id, 1, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 23, 1, datetime.now(), 1, 1)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка в функции process_send_advertisements_all для пользователя "
                "id = %s name = %s при отправке сообщения пользователю %s: %s",
                message.from_user.id, message.from_user.full_name, user_id, e
                )
            await insert_data(message.from_user.id, user_type, 23, 1, datetime.now(), 4, 0)

async def process_send_advertisements_family(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя, 
    содержащего фотографию, видео или текст, и отправки этого
    сообщения всем пользователям, указанным в JSON-файле,
    относящихся к владельцам карты семейная.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
        "Начало функции process_send_advertisements_family для пользователя "
        "id = %s name = %s  прислал сообщение = %s %s",
        message.from_user.id, (message.from_user.full_name), path_media, media_type
        )
    await state.update_data(send_family=path_media)

    path_json_all = 'data/user_data_json/user_id_to_discont_card.json'
    data_id = await read_json_file(path_json_all)
    data_id = data_id['ЦУ0000001']
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id in data_id:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements_family "
                "для пользователя id = %s name = %s прислал сообщение = %s %s",
                message.from_user.id, message.from_user.full_name, path_media, media_type
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id
                await insert_message_data(file_photo_id, 2, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 24, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id
                await insert_message_data(file_video_id, 3, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 24, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id, text=path_media)
                file_text_id = message.message_id
                await insert_message_data(file_text_id, 1, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 24, 1, datetime.now(), 1, 1)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка при отправке сообщения пользователю %s от пользователя "
                "id = %s name = %s в функции process_send_advertisements_family: %s",
                user_id, message.from_user.id, message.from_user.full_name, e
                )
            await insert_data(message.from_user.id, user_type, 24, 1, datetime.now(), 4, 0)

async def process_send_advertisements_master(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фотографию, видео или текст, и отправки этого сообщения
    всем пользователям, указанным в JSON-файле, относящихся к владельцам карты мастер.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
        "Начало функции process_send_advertisements_master "
        "для пользователя id = %s name = %s",
        message.from_user.id, (message.from_user.full_name)
        )
    await state.update_data(send_master=path_media)

    path_json_all = 'data/user_data_json/user_id_to_discont_card.json'
    data_id = await read_json_file(path_json_all)
    data_id = data_id['Р00000002']
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id in data_id:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements_master "
                "для пользователя id = %s name = %s прислал сообщение = %s",
                message.from_user.id, message.from_user.full_name, path_media
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id
                await insert_message_data(file_photo_id, 2, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 25, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id
                await insert_message_data(file_video_id, 3, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 25, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id, text=path_media)
                file_text_id = message.message_id
                await insert_message_data(file_text_id, 1, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 25, 1, datetime.now(), 1, 1)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка при отправке сообщения пользователю %s от пользователя "
                "id = %s name = %s в функции process_send_advertisements_master: %s",
                user_id, message.from_user.id, (message.from_user.full_name), e
                )
            await insert_data(message.from_user.id, user_type, 25, 1, datetime.now(), 4, 0)

async def process_send_advertisements_home(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фотографию, видео или текст, и отправки этого сообщения
    всем пользователям, указанным в JSON-файле, относящихся к владельцам карты домовёнок.
    
    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
        "Начало функции process_send_advertisements_home для пользователя "
        "id = %s name = %s прислал сообщение = %s %s",
        message.from_user.id, (message.from_user.full_name), path_media, media_type
        )
    await state.update_data(send_home=path_media)

    path_json_all = 'data/user_data_json/user_id_to_discont_card.json'
    data_id = await read_json_file(path_json_all)
    data_id = data_id['ЦУ0000004']
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id in data_id:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements_home "
                "для пользователя id = %s name = %s  прислал сообщение = %s %s",
                message.from_user.id, message.from_user.full_name, path_media, media_type
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id
                await insert_message_data(file_photo_id, 2, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 26, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id
                await insert_message_data(file_video_id, 3, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 26, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id, text=path_media)
                file_text_id = message.message_id
                await insert_message_data(file_text_id, 1, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 26, 1, datetime.now(), 1, 1)
            await asyncio.sleep(0.1)  # Небольшая пауза между сообщениями
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка при отправке сообщения пользователю %s от пользователя "
                "id = %s name = %s в функции process_send_advertisements_home: %s",
                user_id, message.from_user.id, (message.from_user.full_name), e
                )
            await insert_data(message.from_user.id, user_type, 26, 1, datetime.now(), 4, 0)

async def process_send_advertisements_employee(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фотографию, видео или текст, и отправки этого сообщения
    всем пользователям, указанным в JSON-файле, относящихся к владельцам карты работников.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'

    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'

    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
        "Начало функции process_send_advertisements_employee "
        "для пользователя id = %s name = %s  прислал сообщение = %s %s",
        message.from_user.id, (message.from_user.full_name), path_media, media_type
        )
    await state.update_data(send_employee=path_media)
    path_json_all = 'data/user_data_json/user_id_to_discont_card.json'
    data_id = await read_json_file(path_json_all)
    data_id = data_id['ЦУ0000003']
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id in data_id:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements "
                "employee для пользователя id = %s name = %s  прислал сообщение = %s %s",
                message.from_user.id, message.from_user.full_name, path_media, media_type
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id
                await insert_message_data(file_photo_id, 2, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 27, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id
                await insert_message_data(file_video_id, 3, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 27, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id, text=path_media)
                file_text_id = message.message_id
                await insert_message_data(file_text_id, 1, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 27, 1, datetime.now(), 1, 1)
            await asyncio.sleep(0.1)  # Небольшая пауза между сообщениями
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка при отправке сообщения пользователю %s "
                "от пользователя id = %s name = %s "
                "в функции process_send_advertisements_employee: %s",
                user_id, message.from_user.id, (message.from_user.full_name), e
                )
            await insert_data(message.from_user.id, user_type, 27, 1, datetime.now(), 4, 0)

async def process_send_advertisements_vip(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фотографию, видео или текст, и отправки этого сообщения
    всем пользователям, указанным в JSON-файле, относящихся к владельцам карты vip.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
                "Начало функции process_send_advertisements_vip "
                "для пользователя id = %s name = %s  прислал сообщение = %s %s",
                message.from_user.id, (message.from_user.full_name), path_media, media_type
                )
    await state.update_data(send_vip=path_media)
    path_json_all = 'data/user_data_json/user_id_to_discont_card.json'
    data_id = await read_json_file(path_json_all)
    data_id = data_id['ЦУ0000005']
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id in data_id:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements_vip "
                "для пользователя id = %s name = %s  прислал сообщение = %s %s",
                message.from_user.id, message.from_user.full_name, path_media, media_type
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id
                await insert_message_data(file_photo_id, 2, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 28, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id
                await insert_message_data(file_video_id, 3, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 28, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id, text=path_media)
                file_text_id = message.message_id
                await insert_message_data(file_text_id, 1, user_type, user_id, datetime.now())
                await insert_data(message.from_user.id, user_type, 28, 1, datetime.now(), 1, 1)
            await asyncio.sleep(0.1)  # Небольшая пауза между сообщениями
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка при отправке сообщения пользователю %s "
                "от пользователя id = %s name = %s "
                "в функции process_send_advertisements_vip: %s ",
                user_id, message.from_user.id, (message.from_user.full_name), e
                )
            await insert_data(message.from_user.id, user_type, 28, 1, datetime.now(), 4, 0)

async def process_send_advertisements_family_and_home(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя, содержащего фотографию,
    видео или текст, и отправки этого сообщения всем пользователям, 
    указанным в JSON-файле, относящихся к владельцам карт семейная и домовёнок.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
        "Начало функции process_send_advertisements_family_and_home "
        "для пользователя id = %s name = %s  прислал сообщение = %s %s",
        message.from_user.id, (message.from_user.full_name), path_media, media_type
        )
    await state.update_data(send_family_and_home=path_media)
    path_json_all = 'data/user_data_json/user_id_to_discont_card.json'
    data_id = await read_json_file(path_json_all)
    data_id_1 = data_id['ЦУ0000001']
    data_id_2 = data_id['ЦУ0000004']
    data_id_set = set(data_id_1 + data_id_2)
    data_id_list = list(data_id_set)
    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id_1 in data_id_list:
        try:
            logger.info(
                "Попытка отправки рекламы в функции process_send_advertisements_family_and_home "
                "для пользователя id = %s name = %s "
                "прислал сообщение = %s %s",
                message.from_user.id, message.from_user.full_name,
                path_media, media_type
                )
            if media_type == 'photo':
                await bot.send_photo(chat_id=user_id_1, photo=path_media, caption=caption_text)
                file_photo_id = message.photo[-1].file_id
                await insert_message_data(file_photo_id, 2, user_type, user_id_1, datetime.now())
                await insert_data(message.from_user.id, user_type, 29, 1, datetime.now(), 2, 1)
            elif media_type == 'video':
                await bot.send_video(chat_id=user_id_1, video=path_media, caption=caption_text)
                file_video_id = message.video.file_id
                await insert_message_data(file_video_id, 3, user_type, user_id_1, datetime.now())
                await insert_data(message.from_user.id, user_type, 29, 1, datetime.now(), 3, 1)
            elif media_type == 'text':
                await bot.send_message(chat_id=user_id_1, text=path_media)
                file_text_id = message.message_id
                await insert_message_data(file_text_id, 1, user_type, user_id_1, datetime.now())
                await insert_data(message.from_user.id, user_type, 29, 1, datetime.now(), 1, 1)
            await asyncio.sleep(0.1)  # Небольшая пауза между сообщениями
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Ошибка при отправке сообщения пользователю %s "
                "от пользователя id = %s "
                "name = %s "
                "в функции process_send_advertisements_family_and_home: %s",
                user_id_1, message.from_user.id, (message.from_user.full_name), e
                )
            await insert_data(message.from_user.id, user_type, 29, 1, datetime.now(), 4, 0)

async def process_send_all_without_master(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Асинхронная функция для обработки сообщения пользователя,
    содержащего фотографию, видео или текст, и отправки этого сообщения всем пользователям,
    указанным в JSON-файле, относящихся ко всем пользователям, кроме карты Мастер.

    :param message: Объект сообщения пользователя, содержащий фотографию, видео или текст.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    if message.photo:
        # Если пользователь отправил фотографию, получаем путь к ней
        path_media = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        # Если пользователь отправил видео, получаем путь к нему
        path_media = message.video.file_id
        media_type = 'video'
    elif message.text:
        # Если пользователь отправил текст, используем его в качестве заголовка
        path_media = message.text
        media_type = 'text'
    else:
        # Если пользователь отправил неизвестный тип сообщения, выводим сообщение об ошибке
        await message.answer("Пожалуйста, отправьте фотографию, видео или текст.")
        return

    caption_text = message.caption if message.caption else "Новая акция!"
    logger.info(
        "Начало функции process_send_advertisements_family_and_home "
        "для пользователя id = %s "
        "name = %s "
        "прислал сообщение = %s %s",
        message.from_user.id, (message.from_user.full_name), path_media, media_type
        )
    await state.update_data(send_all_withot_master=path_media)

    path_json_all = 'data/user_data_json/user_id_and_username.json'
    data_id_all = await read_json_file(path_json_all)
    data_id_all = set(data_id_all.keys()) # Все

    path_json_master = 'data/user_data_json/user_id_to_discont_card.json'
    data_id_master = await read_json_file(path_json_master)
    data_id_1 = set(data_id_master["Р00000002"]) # Мастер

    user_type = await find_user_id(
        message.from_user.id,
        "data/user_data_json/user_id_to_discont_card.json"
        )
    for user_id_1 in data_id_all:
        if user_id_1 not in data_id_1:
            try:
                logger.info(
                    "Попытка отправки рекламы в функции "
                    "process_send_advertisements_family_and_home "
                    "для пользователя id = %s "
                    "name = %s "
                    "прислал сообщение = %s %s",
                    message.from_user.id, message.from_user.full_name, path_media, media_type
                    )
                if media_type == 'photo':
                    await bot.send_photo(chat_id=user_id_1, photo=path_media, caption=caption_text)
                    file_photo_id = message.photo[-1].file_id
                    await insert_message_data(
                        file_photo_id,
                        2,
                        user_type,
                        user_id_1,
                        datetime.now()
                        )
                    await insert_data(message.from_user.id, user_type, 36, 1, datetime.now(), 2, 1)
                elif media_type == 'video':
                    await bot.send_video(chat_id=user_id_1, video=path_media, caption=caption_text)
                    file_video_id = message.video.file_id
                    await insert_message_data(
                        file_video_id,
                        3,
                        user_type,
                        user_id_1,
                        datetime.now()
                        )
                    await insert_data(message.from_user.id, user_type, 36, 1, datetime.now(), 3, 1)
                elif media_type == 'text':
                    await bot.send_message(chat_id=user_id_1, text=path_media)
                    file_text_id = message.message_id
                    await insert_message_data(file_text_id, 1, user_type, user_id_1, datetime.now())
                    await insert_data(message.from_user.id, user_type, 36, 1, datetime.now(), 1, 1)
                await asyncio.sleep(0.1)  # Небольшая пауза между сообщениями
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Ошибка при отправке сообщения пользователю %s "
                    "от пользователя id = %s "
                    "name = %s "
                    "в функции process_send_advertisements_family_and_home: %s",
                    user_id_1, message.from_user.id, (message.from_user.full_name), e
                    )
                await insert_data(message.from_user.id, user_type, 36, 1, datetime.now(), 4, 0)
        else:
            await message.answer("Таких нет.")
