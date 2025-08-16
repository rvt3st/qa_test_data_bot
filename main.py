import os
import time
import json
from secrets import token_urlsafe

from faker import Faker
from telebot import TeleBot, types
from html import escape

# НАСТРОЙКИ
TOKEN = os.getenv("TOKEN")
bot = TeleBot(TOKEN, parse_mode='html')

faker_default = Faker()
faker_ru = Faker('ru_RU')

# Форматы для генерации файлов
FILE_FORMATS = ['.jpg', '.png', '.svg', '.gif', '.ico',
                '.mp4', '.avi', '.webm',
                '.doc', '.docx', '.xls', '.xlsx',
                '.txt', '.pdf', '.css', '.html', '.js', '.json',
                '.zip', '.rar']

MAX_BYTES = 45 * 1024 * 1024

# Клавиатура
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('💳 Карта'),
           types.KeyboardButton('👤 Пользователи'))
    kb.row(types.KeyboardButton('📄 Файл'),
           types.KeyboardButton('🔤 Строка со спецсимволами'))
    return kb

def back_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('⬅️ Назад в меню'))
    return kb

# /start
@bot.message_handler(commands=['start'])
def start_handler(message: types.Message):
    bot.set_my_commands([types.BotCommand('/start', 'перезапуск')])
    bot.send_message(
        message.chat.id,
        'Привет! Я бот для <b>генерации тестовых данных</b>.\n'
        'Выбери функцию 👇',
        reply_markup=main_menu()
    )

# Назад в меню
@bot.message_handler(func=lambda m: m.text == '⬅️ Назад в меню')
def back_to_menu(message: types.Message):
    start_handler(message)

# Генерация тестовой карты

@bot.message_handler(func=lambda m: m.text == '💳 Карта')
def route_card(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('VISA'), types.KeyboardButton('Mastercard'))
    kb.row(types.KeyboardButton('Maestro'), types.KeyboardButton('МИР'))
    kb.row(types.KeyboardButton('⬅️ Назад в меню'))
    bot.send_message(message.chat.id, 'Выбери тип карты:', reply_markup=kb)
    bot.register_next_step_handler(message, handle_card_type)

def handle_card_type(message: types.Message):
    if message.text == '⬅️ Назад в меню':
        return start_handler(message)

    mapping = {
        'VISA': 'visa',
        'Mastercard': 'mastercard',
        'Maestro': 'maestro',
        'МИР': 'mir',
    }
    card_type = mapping.get(message.text)
    if not card_type:
        bot.send_message(message.chat.id, 'Не понимаю. Выбери на клавиатуре.', reply_markup=back_menu())
        return

    if card_type == 'mir':
        number = faker_ru.credit_card_number(card_type)
    else:
        number = faker_default.credit_card_number(card_type)

    bot.send_message(
        message.chat.id,
        f'Тестовая карта <b>{message.text}</b>:\n<code>{number}</code>',
        reply_markup=main_menu()
    )

# Тестовые пользователи

@bot.message_handler(func=lambda m: m.text == '👤 Пользователи')
def route_users(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('1️⃣'), types.KeyboardButton('2️⃣'))
    kb.row(types.KeyboardButton('5️⃣'), types.KeyboardButton('🔟'))
    kb.row(types.KeyboardButton('⬅️ Назад в меню'))
    bot.send_message(message.chat.id, 'Сколько пользователей сгенерировать?', reply_markup=kb)
    bot.register_next_step_handler(message, handle_users_count)

def handle_users_count(message: types.Message):
    if message.text == '⬅️ Назад в меню':
        return start_handler(message)
    mapping = {'1️⃣': 1, '2️⃣': 2, '5️⃣': 5, '🔟': 10}
    n = mapping.get(message.text)
    if not n:
        bot.send_message(message.chat.id, 'Выбери количество на клавиатуре.', reply_markup=back_menu())
        return

    payload = []
    for _ in range(n):
        p = faker_ru.simple_profile()
        p['phone'] = f'+7{faker_ru.msisdn()[3:]}' 
        p['password'] = token_urlsafe(10) 
        payload.append(p)

    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True, default=str)
    bot.send_message(message.chat.id, f'Данные {n} пользователей:\n<code>{text}</code>', reply_markup=main_menu())

# Тестовые файлы

@bot.message_handler(func=lambda m: m.text == '📄 Файл')
def route_file(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=5)
    kb.add(*FILE_FORMATS)
    kb.add('⬅️ Назад в меню')
    bot.send_message(message.chat.id, 'Выбери расширение файла:', reply_markup=kb)
    bot.register_next_step_handler(message, handle_file_format)

