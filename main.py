import os
import random
import string
import telebot
from telebot import types


# ============================================================
# НАСТРОЙКИ
# ============================================================

# Вариант для Railway:
BOT_TOKEN = "8885937936:AAGKbpOWGoiCgp_518spTLhCEW-5_iDDsnY"


# ID оператора.
# ВСТАВЬ СЮДА СВОЙ TELEGRAM ID.
ADMIN_ID = 8758604868


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")


bot = telebot.TeleBot(BOT_TOKEN)


# ============================================================
# ФИЛЬМЫ
# ============================================================

movies = {

    1: {
        "name": "Аватар: Путь воды",
        "genre": "Фантастика",
        "duration": "3 ч 12 мин",
        "price": 350,
        "times": [
            "12:00",
            "15:30",
            "19:00",
            "22:00"
        ]
    },

    2: {
        "name": "Дэдпул и Росомаха",
        "genre": "Боевик / Комедия",
        "duration": "2 ч 08 мин",
        "price": 400,
        "times": [
            "11:30",
            "14:30",
            "18:00",
            "21:30"
        ]
    },

    3: {
        "name": "Интерстеллар",
        "genre": "Фантастика / Драма",
        "duration": "2 ч 49 мин",
        "price": 300,
        "times": [
            "13:00",
            "16:30",
            "20:00"
        ]
    },

    4: {
        "name": "Человек-паук",
        "genre": "Фантастика / Боевик",
        "duration": "2 ч 28 мин",
        "price": 620,
        "times": [
            "12:30",
            "16:00",
            "19:30",
            "22:30"
        ]
    }
}


# ============================================================
# ХРАНИЛИЩЕ
# ============================================================

# Данные пользователей
users = {}

# Занятые места
#
# Например:
# occupied[(4, "19:30")] = {1, 2, 5}
#
occupied = {}

# Заказы
orders = {}


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_user(user_id):

    if user_id not in users:

        users[user_id] = {
            "movie": None,
            "time": None,
            "seat": None,
            "order_id": None,
            "ticket": None
        }

    return users[user_id]


def generate_order_id():

    symbols = string.ascii_uppercase + string.digits

    return "ORD-" + "".join(
        random.choices(symbols, k=8)
    )


def generate_ticket():

    symbols = string.ascii_uppercase + string.digits

    return "CIN-" + "".join(
        random.choices(symbols, k=8)
    )


def main_menu():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "🎬 Фильмы",
        "🎟 Мои билеты"
    )

    keyboard.row(
        "ℹ️ Информация"
    )

    return keyboard


def movies_keyboard():

    keyboard = types.InlineKeyboardMarkup()

    for movie_id, movie in movies.items():

        keyboard.add(
            types.InlineKeyboardButton(
                f"🎬 {movie['name']} — {movie['price']} ₽",
                callback_data=f"movie:{movie_id}"
            )
        )

    return keyboard


def seats_keyboard(movie_id, time):

    key = (movie_id, time)

    if key not in occupied:
        occupied[key] = set()

    keyboard = types.InlineKeyboardMarkup(
        row_width=5
    )

    buttons = []

    for seat in range(1, 21):

        if seat in occupied[key]:

            buttons.append(
                types.InlineKeyboardButton(
                    "❌",
                    callback_data="occupied"
                )
            )

        else:

            buttons.append(
                types.InlineKeyboardButton(
                    str(seat),
                    callback_data=f"seat:{seat}"
                )
            )

    keyboard.add(*buttons)

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"movie:{movie_id}"
        )
    )

    return keyboard


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):

    get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,

        "🎬 <b>КИНОТЕАТР</b>\n\n"
        "Добро пожаловать!\n\n"
        "Выберите фильм, время и место.",
        
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# ============================================================
# ФИЛЬМЫ
# ============================================================

@bot.message_handler(
    func=lambda message: message.text == "🎬 Фильмы"
)
def show_movies(message):

    bot.send_message(
        message.chat.id,

        "🎬 <b>Выберите фильм:</b>",

        parse_mode="HTML",
        reply_markup=movies_keyboard()
    )


