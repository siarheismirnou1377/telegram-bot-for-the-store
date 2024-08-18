"""
Модуль для работы с штрих-кодами.
Этот модуль предоставляет асинхронные функции для чтения, декодирования,
извлечения и генерации штрих-кодов. Он использует библиотеки OpenCV,
pyzbar, и barcode для выполнения этих задач.
"""

import asyncio
import logging
from io import BytesIO
from logging.handlers import RotatingFileHandler

import aiofiles
import cv2
import numpy as np
from barcode import EAN13, EAN8
from barcode.writer import ImageWriter
from pyzbar import pyzbar


logging.basicConfig(level=logging.INFO)

# Установка размера файла логов в 8 МБ
MAX_BYTES = 8 * 1024 * 1024  # 8 МБ в байтах

# Создание обработчика файлов с ограничением размера и ротацией
file_handler = RotatingFileHandler(
    "logs/barcode_log.log",
    maxBytes=MAX_BYTES,  # Установка максимального размера файла логов
    backupCount=30,  # Количество файлов логов, которые будут храниться
    encoding="utf-8",
)

# Формат сообщений
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger = logging.getLogger('barcode_logger')
logger.addHandler(file_handler)


async def read_image(image_path: str) -> np.ndarray | None:
    """
    Асинхронное чтение изображения с диска.

    :@param image_path: Путь к изображению на диске.
    :return: Объект изображения или None, если чтение не удалось.
    """
    logger.info("Выполнение функции read_image, c полученными данными -%s", image_path)
    loop = asyncio.get_running_loop()
    try:
        logger.info("Попытка чтения read_image изображения по пути - %s", image_path)
        # Используем run_in_executor для асинхронного чтения изображения
        future_result = loop.run_in_executor(None, cv2.imread, image_path)  # pylint: disable=no-member
        image = await future_result
        if image is None:
            logger.info("Не удалось прочитать файл - %s. Возвращено %s", image_path, None)
            return None
        return image
    except Exception as e:
        logger.error("Произошла ошибка при чтении файла: %s", e)
        raise

async def return_barcode(image_path: str) -> str | None:
    """
    Асинхронное декодирование штрих-кода на изображении.

    :param image_path: Путь к изображению на диске.
    :return: Текст штрих-кода или None, если декодирование не удалось.
    """
    logger.info("Выполнение функции return_barcode, c полученными данными - %s", image_path)
    try:
        logger.info("Попытка чтения return_barcode изображения по пути - %s", image_path)
        # Асинхронное чтение изображения
        image = await read_image(image_path)
        if image is None:
            logger.info("Изображение по пути %s = %s", image_path, None)
            return None

        # Преобразование изображения в оттенки серого
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # pylint: disable=no-member

        # Найти штрих-коды и QR-коды на изображении
        barcodes = pyzbar.decode(gray_image)

        # Перебрать обнаруженные штрих-коды
        for barcode in barcodes:
            # Извлечь данные и тип штрих-кода
            barcode_data = barcode.data.decode("utf-8")

            # Вывести информацию о штрих-коде
            text = barcode_data
            logger.info(
                "Получен текст %s штрихкода в return_barcode изображения по пути -  %s",
                text, image_path
                )
            return text

    except Exception as e:
        logger.error("Произошла ошибка в функции return_barcode по пути %s : %s", image_path, e)
        raise e

