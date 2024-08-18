"""
Модуль menus содержит функции-обработчики для управления меню и
взаимодействия с пользователями в Telegram-боте. Эти функции
обеспечивают отправку различных меню и клавиатур пользователям,
а также обработку команд, связанных с управлением ботом и
отображением статистики.
"""
import logging
from logging.handlers import RotatingFileHandler

from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from src.utils.read_json import read_json_file, update_json_file
from configs import config


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/menus_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('menus_logger')
logger.addHandler(file_handler)


async def start_bot(message: Message) -> None:
    """
    Обработчик команды "/start".
    Отправляет приветственное сообщение пользователю и обновляет JSON-файл с данными пользователя.

    :param message: Объект сообщения пользователя, содержащий команду "/start".
    :return: None
    """
    logger.info(
        "В функции start_bot Пользователь id = %s name = %s "
        "вызвал команду  - /start", 
        message.from_user.id, message.from_user.full_name
        )

    #обработка данных пользователя для рассылки
    from_user_id = str(message.from_user.id)
    from_user_full_name = message.from_user.full_name
    user_data = {from_user_id:from_user_full_name}
    filename = 'data/user_data_json/user_id_and_username.json'

    await update_json_file(user_data, filename)

    filename = 'data/user_data_json/user_id_to_discont_card.json'
    check_data_master = await read_json_file(filename)
    if (
        message.from_user.id in check_data_master['Р00000002'] and
        message.from_user.id != int(config.OPERATOR_ID)
        ):
        kb = [
            [KeyboardButton(text="Поиск товара"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Посетить магазин"),
            ],
            [KeyboardButton(text="Дисконтная карта"),
             KeyboardButton(text="Баланс д.к. Мастер"),],
            [KeyboardButton(text="Задать вопрос оператору"),],
            [KeyboardButton(text="Перезапустить бот"),],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "<b>Вы в главном меню.</b>\n"
            "- Чтобы искать товары по названию, коду товара, "
            "штрихкоду, нажмите - <b>'Поиск товара'</b>.\n"
            "- Чтобы узнать, что я могу, нажмите - <b>'Информация'</b>.\n"
            "- Чтобы узнать баланс по вашей карте, нажмите - <b>'Узнать баланс'</b>.\n"
            "- Чтобы посетить сайт магазина, нажмите - <b>'Посетить магазин'</b>.\n"
            "- Чтобы добавить свою дисконтную карту, нажмите - <b>'Дисконтная карта'</b>.\n"
            "- Чтобы задать вопрос оператору, нажмите - <b>'Задать вопрос оператору'</b>.\n"
            "- Чтобы перезапустить бот, нажмите - <b>'Перезапустить бот'</b>.\n",
            reply_markup=keyboard
        )
    elif message.from_user.id == int(config.OPERATOR_ID):
        kb = [
            [KeyboardButton(text="Поиск товара"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Посетить магазин"),
            ],
            [KeyboardButton(text="Дисконтная карта"),],
            [KeyboardButton(text="Ответить на вопросы"),],
            [KeyboardButton(text="Перезапустить бот"),],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "<b>Вы в главном меню.</b>\n"
            "- Чтобы искать товары по названию, коду товара, "
            "штрихкоду, нажмите - <b>'Поиск товара'</b>.\n"
            "- Чтобы узнать, что я могу, нажмите - <b>'Информация'</b>.\n"
            "- Чтобы посетить сайт магазина, нажмите - <b>'Посетить магазин'</b>.\n"
            "- Чтобы добавить свою дисконтную карту, нажмите - <b>'Дисконтная карта'</b>.\n"
            "- Чтобы ответить на вопросы пользователей, нажмите - <b>'Ответить на вопросы'</b>.\n"
            "- Чтобы перезапустить бот, нажмите - <b>'Перезапустить бот'</b>.\n",
            reply_markup=keyboard
        )
    else:
        kb = [
            [KeyboardButton(text="Поиск товара"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Посетить магазин"),
            ],
            [KeyboardButton(text="Дисконтная карта"),
             KeyboardButton(text="Задать вопрос оператору"),],
            [KeyboardButton(text="Перезапустить бот"),],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "<b>Вы в главном меню.</b>\n"
            "- Чтобы искать товары по названию, коду товара, "
            "штрихкоду, нажмите - <b>'Поиск товара'</b>.\n"
            "- Чтобы узнать, что я могу, нажмите - <b>'Информация'</b>.\n"
            "- Чтобы посетить сайт магазина, нажмите - <b>'Посетить магазин'</b>.\n"
            "- Чтобы добавить свою дисконтную карту, нажмите - <b>'Дисконтная карта'</b>.\n"
            "- Чтобы задать вопрос оператору, нажмите - <b>'Задать вопрос оператору'</b>.\n"
            "- Чтобы перезапустить бот, нажмите - <b>'Перезапустить бот'</b>.\n",
            reply_markup=keyboard
        )

async def general_menu(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Главное меню".
    Отправляет пользователю клавиатуру с основными командами бота.

    :param message: Объект сообщения пользователя, содержащий команду "Главное меню".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции general_menu Пользователь id = %s name = %s "
        "вызвал команду - Главное меню",
        message.from_user.id, message.from_user.full_name
        )
    filename = 'data/user_data_json/user_id_to_discont_card.json'
    check_data_master = await read_json_file(filename)
    if message.from_user.id in check_data_master['Р00000002']:
        kb = [
            [KeyboardButton(text="Поиск товара"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Посетить магазин"),
            ],
            [KeyboardButton(text="Дисконтная карта"),
             KeyboardButton(text="Баланс д.к. Мастер"),],
            [KeyboardButton(text="Задать вопрос оператору"),],
            [KeyboardButton(text="Перезапустить бот"),],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Вы в главном меню.\n",
            reply_markup=keyboard
        )
    elif message.from_user.id == int(config.OPERATOR_ID):
        kb = [
            [KeyboardButton(text="Поиск товара"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Посетить магазин"),
            ],
            [KeyboardButton(text="Дисконтная карта"),],
            [KeyboardButton(text="Ответить на вопросы"),],
            [KeyboardButton(text="Перезапустить бот"),],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Вы в главном меню.\n",
            reply_markup=keyboard
        )
    else:
        kb = [
            [KeyboardButton(text="Поиск товара"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Посетить магазин"),
            ],
            [KeyboardButton(text="Дисконтная карта"),
             KeyboardButton(text="Задать вопрос оператору"),],
            [KeyboardButton(text="Перезапустить бот"),],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
            "Вы в главном меню.\n",
            reply_markup=keyboard
        )

async def general_menu_marketing(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды, определенной в config.COMMAND.
    Отправляет пользователю клавиатуру с меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции general_menu_marketing Пользователь id = %s "
        "name = %s вызвал команду - %s",
        message.from_user.id, message.from_user.full_name, config.COMMAND
        )
    if message.from_user.id in config.USER_ADMIN:
        # Обработка команды для выбора рассылки пользователям
        kb = [[KeyboardButton(text="Меню рассылки"),
            KeyboardButton(text="Меню статистики"),
            KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Меню рассылки' - меню рассылки акций пользователям.\n"
                "'Меню статистики' - статистика по боту.\n"
                "'Главное меню' - вернуться в основное меню бота.\n",
                reply_markup=keyboard
            )
        logger.info(
            "В функции general_menu_marketing Пользователь id = %s name = %s "
            "вызвал команду %s",
            message.from_user.id, message.from_user.full_name, config.COMMAND
            )
    else:
        logger.warning(
            "В функции general_menu_marketing Пользователю id = %s name = %s "
            "отказано в достпупе команды - %s, так как его нет в %s",
            message.from_user.id, message.from_user.full_name,
            config.COMMAND, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def menu_marketing(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Меню маркетинга".
    Отправляет пользователю клавиатуру с кнопками для выбора
    типа рассылки и возврата в главное меню.

    :param message: Объект сообщения пользователя, содержащий команду "Меню маркетинга".
    :param state: Объект состояния пользователя.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции menu_marketing Пользователь id = %s name = %s "
        "вызвал команду - Меню маркетинга", 
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Меню рассылки"),
            KeyboardButton(text="Меню статистики"),
            KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Меню рассылки' - меню рассылки акций пользователям.\n"
                "'Меню статистики' - статистика по боту.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )
    else:
        logger.warning(
            "В функции menu_marketing Пользователю id = %s name = %s "
            "отказано в достпупе команды - Меню маркетинга, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def menu_statistic(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Меню статистики".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции menu_statistic Пользователь id = %s name = %s "
        "вызвал команду - Меню статистики",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Клики"),
            KeyboardButton(text="Активность"),
            KeyboardButton(text="Публикации"),],
            [KeyboardButton(text="Пользователи"),
            KeyboardButton(text="Запросы"),
            KeyboardButton(text="Вся статистика"),],
            [KeyboardButton(text="Меню маркетинга")],
            [KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Клики' - меню статистики по кликам.\n"
                "'Активность' - меню статистики по активности.\n"
                "'Публикации' - меню статистики по публикациям.\n"
                "'Пользователи' - меню статистики по пользователям.\n"
                "'Запросы' - меню статистики по поисковым запросам.\n"
                "'Вся статистика' - выгрузить файл всей статистики, которую собирает бот.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )
    else:
        logger.warning(
            "В функции menu_statistic Пользователю id = %s name = %s "
            "отказано в достпупе команды - Меню статистики, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def stats_click(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Клики".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_click Пользователь id = %s name = %s "
        "вызвал команду - Клики",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Запуск бота"),
            KeyboardButton(text="Нажатия на кнопки"),],
            [KeyboardButton(text="Меню статистики"),
             KeyboardButton(text="Меню маркетинга")],
            [KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Запуск бота' - количество запусков бота\n"
                "'Нажатия на кнопки' - статистика по количесвту нажатий на кнопки\n"
                "'Меню статистики' - вернуться в меню статистики с вариантами меню.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )

    else:
        logger.warning(
            "В функции stats_click Пользователю id = %s name = %s "
            "отказано в достпупе команды - Клики, так как его нет в %s", 
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def stats_activity(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Активность".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_activity Пользователь id = %s name = %s "
        "вызвал команду - Активность", 
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Без карты"),
            KeyboardButton(text="С картой"),],
            [KeyboardButton(text="Меню статистики"),
             KeyboardButton(text="Меню маркетинга")],
            [KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Без карты' - активность юзеров без карты.\n"
                "'С картой' - активность юзеров с картой, по видам карт.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Меню статистики' - вернуться в меню статистики с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )
    else:
        logger.warning(
            "В функции stats_activity Пользователю id = %s name = %s "
            "отказано в достпупе команды - Активность, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def stats_posts(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Публикации".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_posts Пользователь id = %s name = %s "
        "вызвал команду - Публикации",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Последняя"),
            KeyboardButton(text="Популярные"),
            KeyboardButton(text="Всего публикаций"),],
            [KeyboardButton(text="Меню статистики"),
             KeyboardButton(text="Меню маркетинга")],
            [KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Последняя' - статистика по последней публикации.\n"
                "'Популярные' - самые популярные публикации.\n"
                "'Всего публикаций' - количесвто публикаций всего по картам.\n"
                "'Меню статистики' - вернуться в меню статистики с вариантами меню.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )
    else:
        logger.warning(
            "В функции stats_posts Пользователю id = %s name = %s "
            "отказано в достпупе команды - Публикации, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def stats_users(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Пользователи".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_users Пользователь id = %s name = %s "
        "вызвал команду - Пользователи",
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Всего пользователей"),
            KeyboardButton(text="По программе"),
            KeyboardButton(text="Без программы"),],
            [KeyboardButton(text="Заблокирован"),],
            [KeyboardButton(text="Меню статистики"),
             KeyboardButton(text="Меню маркетинга")],
            [KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Всего пользователей' - количество всего пользователей\n"
                "'По программе' - количество пользователей имеющих дисконтную "
                "карту (по видам карт).\n"
                "'Без программы' - количество пользователей не имеющих дисконтную карту.\n"
                "'Заблокирован' - узнать у скольких пользователей бот заблокирован.\n"
                "'Меню статистики' - вернуться в меню статистики с вариантами меню.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )
    else:
        logger.warning(
            "В функции stats_users Пользователю id = %s name = %s "
            "отказано в достпупе команды - Пользователи, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def stats_search(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Запросы".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции stats_search Пользователь id = %s name = %s "
        "вызвал команду - Запросы", 
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Всего запросов"),
            KeyboardButton(text="Самые частые"),
            KeyboardButton(text="Кол-во по слову")],
            [KeyboardButton(text="Кол-во по штрихкоду"),
            KeyboardButton(text="Кол-во по коду товра"),
            KeyboardButton(text="Часы активности"),],
            [KeyboardButton(text="Меню статистики"),
             KeyboardButton(text="Меню маркетинга")],
            [KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Всего запросов' - количество всего поисковых запросов.\n"
                "'Самые частые' - самые частые запросы.\n"
                "'Кол-во по слову' - количесвто запросов по слову.\n"
                "'Кол-во по штрихкоду' - количество запросов по штрихкоду.\n"
                "'Кол-во по коду товра' - количество запросов по коду.\n"
                "'Часы активности' - время наибольшей активности поисковых запросов "
                "по временным промежуткам в сутках и по дням недели.\n"
                "'Меню статистики' - вернуться в меню статистики с вариантами меню.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм-бота.\n",
                reply_markup=keyboard
            )

    else:
        logger.warning(
            "В функции stats_search Пользователю id = %s name = %s отказано в достпупе "
            "команды - Запросы, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)

async def sending_out_advertisements(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды "Меню рассылки".
    Отправляет пользователю клавиатуру с вариантами рассылки и меню.

    :param message: Объект сообщения пользователя, содержащий команду.
    :param state: Объект состояния.
    :return: None
    """
    await state.clear()
    logger.info(
        "В функции sending_out_advertisements Пользователь id = %s name = %s "
        "вызвал команду - Меню рассылки", 
        message.from_user.id, message.from_user.full_name
        )
    if message.from_user.id in config.USER_ADMIN:
        kb = [[KeyboardButton(text="Рассылка всем"),],
            [KeyboardButton(text="Семейная"),
            KeyboardButton(text="Мастер"),
            KeyboardButton(text="Домовёнок"),],
            [KeyboardButton(text="Семейная+Домовёнок"),
             KeyboardButton(text="Всем кроме Мастер"),],
            [KeyboardButton(text="Меню маркетинга"),
            KeyboardButton(text="Главное меню")],
            ]
        keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

        await message.answer(
                "'Рассылка всем' - все пользователи бота получат сообщение об акции.\n"
                "'Семейная' - сообщение об акции получат только пользователи со "
                "скидочными картами 'Семейная'.\n"
                "'Мастер' - сообщение об акции получат только пользователи со "
                "скидочными картами 'Мастер'.\n"
                "'Домовёнок' - сообщение об акции получат только пользователи со "
                "скидочными картами 'Домовёнок'.\n"
                "'Семейная+Домовёнок' - сообщение об акции получат только пользователи со "
                "скидочными картами 'Семейная+Домовёнок'.\n"
                "'Всем кроме Мастер' - сообщение об акции получат все пользователи кроме "
                "пользователей со скидочными картами 'Мастер'.\n"
                "'Меню маркетинга' - вернуться в меню маркетинга с вариантами меню.\n"
                "'Главное меню' - вернуться в главное меню телеграм_бота.\n",
                reply_markup=keyboard
            )
    else:
        logger.warning(
            "В функции sending_out_advertisements Пользователю id = %s name = %s "
            "отказано в достпупе команды - Меню рассылки, так как его нет в %s",
            message.from_user.id, message.from_user.full_name, config.USER_ADMIN
            )
        await state.clear()
        await general_menu(message, state)