# ============================================================
# ВЫБОР ФИЛЬМА
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("movie:")
)
def select_movie(call):

    bot.answer_callback_query(call.id)

    movie_id = int(
        call.data.split(":")[1]
    )

    movie = movies[movie_id]

    user = get_user(
        call.from_user.id
    )

    user["movie"] = movie_id
    user["time"] = None
    user["seat"] = None
    user["order_id"] = None

    keyboard = types.InlineKeyboardMarkup()

    for time in movie["times"]:

        keyboard.add(
            types.InlineKeyboardButton(
                f"🕐 {time}",
                callback_data=f"time:{time}"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data="back_movies"
        )
    )

    text = (
        f"🎬 <b>{movie['name']}</b>\n\n"

        f"🎭 Жанр: {movie['genre']}\n"
        f"⏱ Длительность: {movie['duration']}\n"
        f"💰 Цена: {movie['price']} ₽\n\n"

        "🕐 <b>Выберите время:</b>"
    )

    bot.edit_message_text(
        text,

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML",
        reply_markup=keyboard
    )


# ============================================================
# ВЫБОР ВРЕМЕНИ
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("time:")
)
def select_time(call):

    bot.answer_callback_query(call.id)

    time = call.data.split(
        ":",
        1
    )[1]

    user = get_user(
        call.from_user.id
    )

    user["time"] = time
    user["seat"] = None

    movie_id = user["movie"]

    bot.edit_message_text(
        "💺 <b>ВЫБОР МЕСТА</b>\n\n"

        "🔢 — свободное\n"
        "❌ — занято\n\n"

        "Выберите место:",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML",

        reply_markup=seats_keyboard(
            movie_id,
            time
        )
    )


# ============================================================
# ЗАНЯТОЕ МЕСТО
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "occupied"
)
def occupied_seat(call):

    bot.answer_callback_query(
        call.id,
        "❌ Это место уже занято!",
        show_alert=True
    )


# ============================================================
# ВЫБОР МЕСТА
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("seat:")
)
def select_seat(call):

    user_id = call.from_user.id

    user = get_user(user_id)

    seat = int(
        call.data.split(":")[1]
    )

    movie_id = user["movie"]
    time = user["time"]

    key = (
        movie_id,
        time
    )

    if seat in occupied.get(key, set()):

        bot.answer_callback_query(
            call.id,
            "❌ Это место уже занято!",
            show_alert=True
        )

        return

    user["seat"] = seat

    movie = movies[movie_id]

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "💳 Оплатить",
            callback_data="payment"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "💺 Выбрать другое место",
            callback_data="back_seats"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Отменить",
            callback_data="cancel"
        )
    )

    text = (
        "🎟 <b>ВАШ ЗАКАЗ</b>\n\n"

        f"🎬 Фильм: <b>{movie['name']}</b>\n"
        f"🕐 Время: <b>{time}</b>\n"
        f"💺 Место: <b>{seat}</b>\n"
        f"💰 Цена: <b>{movie['price']} ₽</b>\n\n"

        "Проверьте данные заказа."
    )

    bot.edit_message_text(
        text,

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML",
        reply_markup=keyboard
    )

    bot.answer_callback_query(call.id)


# ============================================================
# НАЗАД К МЕСТАМ
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "back_seats"
)
def back_seats(call):

    bot.answer_callback_query(call.id)

    user = get_user(
        call.from_user.id
    )

    movie_id = user["movie"]
    time = user["time"]

    bot.edit_message_text(
        "💺 <b>ВЫБОР МЕСТА</b>\n\n"
        "Выберите место:",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML",

        reply_markup=seats_keyboard(
            movie_id,
            time
        )
    )


