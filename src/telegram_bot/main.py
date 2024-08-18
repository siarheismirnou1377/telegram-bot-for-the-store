"""
Модуль main содержит функции-обработчики для управления telegram-ботом.
Эти функции предназначены для вызова других функций из других модулей
telgram-bota. Так же тут есть функци запуска бота, остановки и бэкапа.
Функционал разделен на несколько модулей: 
1. Главное меню;
    1.1 Меню поиска товра;
    1.2 Меню дисконтной карт;
2.Меню управления маркетингом;
    2.1 Меню маркетинга;
    2.2 Меню статистики;
    2.3 меню рассылки;
3. Меню управления;
4. Меню запуска бота.
"""

import asyncio
import datetime
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler
import aiofiles

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile

from src.telegram_bot.other_button import (
    add_discont_card,
    all_requests_to_code,
    answer_question,
    ask_question,
    information,
    product_search,
    send_advertisements_family_and_home,
    send_all_without_master,
    visit_the_store,
    balance_discont_card,
    send_advertisements_all,
    send_advertisements_family,
    send_advertisements_master,
    send_advertisements_home,
    handle_privacy_agreement,
    stats_start_bot,
    click_button_stat,
    activity_not_card_stat,
    activity_card_stat,
    all_posts_stat,
    all_users_stat,
    all_users_not_card_stat,
    all_users_card_stat,
    bot_ban_stat,
    all_requests,
    popular_requests,
    all_requests_to_word,
    all_requests_to_barcode,
    time_search_popular,
    stats_all,
)
from src.telegram_bot.menus import (
    general_menu_marketing,
    general_menu,
    start_bot,
    stats_search,
    menu_marketing,
    menu_statistic,
    sending_out_advertisements,
    stats_click, stats_activity,
    stats_posts, stats_users,
)
from src.telegram_bot.states_class import (
    FormAsk,
    FormProduct,
    FormDiscontCard,
    FormSendingAdv,
    UserStates
)
from src.telegram_bot import process_bot
from configs import config


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/bot_gemma_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('bot_gemma_logger')
logger.addHandler(file_handler)



# Создание роутера
form_router = Router()

# Создание бота с указанным токеном и режимом разбора HTML
gemma_bot = Bot(config.TOKEN, parse_mode=ParseMode.HTML)

# Создание диспетчера
dp = Dispatcher()

# Включение роутера в диспетчер
dp.include_router(form_router)

#-------------------------------------------------------------УПРАВЛЕНИЕ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ---------------------------------------------------------------------------------------#
#---------------------------------------------------------------------ГЛАВНОГО МЕНЮ---------------------------------------------------------------------------------------------------#

# Обработчик команды "/start"
@form_router.message(CommandStart())
async def start_bot_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "/start".
    Вызывает функцию handle_privacy_agreement для обработки согласия 
    пользователя с политикой конфиденциальности.

    :param message: Объект сообщения пользователя, содержащий команду "/start".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции start_bot_wrapper")
    await handle_privacy_agreement(message, state, bot)

