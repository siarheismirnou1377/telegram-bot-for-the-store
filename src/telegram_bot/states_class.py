"""
Модуль для определения состояний пользователей и форм в приложении.
Этот модуль содержит классы, которые определяют различные состояния пользователей и форм,
используемых в приложении. Каждый класс представляет собой группу состояний, связанных с
определенной функциональностью или процессом.
"""

from aiogram.fsm.state import State, StatesGroup

class UserStates(StatesGroup):
    """
    Класс состояния пользователя.
    """
    privacy_agreement: State = State()

class FormProduct(StatesGroup):
    """
    Класс состояния продукта.
    """
    product: State = State()
    code_product: State = State()

class FormBarcode(StatesGroup):
    """
    Класс состояния штрих-кода.
    """
    photo_barcode: State = State()
    text_barcode: State = State()

class FormDiscontCard(StatesGroup):
    """
    Класс состояния дисконтной карты.
    """
    number_card: State = State()
    photo_card: State = State()
    text_card: State = State()

class FormSendingAdv(StatesGroup):
    """
    Класс состояния рассылки рекламы.
    """
    send_all: State = State()
    send_family: State = State()
    send_master: State = State()
    send_home: State = State()
    send_employee: State = State()
    send_vip: State = State()
    send_family_and_home: State = State()
    send_all_withot_master: State = State()

class FormAsk(StatesGroup):
    """
    Класс состояния вопроса от пользователя.
    """
    ask_question: State = State()
    answer_questions: State = State()