# ============================================================
# НАЖАЛИ ОПЛАТИТЬ
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "payment"
)
def payment(call):

    bot.answer_callback_query(call.id)

    user_id = call.from_user.id

    user = get_user(user_id)

    movie_id = user["movie"]
    time = user["time"]
    seat = user["seat"]

    if movie_id is None or time is None or seat is None:

        bot.send_message(
            call.message.chat.id,
            "❌ Данные заказа потеряны. Начните заново."
        )

        return

    movie = movies[movie_id]

    key = (
        movie_id,
        time
    )

    # Проверяем место
    if seat in occupied.get(key, set()):

        bot.send_message(
            call.message.chat.id,

            "❌ Это место уже заняли.\n"
            "Выберите другое место."
        )

        return

    # Создаём заказ
    order_id = generate_order_id()

    orders[order_id] = {

        "user_id": user_id,

        "movie_id": movie_id,

        "time": time,

        "seat": seat,

        "price": movie["price"],

        "status": "waiting_card",

        "card": None,

        "receipt_file_id": None,

        "ticket": None
    }

    user["order_id"] = order_id

    username = call.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "нет username"

    # Сообщение оператору
    admin_text = (

        "🔔 <b>НОВЫЙ ЗАКАЗ</b>\n\n"

        f"🆔 Заказ: <code>{order_id}</code>\n"

        f"👤 Пользователь: {username_text}\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"

        f"🎬 Фильм: <b>{movie['name']}</b>\n"
        f"🕐 Сеанс: <b>{time}</b>\n"
        f"💺 Место: <b>{seat}</b>\n"
        f"💰 Сумма: <b>{movie['price']} ₽</b>\n\n"

        "Нажмите кнопку ниже, чтобы "
        "перейти к отправке реквизитов."
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "💳 Отправить реквизиты",
            callback_data=f"card:{order_id}"
        )
    )

    bot.send_message(
        ADMIN_ID,
        admin_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    # Пользователю
    bot.edit_message_text(

        "⏳ <b>Заказ отправлен оператору.</b>\n\n"

        "Оператор сейчас подготовит "
        "реквизиты для оплаты.\n\n"

        "После получения реквизитов "
        "оплатите заказ и отправьте "
        "<b>фото квитанции</b>.",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML"
    )


# ============================================================
# ОПЕРАТОР НАЖАЛ «ОТПРАВИТЬ РЕКВИЗИТЫ»
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("card:")
)
def card_button(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "Нет доступа",
            show_alert=True
        )

        return

    bot.answer_callback_query(call.id)

    order_id = call.data.split(
        ":",
        1
    )[1]

    if order_id not in orders:
        return

    order = orders[order_id]

    if order["status"] != "waiting_card":

        bot.send_message(
            ADMIN_ID,
            "Этот заказ уже обрабатывается."
        )

        return

    order["status"] = "operator_entering_card"

    bot.send_message(

        ADMIN_ID,

        "💳 <b>Введите реквизиты карты</b>\n\n"

        f"Заказ: <code>{order_id}</code>\n"
        f"Сумма: <b>{order['price']} ₽</b>\n\n"

        "Отправьте следующим сообщением "
        "номер карты.",

        parse_mode="HTML"
    )


# ============================================================
# СООБЩЕНИЯ ОПЕРАТОРА
# ============================================================

@bot.message_handler(
    func=lambda message:
    message.from_user.id == ADMIN_ID
)
def admin_text(message):

    text = message.text.strip()

    # Ищем заказ, где оператор должен ввести карту
    order_id = None

    for current_id, order in orders.items():

        if order["status"] == "operator_entering_card":

            order_id = current_id
            break

    if order_id is None:

        bot.send_message(
            ADMIN_ID,

            "Нет заказа, ожидающего реквизиты карты."
        )

        return

    order = orders[order_id]

    order["card"] = text

    order["status"] = "waiting_receipt"

    movie = movies[
        order["movie_id"]
    ]

    # Отправляем карту пользователю
    bot.send_message(

        order["user_id"],

        "💳 <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ</b>\n\n"

        f"🎬 Фильм: {movie['name']}\n"
        f"🕐 Сеанс: {order['time']}\n"
        f"💺 Место: {order['seat']}\n"
        f"💰 Сумма: <b>{order['price']} ₽</b>\n\n"

        "💳 Карта для оплаты:\n"
        f"<code>{text}</code>\n\n"

        "После оплаты отправьте сюда "
        "<b>фото квитанции</b>.\n\n"

        "После проверки оператор подтвердит "
        "оплату и выдаст электронный билет.",

        parse_mode="HTML"
    )

    # Подтверждение оператору
    bot.send_message(

        ADMIN_ID,

        "✅ <b>Реквизиты отправлены пользователю.</b>\n\n"

        f"Заказ: <code>{order_id}</code>\n"

        "Теперь ожидаем квитанцию.",

        parse_mode="HTML"
    )