@form_router.message(UserStates.privacy_agreement)
async def process_privacy_agreement_wrapper(message: Message, state: FSMContext, bot:Bot) -> None:
    """
    Обработчик сообщений в состоянии privacy_agreement.
    Вызывает функцию process_bot.process_privacy_agreement
    для обработки согласия пользователя с политикой конфиденциальности.

    :param message: Объект сообщения пользователя.
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_privacy_agreement_wrapper")
    await process_bot.process_privacy_agreement(message, state, bot)

# Обработчик команды "Информация"
@form_router.message(F.text == "Информация")
async def information_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Информация".
    Вызывает функцию information для предоставления пользователю информации о боте.

    :param message: Объект сообщения пользователя, содержащий команду "Информация".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции information_wrapper")
    await information(message, state)

# Обработчик команды "Перезапустить бот"
@form_router.message(F.text == "Перезапустить бот")
async def restart_wrapper(message: Message) -> None:
    """
    Обработчик команды "Перезапустить бот".
    Вызывает функцию start_bot для перезапуска бота.

    :param message: Объект сообщения пользователя, содержащий команду "Перезапустить бот".
    :return: None
    """
    logger.info("Выполнение функции start_bot")
    await start_bot(message)

# Обработчик команды "Посетить магазин"
@form_router.message(F.text == "Посетить магазин")
async def visit_the_store_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Посетить магазин".
    Вызывает функцию visit_the_store для вывода ссылки сайта магазина и информации о работе.

    :param message: Объект сообщения пользователя, содержащий команду "Посетить магазин".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции visit_the_store_wrapper")
    await visit_the_store(message, state)

# Обработчик команды "Главное меню"
@form_router.message(F.text == "Главное меню")
async def general_menu_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Главное меню".
    Вызывает функцию general_menu для возврата пользователя в главное меню.

    :param message: Объект сообщения пользователя, содержащий команду "Главное меню".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции general_menu_wrapper")
    await general_menu(message, state)

# Обработчик команды "Задать вопрос оператору"
@form_router.message(F.text == "Задать вопрос оператору")
async def ask_question_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Задать вопрос оператору".
    Вызывает функцию ask_question для начала процесса задания вопроса оператору.

    :param message: Объект сообщения пользователя, содержащий команду "Задать вопрос оператору".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции ask_question_wrapper")
    await ask_question(message, state)

@form_router.message(FormAsk.ask_question)
async def process_ask_question_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик сообщений в состоянии ask_question.
    Обрабатывает введенный пользователем текст и вызывает
    соответствующие функции в зависимости от команды.

    :param message: Объект сообщения пользователя.
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_ask_question_wrapper")
    if message.text == "Дисконтная карта":
        await state.clear()
        await add_discont_card(message, state, bot)
    elif message.text == "Информация":
        await state.clear()
        await information(message, state)
    elif message.text == "Посетить магазин":
        await state.clear()
        await visit_the_store(message, state)
    elif message.text == f'/{config.COMMAND}':
        await state.clear()
        await general_menu_marketing(message, state)
    elif  message.text == "Баланс д.к. Мастер":
        await state.clear()
        await balance_discont_card(message, state)
    elif message.text == "Поиск товара":
        await state.clear()
        await product_search(message, state, bot)
    else:
        await process_bot.process_ask_question(message, state, bot)

# Обработчик команды "Ответить на вопросы"
@form_router.message(F.text == "Ответить на вопросы")
async def answer_question_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Ответить на вопросы".
    Вызывает функцию answer_question для начала процесса ответа на вопросы пользователей.

    :param message: Объект сообщения пользователя, содержащий команду "Ответить на вопросы".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции answer_question_wrapper")
    await answer_question(message, state)

@form_router.message(FormAsk.answer_questions)
async def process_answer_questions_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик сообщений в состоянии answer_questions.
    Обрабатывает введенный пользователем текст и вызывает
    соответствующие функции в зависимости от команды.

    :param message: Объект сообщения пользователя.
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_answer_questions_wrapper")
    if message.text == "Дисконтная карта":
        await state.clear()
        await add_discont_card(message, state, bot)
    elif message.text == "Информация":
        await state.clear()
        await information(message, state)
    elif message.text == "Посетить магазин":
        await state.clear()
        await visit_the_store(message, state)
    elif message.text == f'/{config.COMMAND}':
        await state.clear()
        await general_menu_marketing(message, state)
    elif  message.text == "Баланс д.к. Мастер":
        await state.clear()
        await balance_discont_card(message, state)
    elif message.text == "Поиск товара":
        await state.clear()
        await product_search(message, state, bot)
    else:
        await process_bot.process_answer_questions(message, state, bot)



#----------------------------------------------------------------КОНЕЦ ГЛАВНОГО МЕНЮ---------------------------------------------------------------------------------------------#


#----------------------------------------------------------------МЕНЮ ПОИСКА ТОВАРА----------------------------------------------------------------------------------------------#

# Обработчик команды "Поиск товара"
@form_router.message(F.text == "Поиск товара")
async def product_search_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "Поиск товара".
    Вызывает функцию product_search для начала процесса поиска товара.

    :param message: Объект сообщения пользователя, содержащий команду "Поиск товара".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции product_search_wrapper")
    await product_search(message, state, bot)

# Обработчик сообщений, когда пользователь находится в состоянии FormProduct.product
@form_router.message(FormProduct.product)
async def process_search_general_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии FormProduct.product.
    Передает управление в функцию process_bot.process_search для дальнейшей обработки сообщения.

    :param message: Объект сообщения пользователя, который должен быть обработан.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_search_general_wrapper")
    if message.text == "Дисконтная карта":
        await state.clear()
        await add_discont_card(message, state, bot)
    elif message.text == "Информация":
        await state.clear()
        await information(message, state)
    elif message.text == "Посетить магазин":
        await state.clear()
        await visit_the_store(message, state)
    elif message.text == f'/{config.COMMAND}':
        await state.clear()
        await general_menu_marketing(message, state)
    elif  message.text == "Баланс д.к. Мастер":
        await state.clear()
        await balance_discont_card(message, state)
    elif  message.text == "Задать вопрос оператору":
        await state.clear()
        await ask_question(message, state)
    elif message.text == "Ответить на вопросы":
        await state.clear()
        await answer_question(message, state)
    else:
        # Передача управления в функцию process_bot.process_search
        await process_bot.process_search_general(message, state, bot)

#--------------------------------------------------------------КОНЕЦ МЕНЮ ПОИСКА ТОВАРА------------------------------------------------------------------------------------------#


#----------------------------------------------------------------МЕНЮ ДИСКОНТНОЙ КАРТЫ-------------------------------------------------------------------------------------------#

# Обработчик команды "Дисконтная карта"
@form_router.message(F.text == "Дисконтная карта")
async def add_discont_card_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "Дисконтная карта".
    Вызывает функцию add_discont_card для начала процесса добавления дисконтной карты.

    :param message: Объект сообщения пользователя, содержащий команду "Дисконтная карта".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции add_discont_card_wrapper")
    await add_discont_card(message, state, bot)

# Обработчик сообщений, когда пользователь находится в
# состоянии FormDiscontCard.photo_card и отправляет фото
@form_router.message(FormDiscontCard.number_card)
async def process_added_card_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии
    FormDiscontCard.photo_card и отправляет фото.
    Передает управление в функцию process_bot.process_added_card
    для дальнейшей обработки фото дисконтной карты.

    :param message: Объект сообщения пользователя, содержащий фото дисконтной карты.
    :param state: Объект состояния пользователя.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_added_card_wrapper")
    if message.text == "Баланс д.к. Мастер":
        # Прекращаем выполнение функции process_barcode_card
        await state.clear()
        await balance_discont_card(message, state)
    elif message.text == "Главное меню":
        await state.clear()
        await general_menu(message, state)
    elif message.text == f'/{config.COMMAND}':
        await state.clear()
        await general_menu_marketing(message, state)
    elif  message.text == "Поиск товра":
        await state.clear()
        await product_search(message, state, bot)
    elif  message.text == "Задать вопрос оператору":
        await state.clear()
        await ask_question(message, state)
    elif message.text == "Ответить на вопросы":
        await state.clear()
        await answer_question(message, state)
    else:
        # Передача управления в функцию process_bot.process_barcode_card
        await process_bot.process_added_card(message, state, bot)

# Обработчик команды ""Баланс д.к. Мастер""
@form_router.message(F.text == "Баланс д.к. Мастер")
async def balance_discont_card_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Баланс д.к. Мастер".
    Вызывает функцию balance_discont_card для просмотра баланса дисконтной карты.

    :param message: Объект сообщения пользователя, содержащий команду "Баланс д.к. Мастер".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции balance_discont_card_wrapper")
    await balance_discont_card(message, state)

#-----------------------------------------------------------КОНЕЦ МЕНЮ ДИСКОНТНОЙ КАРТЫ------------------------------------------------------------------------------------------#
#--------------------------------------------------------КОНЕЦ УПРАВЛЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ--------------------------------------------------------------------------------------#


#-------------------------------------------------------------УПРАВЛЕНИЕ МАРКЕТИНГОМ---------------------------------------------------------------------------------------------#

#-----------------------------------------------------------------МЕНЮ МАРКЕТИНГА------------------------------------------------------------------------------------------------#

# Обработчик команды, определенной в config.COMMAND
@form_router.message(Command(config.COMMAND))
async def general_menu_marketing_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды, определенной в config.COMMAND.
    Вызывает функцию general_menu_marketing для отображения главного меню маркетинга.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции general_menu_marketing_wrapper")
    await general_menu_marketing(message, state)

# Обработчик команды "Меню маркетинга"
@form_router.message(F.text == "Меню маркетинга")
async def menu_marketing_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Меню маркетинга".
    Вызывает функцию menu_marketing для отображения меню маркетинга.

    :param message: Объект сообщения пользователя, содержащий команду "Меню маркетинга".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции menu_marketing_wrapper")
    await menu_marketing(message, state)

#--------------------------------------------------------------КОНЕЦ МЕНЮ МАРКЕТИНГА---------------------------------------------------------------------------------------------#


#------------------------------------------------------------------МЕНЮ СТАТИСТИКИ-----------------------------------------------------------------------------------------------#

# Обработчик команды Меню статистики
@form_router.message(F.text == "Меню статистики")
async def menu_statistic_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Меню статистики".
    Вызывает функцию menu_statistic для отображения меню статистики.

    :param message: Объект сообщения пользователя, содержащий команду "Меню статистики".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции menu_statistic_wrapper")
    await menu_statistic(message, state)

# Обработчик команды "Клики"
@form_router.message(F.text == "Клики")
async def stats_click_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Клики".
    Вызывает функцию stats_click для отображения статистики по кликам.

    :param message: Объект сообщения пользователя, содержащий команду "Клики".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stats_click_wrapper")
    await stats_click(message, state)

# Обработчик команды Запуск бота
@form_router.message(F.text == "Запуск бота")
async def stats_start_bot_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Запуск бота".
    Вызывает функцию stats_start_bot для отображения статистики по запускам бота.

    :param message: Объект сообщения пользователя, содержащий команду "Запуск бота".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stats_start_bot_wrapper")
    await stats_start_bot(message, state)

# Обработчик команды Нажатия на кнопки
@form_router.message(F.text == "Нажатия на кнопки")
async def click_button_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Нажатия на кнопки".
    Вызывает функцию click_button_stat для отображения статистики по нажатиям на кнопки.

    :param message: Объект сообщения пользователя, содержащий команду "Нажатия на кнопки".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции click_button_stat_wrapper")
    await click_button_stat(message, state)

# Обработчик команды "Активность"
@form_router.message(F.text == "Активность")
async def stats_activity_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Активность".
    Вызывает функцию stats_activity для отображения статистики по активности пользователей.

    :param message: Объект сообщения пользователя, содержащий команду "Активность".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stats_activity_wrapper")
    await stats_activity(message, state)

# Обработчик команды "Без карты"
@form_router.message(F.text == "Без карты")
async def activity_not_card_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Без карты".
    Вызывает функцию activity_not_card_stat для отображения статистики
    по активности пользователей без карты.

    :param message: Объект сообщения пользователя, содержащий команду "Без карты".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции activity_not_card_stat_wrapper")
    await activity_not_card_stat(message, state)

# Обработчик команды "С картой"
@form_router.message(F.text == "С картой")
async def activity_card_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "С картой".
    Вызывает функцию activity_card_stat для отображения статистики
    по активности пользователей с картой.

    :param message: Объект сообщения пользователя, содержащий команду "С картой".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции activity_card_stat_wrapper")
    await activity_card_stat(message, state)

# Обработчик команды "Публикации"
@form_router.message(F.text == "Публикации")
async def stats_posts_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Публикации".
    Вызывает функцию stats_posts для отображения статистики по публикациям.

    :param message: Объект сообщения пользователя, содержащий команду "Публикации".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stats_posts_wrapper")
    await stats_posts(message, state)

# Обработчик команды "Последняя"
@form_router.message(F.text == "Последняя")
async def last_post_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Последняя".
    Отправляет статистику по последней публикации отправленной пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Последняя".
    :param state: Объект состояния пользователя.
    :return: None
    """
    # Нужна реализация отслеживания последней акции отправленной пользователям по группам и без
    await state.clear()
    logger.info(
        "Пользователь id = %s name = %s вызвал команду - Последняя",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        await message.answer("Эта функция находится в разработке.")
    else:

        logger.warning(
            "Пользователю id = %s name = %s отказано в достпупе команды - Последняя, "
            "так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

# Обработчик команды "Популярные"
@form_router.message(F.text == "Популярные")
async def poppular_posts_stat(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Популярные".
    Отправляет статистику по популярным публикациям в боте.

    :param message: Объект сообщения пользователя, содержащий команду "Популярные".
    :param state: Объект состояния пользователя.
    :return: None
    """
    # Нужна реализация отслеживания популярных акций пользователям
    await state.clear()
    logger.info(
        "Пользователь id = %s name = %s вызвал команду - Популярные",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        await message.answer("Эта функция находится в разработке.")
    else:
        logger.warning(
            "Пользователю id = %s name = %s отказано в достпупе команды - "
            "Популярные, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

# Обработчик команды "Всего публикаций"
@form_router.message(F.text == "Всего публикаций")
async def all_posts_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всего публикаций".
    Вызывает функцию all_posts_stat для отображения статистики по всем публикациям.

    :param message: Объект сообщения пользователя, содержащий команду "Всего публикаций".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_posts_stat_wrapper")
    await all_posts_stat(message, state)

# Обработчик команды "Пользователи"
@form_router.message(F.text == "Пользователи")
async def stats_users_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Пользователи".
    Вызывает функцию stats_users для отображения статистики по пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Пользователи".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stats_users_wrapper")
    await stats_users(message, state)

# Обработчик команды "Всего пользователей"
@form_router.message(F.text == "Всего пользователей")
async def all_users_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всего пользователей".
    Вызывает функцию all_users_stat для отображения статистики по всем пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Всего пользователей".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_users_stat_wrapper")
    await all_users_stat(message, state)

# Обработчик команды "Без программы"
@form_router.message(F.text == "Без программы")
async def all_users_not_card_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Без программы".
    Вызывает функцию all_users_not_card_stat для отображения
    статистики по пользователям без программы.

    :param message: Объект сообщения пользователя, содержащий команду "Без программы".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_users_not_card_stat_wrapper")
    await all_users_not_card_stat(message, state)

# Обработчик команды "По программе"
@form_router.message(F.text == "По программе")
async def all_users_card_stat_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "По программе".
    Вызывает функцию all_users_card_stat для отображения статистики по пользователям по программе.

    :param message: Объект сообщения пользователя, содержащий команду "По программе".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_users_card_stat_wrapper")
    await all_users_card_stat(message, state)

# Обработчик команды "Заблокирован"
@form_router.message(F.text == "Заблокирован")
async def bot_ban_stat_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "Заблокирован".
    Вызывает функцию bot_ban_stat для отображения статистики по заблокированным пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Заблокирован".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции bot_ban_stat_wrapper")
    await bot_ban_stat(message, state, bot)

# Обработчик команды "Запросы"
@form_router.message(F.text == "Запросы")
async def stats_search_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Запросы".
    Вызывает функцию stats_search для отображения статистики по запросам.

    :param message: Объект сообщения пользователя, содержащий команду "Запросы".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stats_search_wrapper")
    await stats_search(message, state)

# Обработчик команды "Всего запросов"
@form_router.message(F.text == "Всего запросов")
async def all_requests_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всего запросов".
    Вызывает функцию all_requests для отображения статистики по всем запросам.

    :param message: Объект сообщения пользователя, содержащий команду "Всего запросов".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_requests_wrapper")
    await all_requests(message, state)

# Обработчик команды "Самые частые"
@form_router.message(F.text == "Самые частые")
async def popular_requests_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Самые частые".
    Вызывает функцию popular_requests для отображения статистики по самым частым запросам.

    :param message: Объект сообщения пользователя, содержащий команду "Самые частые".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции popular_requests_wrapper")
    await popular_requests(message, state)

# Обработчик команды "Кол-во по слову"
@form_router.message(F.text == "Кол-во по слову")
async def all_requests_to_word_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Кол-во по слову".
    Вызывает функцию all_requests_to_word для отображения статистики по запросам по слову.

    :param message: Объект сообщения пользователя, содержащий команду "Кол-во по слову".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_requests_to_word_wrapper")
    await all_requests_to_word(message, state)

# Обработчик команды "Кол-во по штрихкоду"
@form_router.message(F.text == "Кол-во по штрихкоду")
async def all_requests_to_barcode_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Кол-во по штрихкоду".
    Вызывает функцию all_requests_to_barcode для отображения статистики по запросам по штрихкоду.

    :param message: Объект сообщения пользователя, содержащий команду "Кол-во по штрихкоду".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_requests_to_barcode_wrapper")
    await all_requests_to_barcode(message, state)

# Обработчик команды "Кол-во по штрихкоду"
@form_router.message(F.text == "Кол-во по коду товра")
async def all_requests_to_code_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Кол-во по коду товара".
    Вызывает функцию all_requests_to_code для отображения статистики по запросам по коду товара.

    :param message: Объект сообщения пользователя, содержащий команду "Кол-во по коду товара".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции all_requests_to_code_wrapper")
    await all_requests_to_code(message, state)

# Обработчик команды "Часы активности"
@form_router.message(F.text == "Часы активности")
async def time_search_popular_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Часы активности".
    Вызывает функцию time_search_popular для отображения статистики по часам активности.

    :param message: Объект сообщения пользователя, содержащий команду "Часы активности".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции time_search_popular_wrapper")
    await time_search_popular(message, state)

# Обработчик команды "Вся статистика"
@form_router.message(F.text == "Вся статистика")
async def stats_all_wrapper(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды "Вся статистика".
    Вызывает функцию stats_all для вывода файла всей статистики.

    :param message: Объект сообщения пользователя, содержащий команду "Вся статистика".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :param bot: Объект бота для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции stats_all_wrapper")
    await stats_all(message, state, bot)

#-------------------------------------------------------------КОНЕЦ МЕНЮ СТАТИСТИКИ----------------------------------------------------------------------------------------------#


#------------------------------------------------------------------МЕНЮ РАССЫЛКИ-------------------------------------------------------------------------------------------------#

# Обработчик команды Меню рассылки
@form_router.message(F.text == "Меню рассылки")
async def sending_out_advertisements_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Меню рассылки".
    Вызывает функцию sending_out_advertisements для отображения меню рассылки.

    :param message: Объект сообщения пользователя, содержащий команду "Меню рассылки".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции sending_out_advertisements_wrapper")
    await sending_out_advertisements(message, state)

# Обработчик команды "Рассылка всем"
@form_router.message(F.text == "Рассылка всем")
async def send_advertisements_all_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Рассылка всем".
    Вызывает функцию send_advertisements_all для начала рассылки всем пользователям.

    :param message: Объект сообщения пользователя, содержащий команду "Рассылка всем".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции send_advertisements_all_wrapper")
    await send_advertisements_all(message, state)

# Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_all
@form_router.message(FormSendingAdv.send_all)
async def process_send_advertisements_all_wrapper(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_all.
    Передает управление в функцию process_bot.process_send_advertisements_all
    для дальнейшей обработки акции для рассылки всем пользователям.

    :param message: Объект сообщения пользователя, содержащий акцию для рассылки.
    :param state: Объект состояния пользователя.
    :param bot: Экземпляр бота, используемый для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_send_advertisements_all_wrapper")
    actions = {
        "Семейная": send_advertisements_family,
        "Домовёнок": send_advertisements_home,
        "Мастер": send_advertisements_master,
        "Семейная+Домовёнок": send_advertisements_family_and_home,
        "Всем кроме Мастер": send_all_without_master,
        "Меню маркетинга": menu_marketing,
        "Главное меню": general_menu
    }

    action = actions.get(message.text)
    if action:
        await state.clear()
        await action(message, state)
    else:
        # Передача управления в функцию process_bot.process_send_advertisements_all
        await process_bot.process_send_advertisements_all(message, state, bot)

# Обработчик команды "Семейная"
@form_router.message(F.text == "Семейная")
async def send_advertisements_family_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Семейная".
    Вызывает функцию send_advertisements_family для начала рассылки
    пользователям с картой "Семейная".

    :param message: Объект сообщения пользователя, содержащий команду "Семейная".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции send_advertisements_family_wrapper")
    await send_advertisements_family(message, state)

# Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_family
@form_router.message(FormSendingAdv.send_family)
async def process_send_advertisements_family_wrapper(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_family.
    Передает управление в функцию process_bot.process_send_advertisements_family
    для дальнейшей обработки акции для рассылки пользователям с картой "Семейная".

    :param message: Объект сообщения пользователя, содержащий акцию для рассылки.
    :param state: Объект состояния пользователя.
    :param bot: Экземпляр бота, используемый для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_send_advertisements_family_wrapper")
    actions = {
        "Рассылка всем": send_advertisements_all,
        "Домовёнок": send_advertisements_home,
        "Мастер": send_advertisements_master,
        "Семейная+Домовёнок": send_advertisements_family_and_home,
        "Всем кроме Мастер": send_all_without_master,
        "Меню маркетинга": menu_marketing,
        "Главное меню": general_menu
    }

    action = actions.get(message.text)
    if action:
        await state.clear()
        await action(message, state)
    else:
        #Передача управления в функцию process_bot.process_send_advertisements_family
        await process_bot.process_send_advertisements_family(message, state, bot)

# Обработчик команды "Мастер"
@form_router.message(F.text == "Мастер")
async def  send_advertisements_master_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Мастер".
    Вызывает функцию send_advertisements_master для начала рассылки пользователям с картой "Мастер".

    :param message: Объект сообщения пользователя, содержащий команду "Мастер".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции send_advertisements_master_wrapper")
    await send_advertisements_master(message, state)

# Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_master
@form_router.message(FormSendingAdv.send_master)
async def process_send_advertisements_master_wrapper(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_master.
    Передает управление в функцию process_bot.process_send_advertisements_master
    для дальнейшей обработки акции для рассылки пользователям с картой "Мастер".

    :param message: Объект сообщения пользователя, содержащий акцию для рассылки.
    :param state: Объект состояния пользователя.
    :param bot: Экземпляр бота, используемый для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_send_advertisements_master_wrapper")
    actions = {
        "Рассылка всем": send_advertisements_all,
        "Домовёнок": send_advertisements_home,
        "Семейная": send_advertisements_family,
        "Семейная+Домовёнок": send_advertisements_family_and_home,
        "Всем кроме Мастер": send_all_without_master,
        "Меню маркетинга": menu_marketing,
        "Главное меню": general_menu
    }

    action = actions.get(message.text)
    if action:
        await state.clear()
        await action(message, state)
    else:
        # Передача управления в функцию process_bot.process_send_advertisements_master
        await process_bot.process_send_advertisements_master(message, state, bot)

# Обработчик команды "Домовёнок"
@form_router.message(F.text == "Домовёнок")
async def  send_advertisements_home_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Домовёнок".
    Вызывает функцию send_advertisements_home для начала рассылки
    пользователям с картой "Домовёнок".

    :param message: Объект сообщения пользователя, содержащий команду "Домовёнок".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции send_advertisements_home_wrapper")
    await  send_advertisements_home(message, state)

# Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_home
@form_router.message(FormSendingAdv.send_home)
async def process_send_advertisements_home_wrapper(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_home.
    Передает управление в функцию process_bot.process_send_advertisements_home для 
    дальнейшей обработки акции для рассылки пользователям с картой "Домовёнок".

    :param message: Объект сообщения пользователя, содержащий акцию для рассылки.
    :param state: Объект состояния пользователя.
    :param bot: Экземпляр бота, используемый для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_send_advertisements_home_wrapper")
    actions = {
        "Рассылка всем": send_advertisements_all,
        "Мастер": send_advertisements_master,
        "Семейная": send_advertisements_family,
        "Семейная+Домовёнок": send_advertisements_family_and_home,
        "Всем кроме Мастер":send_all_without_master,
        "Меню маркетинга": menu_marketing,
        "Главное меню": general_menu
    }

    action = actions.get(message.text)
    if action:
        await state.clear()
        await action(message, state)
    else:
        # Передача управления в функцию process_bot.process_send_advertisements_home
        await process_bot.process_send_advertisements_home(message, state, bot)

# Обработчик команды "Семейная+Домовёнок"
@form_router.message(F.text == "Семейная+Домовёнок")
async def  send_advertisements_family_and_home_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Семейная+Домовёнок".
    Вызывает функцию send_advertisements_family_and_home для начала рассылки
    пользователям с картами "Семейная" и "Домовёнок".

    :param message: Объект сообщения пользователя, содержащий команду "Семейная+Домовёнок".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции send_advertisements_family_and_home_wrapper")
    await send_advertisements_family_and_home(message, state)

# Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_family_and_home
@form_router.message(FormSendingAdv.send_family_and_home)
async def process_send_advertisements_family_and_home_wrapper(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Обработчик сообщений, когда пользователь находится в состоянии
    FormSendingAdv.send_family_and_home.
    Передает управление в функцию process_bot.process_send_advertisements_family_and_home
    для дальнейшей обработки акции для рассылки пользователям с картами "Семейная"и"Домовёнок".

    :param message: Объект сообщения пользователя, содержащий акцию для рассылки.
    :param state: Объект состояния пользователя.
    :param bot: Экземпляр бота, используемый для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_send_advertisements_family_and_home_wrapper")
    actions = {
        "Рассылка всем": send_advertisements_all,
        "Мастер": send_advertisements_master,
        "Семейная": send_advertisements_family,
        "Домовёнок": send_advertisements_home,
        "Всем кроме Мастер":send_all_without_master,
        "Меню маркетинга": menu_marketing,
        "Главное меню": general_menu
    }

    action = actions.get(message.text)
    if action:
        await state.clear()
        await action(message, state)
    else:
        # Передача управления в функцию process_bot.process_send_advertisements_home
        await process_bot.process_send_advertisements_family_and_home(message, state, bot)

# Обработчик команды "Всем кроме Мастер"
@form_router.message(F.text == "Всем кроме Мастер")
async def  send_all_without_master_wrapper(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Всем кроме Мастер".
    Вызывает функцию send_all_without_master для начала рассылки
    всем пользователям, кроме тех, у кого есть карта "Мастер".

    :param message: Объект сообщения пользователя, содержащий команду "Всем кроме Мастер".
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции send_all_without_master_wrapper")
    await send_all_without_master(message, state)

# Обработчик сообщений, когда пользователь находится в состоянии FormSendingAdv.send_family_and_home
@form_router.message(FormSendingAdv.send_all_withot_master)
async def process_send_all_without_master_wrapper(
    message: Message,
    state: FSMContext,
    bot: Bot
    ) -> None:
    """
    Обработчик сообщений, когда пользователь находится в
    состоянии FormSendingAdv.send_family_and_home.
    Передает управление в функцию process_bot.process_send_advertisements_family_and_home
    для дальнейшей обработки акции для рассылки пользователям с картами "Семейная"и"Домовёнок".

    :param message: Объект сообщения пользователя, содержащий акцию для рассылки.
    :param state: Объект состояния пользователя.
    :param bot: Экземпляр бота, используемый для взаимодействия с Telegram API.
    :return: None
    """
    logger.info("Выполнение функции process_send_all_without_master_wrapper")
    actions = {
        "Рассылка всем": send_advertisements_all,
        "Мастер": send_advertisements_master,
        "Семейная": send_advertisements_family,
        "Домовёнок": send_advertisements_home,
        "Семейная+Домовёнок": send_advertisements_family_and_home,
        "Меню маркетинга": menu_marketing,
        "Главное меню": general_menu
    }

    action = actions.get(message.text)
    if action:
        await state.clear()
        await action(message, state)
    else:
        # Передача управления в функцию process_bot.process_send_advertisements_home
        await process_bot.process_send_all_without_master(message, state, bot)


#---------------------------------------------------------------КОНЕЦ МЕНЮ РАССЫЛКИ----------------------------------------------------------------------------------------------#   
#----------------------------------------------------------КОНЕЦ УПРАВЛЕНИЯ МАРКЕТИНГОМ------------------------------------------------------------------------------------------#

#------------------------------------------------------------------МЕНЮ УПРАВЛЕНИЯ-----------------------------------------------------------------------------------------------#
@form_router.message(Command(config.COMMAND_STOP))
async def stop_bot_gemma(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды остановки бота.
    Останавливает бота, если пользователь имеет права администратора.

    :param message: Объект сообщения пользователя, содержащий команду остановки бота.
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции stop_bot_gemma")
    if message.from_user.id in config.USER_GENERAL_ADMIN:
        await message.answer("Бот остановлен")
        logger.info(
            "Пользователю id = %s name = %s вызвал команду - %s и остановил бот",
            message.from_user.id, message.from_user.full_name, config.COMMAND_STOP
            )
        await dp.stop_polling()
    else:
        logger.warning(
            "Пользователю id = %s name = %s отказано в достпупе команды - %s, "
            "так как его нет в config.USER_GENERAL_ADMIN",
            message.from_user.id, message.from_user.full_name, config.COMMAND_STOP
            )
        await state.clear()
        await general_menu(message, state)

@form_router.message(Command(config.COMMAND_BACKUP))
async def backup_bot(message: Message, state: FSMContext, bot: Bot) -> None:
    """
    Обработчик команды создания резервной копии данных бота.
    Создает резервные копии баз данных и отправляет их пользователю,
    если он имеет права администратора.

    :param message: Объект сообщения пользователя, содержащий команду создания резервной копии.
    :param state: Состояние конечного автомата для управления диалогом с пользователем.
    :return: None
    """
    logger.info("Выполнение функции backup_bot")
    if message.from_user.id in config.USER_GENERAL_ADMIN:
        await message.answer("Отправляю вам базы данных и другие файлы для восстановления.")
        logger.info(
            "Пользователю id = %s name = %s вызвал команду - %s",
            message.from_user.id, message.from_user.full_name, config.COMMAND_BACKUP
            )
        # Создание резервной копии базы данных
        backup_path_1 = await create_backup('data/statisctics/message_database.db')
        backup_path_2 = await create_backup('data/statisctics/user_database.db')
        backup_path_3 = await create_backup('data/user_data_json/user_id_and_username.json')
        backup_path_4 = await create_backup('data/user_data_json/user_id_and_number_card_master.json')
        backup_path_5 = await create_backup('data/user_data_json/user_id_to_discont_card.json')

        async with aiofiles.open(backup_path_1, 'rb') as backup_file:
            file_data = await backup_file.read()

        async with aiofiles.open(backup_path_2, 'rb') as backup_file2:
            file_data2 = await backup_file2.read()

        async with aiofiles.open(backup_path_3, 'rb') as backup_file3:
            file_data3 = await backup_file3.read()

        async with aiofiles.open(backup_path_4, 'rb') as backup_file4:
            file_data4 = await backup_file4.read()

        async with aiofiles.open(backup_path_5, 'rb') as backup_file5:
            file_data5 = await backup_file5.read()

        db_file = BufferedInputFile(file_data, filename=backup_path_1)
        db_file2 = BufferedInputFile(file_data2, filename=backup_path_2)
        db_file3 = BufferedInputFile(file_data3, filename=backup_path_3)
        db_file4 = BufferedInputFile(file_data4, filename=backup_path_4)
        db_file5 = BufferedInputFile(file_data5, filename=backup_path_5)

        await bot.send_document(chat_id=message.chat.id, document=db_file)
        await bot.send_document(chat_id=message.chat.id, document=db_file2)
        await bot.send_document(chat_id=message.chat.id, document=db_file3)
        await bot.send_document(chat_id=message.chat.id, document=db_file4)
        await bot.send_document(chat_id=message.chat.id, document=db_file5)

        os.remove(backup_path_1)
        os.remove(backup_path_2)
        os.remove(backup_path_3)
        os.remove(backup_path_4)
        os.remove(backup_path_5)
    else:
        logger.warning(
            "Пользователю id = %s name = %s отказано в достпупе команды - %s, "
            "так как его нет в config.USER_GENERAL_ADMIN", 
            message.from_user.id, message.from_user.full_name, config.COMMAND_BACKUP
            )
        await state.clear()
        await general_menu(message, state)

async def create_backup(db_path: str) -> str:
    """
    Создает резервную копию указанного файла.

    :param db_path: Путь к файлу, для которого нужно создать резервную копию.
    :return: Путь к созданной резервной копии.
    """
    logger.info("Выполнение функции create_backup")
    # Получение базового имени файла базы данных без пути
    db_basename = os.path.basename(db_path)

    # Формирование имени файла бэкапа
    backup_name = (
        f"backup_{db_basename}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}"
        f"{os.path.splitext(db_path)[1]}"
        )
    backup_path = os.path.join('data/backups', backup_name)

    # Создание директории для бэкапов, если ее нет
    os.makedirs('data/backups', exist_ok=True)

    # Копирование файла базы данных
    if db_path.endswith('.db'):
        # Для SQLite баз данных, используем shutil.copyfile, который асинхронный в Python
        shutil.copyfile(db_path, backup_path)
    else:
        # Для JSON файлов, используем shutil.copyfile, который асинхронный в Python
        shutil.copyfile(db_path, backup_path)

    return backup_path

@form_router.message(Command(config.COMMAND_RESTART_BOT_MESSAGE))
async def send_restart_bot(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды уведомления о перезапуске бота.
    Отправляет уведомление о необходимости перезапуска бота,
    если пользователь имеет права администратора.

    :param message: Объект сообщения пользователя, содержащий
    команду уведомления о перезапуске бота.
    :param state: Состояние конечного автомата для управления
    диалогом с пользователем.
    
    :return: None
    """
    logger.info("Выполнение функции send_restart_bot")
    if message.from_user.id in config.USER_GENERAL_ADMIN:
        await message.answer(
            "Здравствуйте. Мы внесли изменения в функционал бота. "
            "Чтобы пользоваться дальше ботом, нажмите кнопку 'Перезапустить бот'."
            )
    else:
        logger.warning(
            "Пользователю id = %s name = %s отказано в достпупе команды - %s, "
            "так как его нет в config.USER_GENERAL_ADMIN", 
            message.from_user.id,
            message.from_user.full_name,
            config.COMMAND_RESTART_BOT_MESSAGE
            )
        await state.clear()
        await general_menu(message, state)
#---------------------------------------------------------------КОНЕЦ МЕНЮ УПРАВЛЕНИЯ--------------------------------------------------------------------------------------------# 

#-----------------------------------------------------------------МЕНЮ ЗАПУСКА БОТА----------------------------------------------------------------------------------------------# 

async def main():
    """
    Основная функция запуска бота.
    Запускает бота в режиме опроса (polling) для получения обновлений от Telegram.
    """
    logger.info("Запуск бота")
    await dp.start_polling(gemma_bot)

if __name__ == "__main__":
    # Запуск асинхронного цикла событий
    asyncio.run(main())