async def extract_barcode_image(image_path: str) -> str | None:
    """
    Асинхронное извлечение штрих-кода из изображения и
    сохранение изображения с вырезанным штрих-кодом.

    :param image_path: Путь к изображению на диске.
    :return: Путь к сохраненному изображению с вырезанным штрих-кодом или None,
    если извлечение не удалось.
    """
    logger.info("Выполнение функции extract_barcode_image, c полученными данными - %s", image_path)
    try:
        logger.info("Попытка чтения extract_barcode_image изображения по пути -  %s", image_path)
        # Асинхронное чтение изображения
        image = await read_image(image_path)
        if image is None:
            logger.info("Изображение по пути %s = %s", image_path, None)
            return None

        # Преобразование изображения в оттенки серого
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # pylint: disable=no-member

        # Найти штрих-коды и QR-коды на изображении
        barcodes = pyzbar.decode(gray_image)

        # Перебрать обнаруженные штрих-коды
        for barcode in barcodes:
            logger.info(
                "Цикл для переборки обнаруженных штрих-кодов в extract_barcode_image"
                "изображения по пути - %s", image_path
                )
            # Извлечь данные и тип штрих-кода
            barcode_data = barcode.data.decode("utf-8")
            spaced_barcode_data = ' '.join(barcode_data)

            # Получить границы штрих-кода
            (x, y, w, h) = barcode.rect

            # Вырезать штрих-код из изображения
            barcode_image = image[y:y+h, x:x+w]
            # Создать новое изображение с белым фоном
            white_background = np.full((h + 100, w + 100, 3), 255, dtype=np.uint8)

            # Добавить рамку
            cv2.rectangle(white_background, (0, 0), (w + 99, h + 99), (0, 0, 0), 1) # pylint: disable=no-member
            # Вставить вырезанный штрих-код в центр нового изображения
            white_background[50:50+h, 50:50+w] = barcode_image

            # Добавить текст с номером штрих-кода на изображение
            cv2.putText(  # pylint: disable=no-member
                white_background, spaced_barcode_data,
                (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2  # pylint: disable=no-member
                )
            path_img = f'card_{image_path}'
            # Сохранить изображение
            cv2.imwrite(path_img, white_background)  # pylint: disable=no-member
            logger.info(
                "Конец цикла для переборки обнаруженных штрих-кодов в extract_barcode_image "
                "изображения по пути - %s с возвратом пути созданного изображения %s",
                image_path, path_img
                )
            return path_img
    except Exception as e:
        logger.error("Произошла ошибка в функции return_barcode по пути %s: %s", image_path, e)
        raise e

async def generate_barcode(number: str, filename: str) -> None:
    """
    Асинхронное генерирование штрих-кода EAN-8 или EAN-13 и сохранение его в файл.

    :param number: Номер штрих-кода в виде строки.
    :param filename: Путь к файлу, в который будет сохранен штрих-код.
    :raises ValueError: Если длина номера не равна 8 или 13.
    """
    logger.info(
        "Выполнение функции generate_barcode, c полученными данными - %s и %s",
        number, filename
        )
    count = len(number)
    logger.info(
        "Длина %s = %s в generate_barcode, c полученными данными - %s и %s",
        number, count, number, filename
        )
    try:
        if count == 13:
            # Создаем штрих-код EAN-13
            my_code = EAN13(number, writer=ImageWriter())
            logger.info(
                "Длина %s = %s в generate_barcode, c полученными данными - %s и %s "
                "создание штрихкода %s", number, count, number, filename, my_code
                )
            # Сохраняем штрих-код в буфер
            buffer = BytesIO()
            my_code.write(buffer)

            # Перемещаем указатель в начало буфера
            buffer.seek(0)

            # Асинхронно записываем буфер в файл
            async with aiofiles.open(filename, 'wb') as f:
                await f.write(buffer.read())
                logger.info("Штрихкод %s  в generate_barcode, был записан по пути %s", my_code, f)

        elif count == 8:
            # Создаем штрих-код EAN-8
            my_code = EAN8(number, writer=ImageWriter())
            logger.info(
                "Длина %s  = %s в generate_barcode, c полученными данными - %s и %s "
                "создание штрихкода %s", number, count, number, filename, my_code
                )
            # Сохраняем штрих-код в буфер
            buffer = BytesIO()
            my_code.write(buffer)

            # Перемещаем указатель в начало буфера
            buffer.seek(0)

            # Асинхронно записываем буфер в файл
            async with aiofiles.open(filename, 'wb') as f:
                await f.write(buffer.read())
                logger.info("Штрихкод %s в generate_barcode, был записан по пути %s", my_code, f)
        else:
            raise ValueError(
                f"Недопустимая длина номера. {number}"
                f"должен состоять из 8 или 13 цифр."
                )
    except ValueError as e:
        logger.error(
            "Произошла ошибка в функции generate_barcode по пути с данными %s и %s: %s",
            number, filename, e
            )