# ============================================================
# ПОЛЬЗОВАТЕЛЬ ОТПРАВИЛ ФОТО
# ============================================================

@bot.message_handler(
    content_types=["photo"]
)
def receipt(message):

    user_id = message.from_user.id

    order_id = None

    # Ищем активный заказ пользователя
    for current_id, order in orders.items():

        if (
            order["user_id"] == user_id
            and order["status"] == "waiting_receipt"
        ):

            order_id = current_id
            break

    if order_id is None:

        bot.send_message(

            message.chat.id,

            "❌ Сейчас нет заказа, "
            "для которого требуется квитанция."
        )

        return

    order = orders[order_id]

    order["receipt_file_id"] = (
        message.photo[-1].file_id
    )

    order["status"] = "checking_receipt"

    movie = movies[
        order["movie_id"]
    ]

    # Кнопки оператору
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Подтвердить оплату",
            callback_data=f"confirm:{order_id}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Отклонить квитанцию",
            callback_data=f"reject:{order_id}"
        )
    )

    # Отправляем квитанцию оператору
    bot.send_photo(

        ADMIN_ID,

        message.photo[-1].file_id,

        caption=(

            "🧾 <b>ПОЛУЧЕНА КВИТАНЦИЯ</b>\n\n"

            f"🆔 Заказ: <code>{order_id}</code>\n"

            f"🎬 Фильм: {movie['name']}\n"
            f"🕐 Сеанс: {order['time']}\n"
            f"💺 Место: {order['seat']}\n"
            f"💰 Сумма: {order['price']} ₽\n\n"

            f"👤 Telegram ID: "
            f"<code>{user_id}</code>\n\n"

            "Проверьте оплату."
        ),

        parse_mode="HTML",

        reply_markup=keyboard
    )

    # Пользователю
    bot.send_message(

        user_id,

        "🧾 <b>Квитанция получена.</b>\n\n"

        "Оператор проверяет оплату.\n\n"

        "После подтверждения вы получите "
        "электронный билет.",

        parse_mode="HTML"
    )


# ============================================================
# ПОДТВЕРДИТЬ ОПЛАТУ
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("confirm:")
)
def confirm_payment(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "Нет доступа",
            show_alert=True
        )

        return

    bot.answer_callback_query(call.id)

    order_id = call.data.split(
        ":",
        1
    )[1]

    if order_id not in orders:
        return

    order = orders[order_id]

    if order["status"] != "checking_receipt":

        bot.send_message(
            ADMIN_ID,
            "Этот заказ уже обработан."
        )

        return

    movie = movies[
        order["movie_id"]
    ]

    key = (
        order["movie_id"],
        order["time"]
    )

    # Проверяем место
    if order["seat"] in occupied.get(
        key,
        set()
    ):

        bot.send_message(

            ADMIN_ID,

            "❌ Ошибка: это место уже занято."
        )

        return

    # Занимаем место
    occupied.setdefault(
        key,
        set()
    ).add(
        order["seat"]
    )

    # Создаём билет
    ticket = generate_ticket()

    order["ticket"] = ticket
    order["status"] = "paid"

    user = get_user(
        order["user_id"]
    )

    user["ticket"] = ticket

    # Отправляем билет пользователю
    bot.send_message(

        order["user_id"],

        "✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\n"

        "🎟 <b>ЭЛЕКТРОННЫЙ БИЛЕТ</b>\n\n"

        f"🎬 Фильм: <b>{movie['name']}</b>\n"
        f"🕐 Сеанс: <b>{order['time']}</b>\n"
        f"💺 Место: <b>{order['seat']}</b>\n"
        f"💰 Стоимость: <b>{order['price']} ₽</b>\n\n"

        f"🔑 Номер билета:\n"
        f"<code>{ticket}</code>\n\n"

        "Предъявите этот билет "
        "контролёру при входе.",

        parse_mode="HTML"
    )

    # Оператору
    bot.send_message(

        ADMIN_ID,

        "✅ <b>ЗАКАЗ ПОДТВЕРЖДЁН</b>\n\n"

        f"Заказ: <code>{order_id}</code>\n"
        f"Билет: <code>{ticket}</code>",

        parse_mode="HTML"
    )