def handle_file_format(message: types.Message):
    if message.text == '⬅️ Назад в меню':
        return start_handler(message)
    if message.text not in FILE_FORMATS:
        bot.send_message(message.chat.id, 'Неверное расширение. Выбери на клавиатуре.', reply_markup=back_menu())
        return

    chosen_format = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('B (байты)', 'KB (килобайты)', 'MB (мегабайты)')
    kb.add('⬅️ Назад в меню')
    msg = bot.send_message(
        message.chat.id,
        f'Выбрано расширение <b>{chosen_format}</b>.\nВыбери единицы измерения:',
        reply_markup=kb
    )
    bot.register_next_step_handler(msg, handle_file_unit, chosen_format)

def handle_file_unit(message: types.Message, chosen_format: str):
    if message.text == '⬅️ Назад в меню':
        return start_handler(message)
    if message.text not in ['B (байты)', 'KB (килобайты)', 'MB (мегабайты)']:
        bot.send_message(message.chat.id, 'Неверная единица. Выбери на клавиатуре.', reply_markup=back_menu())
        return

    unit = message.text
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('⬅️ Назад в меню')
    msg = bot.send_message(
        message.chat.id,
        f'Расширение: <b>{chosen_format}</b>\nЕдиницы: <b>{unit}</b>\n\n'
        'Введи <b>целое число</b> — размер файла.\n'
        'Ограничения: 1 байт … 45 MB.',
        reply_markup=kb
    )
    bot.register_next_step_handler(msg, handle_file_size, chosen_format, unit)

def handle_file_size(message: types.Message, chosen_format: str, unit: str):
    if message.text == '⬅️ Назад в меню':
        return start_handler(message)

    if not message.text.isdigit():
        return bot.send_message(message.chat.id, 'Нужно целое число. Попробуй ещё раз.', reply_markup=back_menu())

    size = int(message.text)
    if unit.startswith('MB'):
        size_bytes = size * 1024 * 1024
        unit_short = 'MB'
    elif unit.startswith('KB'):
        size_bytes = size * 1024
        unit_short = 'KB'
    else:
        size_bytes = size
        unit_short = 'B'

    if size_bytes < 1 or size_bytes > MAX_BYTES:
        return bot.send_message(message.chat.id, 'Размер вне диапазона (1 B … 45 MB).', reply_markup=back_menu())

    ts = int(time.time())
    filename = f'{ts}-{size_bytes}-bytes{chosen_format}'
    with open(filename, 'wb') as f:
        f.write(os.urandom(size_bytes))

    if unit_short in ('MB', 'KB'):
        caption = f'Файл {chosen_format} сгенерирован.\nРазмер: <b>{size} {unit_short}</b> ({size_bytes:,} B)'.replace(',', ' ')
    else:
        caption = f'Файл {chosen_format} сгенерирован.\nРазмер: <b>{size_bytes:,} B</b>'.replace(',', ' ')

    with open(filename, 'rb') as f:
        bot.send_document(message.chat.id, f, caption=caption, reply_markup=main_menu())

    try:
        os.unlink(filename)
    except OSError:
        pass

# Строка со спецсимволами

@bot.message_handler(func=lambda m: m.text == '🔤 Строка со спецсимволами')
def route_special_string(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('Сгенерировать строку'))
    kb.row(types.KeyboardButton('⬅️ Назад в меню'))
    bot.send_message(
        message.chat.id,
        'Сгенерировать тестовую строку со спецсимволами и разными алфавитами?',
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text == 'Сгенерировать строку')
def handle_special_string(message: types.Message):
    part_cyr = 'Кириллица: Привет, мир!'
    part_ar = 'عربي: مرحبًا بالعالم'
    part_zh = '中文：你好，世界'
    part_di = 'Диакретические символы: Ą Ę Ė Į Ų Ū'
    part_emj = 'Emoji: 😀🥷🏽🚀✨📦'
    part_ws = 'Пробелы и неразрывный\u00A0пробел'
    part_newlines = 'Переносы:\nстрока 1\nстрока 2\r\nстрока 3'
    part_quotes = 'Кавычки: "double" «ёлочки» ‘single’'
    part_esc = r'Экранирование: \n \t \\ \/ < > &'

    long_mixed = ('абв🙂ABC漢字' * 80)[:1000]

    full = (
        f'{part_cyr}\n{part_ar}\n{part_zh}\n{part_di}\n{part_emj}\n'
        f'{part_ws}\n{part_newlines}\n{part_quotes}\n{part_esc}\n\n'
        f'Длинная_строка_1000симв:\n{long_mixed}'
    )

    safe = escape(full, quote=False)
    bot.send_message(
        message.chat.id,
        f'Готово! Вот строка для стресс-тестов ввода/валидации/логов:\n<pre>{safe}</pre>',
        reply_markup=main_menu(),
        disable_web_page_preview=True
    )

# Запуск
def main():
    bot.infinity_polling()

if __name__ == '__main__':
    main()