# ============================================================
# ОТКЛОНИТЬ КВИТАНЦИЮ
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("reject:")
)
def reject_payment(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "Нет доступа",
            show_alert=True
        )

        return

    bot.answer_callback_query(call.id)

    order_id = call.data.split(
        ":",
        1
    )[1]

    if order_id not in orders:
        return

    order = orders[order_id]

    order["status"] = "waiting_receipt"

    bot.send_message(

        order["user_id"],

        "❌ <b>Квитанция отклонена.</b>\n\n"

        "Оператор не смог подтвердить оплату.\n\n"

        "Пожалуйста, отправьте корректную "
        "фотографию квитанции.",

        parse_mode="HTML"
    )

    bot.send_message(

        ADMIN_ID,

        f"❌ Квитанция заказа "
        f"<code>{order_id}</code> отклонена.",

        parse_mode="HTML"
    )


# ============================================================
# МОИ БИЛЕТЫ
# ============================================================

@bot.message_handler(
    func=lambda message:
    message.text == "🎟 Мои билеты"
)
def my_tickets(message):

    user_id = message.from_user.id

    user = get_user(user_id)

    ticket = user.get("ticket")

    if not ticket:

        bot.send_message(

            message.chat.id,

            "🎟 У вас пока нет подтверждённых билетов."
        )

        return

    order = None

    for current_order in orders.values():

        if (
            current_order.get("ticket")
            == ticket
        ):

            order = current_order
            break

    if not order:

        bot.send_message(

            message.chat.id,

            "❌ Билет не найден."
        )

        return

    movie = movies[
        order["movie_id"]
    ]

    bot.send_message(

        message.chat.id,

        "🎟 <b>МОЙ БИЛЕТ</b>\n\n"

        f"🎬 {movie['name']}\n"
        f"🕐 Сеанс: {order['time']}\n"
        f"💺 Место: {order['seat']}\n"
        f"💰 Цена: {order['price']} ₽\n\n"

        f"🔑 <code>{ticket}</code>",

        parse_mode="HTML"
    )


# ============================================================
# ИНФОРМАЦИЯ
# ============================================================

@bot.message_handler(
    func=lambda message:
    message.text == "ℹ️ Информация"
)
def information(message):

    bot.send_message(

        message.chat.id,

        "ℹ️ <b>КИНОТЕАТР</b>\n\n"

        "📍 Адрес: ул. Центральная, 15\n"
        "☎️ Телефон: +7 900 000-00-00\n\n"

        "🎟 Электронный билет приходит "
        "после подтверждения оплаты.",

        parse_mode="HTML"
    )


# ============================================================
# НАЗАД К ФИЛЬМАМ
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "back_movies"
)
def back_movies(call):

    bot.answer_callback_query(call.id)

    bot.edit_message_text(

        "🎬 <b>Выберите фильм:</b>",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML",

        reply_markup=movies_keyboard()
    )


# ============================================================
# НЕИЗВЕСТНЫЙ ТЕКСТ
# ============================================================

@bot.message_handler(
    func=lambda message: True
)
def unknown(message):

    # Не отвечаем оператору лишний раз
    if message.from_user.id == ADMIN_ID:
        return

    bot.send_message(

        message.chat.id,

        "Используйте меню ниже:",

        reply_markup=main_menu()
    )


# ============================================================
# ЗАПУСК
# ============================================================

print("================================")
print("🎬 CINEMA BOT")
print("================================")
print("✅ Бот запущен")
print("🔄 Подключение к Telegram...")
print("================================")

bot.infinity_polling(
    timeout=30,
    long_polling_timeout=30
        )
