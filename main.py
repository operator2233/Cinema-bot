import os
import random
import string
import telebot
from telebot import types

# ==================================================
# НАСТРОЙКИ
# ==================================================

BOT_TOKEN = "8885937936:AAGKbpOWGoiCgp_518spTLhCEW-5_iDDsnY"
ADMIN_ID = "@Operator4040"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

if not ADMIN_ID:
    raise RuntimeError("ADMIN_ID не найден")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(BOT_TOKEN)

# ==================================================
# ФИЛЬМЫ
# ==================================================

movies = {
    1: {
        "name": "Аватар: Путь воды",
        "genre": "Фантастика",
        "duration": "3 ч 12 мин",
        "price": 350,
        "times": ["12:00", "15:30", "19:00", "22:00"]
    },

    2: {
        "name": "Дэдпул и Росомаха",
        "genre": "Боевик / Комедия",
        "duration": "2 ч 08 мин",
        "price": 400,
        "times": ["11:30", "14:30", "18:00", "21:30"]
    },

    3: {
        "name": "Интерстеллар",
        "genre": "Фантастика / Драма",
        "duration": "2 ч 49 мин",
        "price": 300,
        "times": ["13:00", "16:30", "20:00"]
    },

    4: {
        "name": "Человек-паук",
        "genre": "Фантастика / Боевик",
        "duration": "2 ч 28 мин",
        "price": 620,
        "times": ["12:30", "16:00", "19:30", "22:30"]
    }
}

# ==================================================
# ДАННЫЕ
# ==================================================

users = {}

# Занятые места
occupied = {}

# Заказы
orders = {}

# ==================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==================================================

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
    return "ORD-" + "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=8
        )
    )


def generate_ticket():
    return "CIN-" + "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=8
        )
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


def movie_keyboard():
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

    keyboard = types.InlineKeyboardMarkup(row_width=5)

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


# ==================================================
# START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,

        "🎬 <b>КИНОТЕАТР</b>\n\n"
        "Добро пожаловать!\n\n"
        "Выберите фильм, сеанс и место.",
        
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# ==================================================
# ФИЛЬМЫ
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎬 Фильмы"
)
def films(message):

    bot.send_message(
        message.chat.id,

        "🎬 <b>Выберите фильм:</b>",

        parse_mode="HTML",
        reply_markup=movie_keyboard()
    )


# ==================================================
# ВЫБОР ФИЛЬМА
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("movie:")
)
def select_movie(call):

    bot.answer_callback_query(call.id)

    movie_id = int(call.data.split(":")[1])

    movie = movies[movie_id]

    user = get_user(call.from_user.id)

    user["movie"] = movie_id
    user["time"] = None
    user["seat"] = None
    user["order_id"] = None
    user["ticket"] = None

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
            callback_data="movies"
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


# ==================================================
# ВЫБОР ВРЕМЕНИ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("time:")
)
def select_time(call):

    bot.answer_callback_query(call.id)

    time = call.data.split(":", 1)[1]

    user = get_user(call.from_user.id)

    user["time"] = time
    user["seat"] = None

    movie_id = user["movie"]

    bot.edit_message_text(
        "💺 <b>ВЫБОР МЕСТА</b>\n\n"
        "🔢 — свободно\n"
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


# ==================================================
# ЗАНЯТОЕ МЕСТО
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "occupied"
)
def occupied_seat(call):

    bot.answer_callback_query(
        call.id,
        "Это место уже занято!",
        show_alert=True
    )


# ==================================================
# ВЫБОР МЕСТА
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("seat:")
)
def select_seat(call):

    bot.answer_callback_query(call.id)

    seat = int(
        call.data.split(":")[1]
    )

    user = get_user(call.from_user.id)

    movie_id = user["movie"]
    time = user["time"]

    key = (movie_id, time)

    if seat in occupied.get(key, set()):

        bot.answer_callback_query(
            call.id,
            "Это место уже занято!",
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
            "💺 Другое место",
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


# ==================================================
# НАЗАД К МЕСТАМ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "back_seats"
)
def back_seats(call):

    user = get_user(call.from_user.id)

    movie_id = user["movie"]
    time = user["time"]

    bot.edit_message_text(
        "💺 <b>Выберите место:</b>",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML",

        reply_markup=seats_keyboard(
            movie_id,
            time
        )
    )

    bot.answer_callback_query(call.id)


# ==================================================
# НАЖАЛИ ОПЛАТИТЬ
# ==================================================

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

    movie = movies[movie_id]

    key = (movie_id, time)

    # Проверяем место
    if seat in occupied.get(key, set()):

        bot.send_message(
            call.message.chat.id,

            "❌ Это место уже заняли.\n"
            "Пожалуйста, выберите другое."
        )

        return

    # Создаём заказ
    order_id = generate_order_id()

    user["order_id"] = order_id

    orders[order_id] = {
        "user_id": user_id,
        "movie_id": movie_id,
        "time": time,
        "seat": seat,
        "price": movie["price"],
        "status": "waiting_card",
        "ticket": None
    }

    # Уведомление оператору
    username = call.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "нет username"

    admin_text = (
        "🔔 <b>НОВЫЙ ЗАКАЗ</b>\n\n"

        f"🆔 Заказ: <code>{order_id}</code>\n"
        f"👤 Пользователь: {username_text}\n"
        f"👤 ID: <code>{user_id}</code>\n\n"

        f"🎬 Фильм: <b>{movie['name']}</b>\n"
        f"🕐 Сеанс: <b>{time}</b>\n"
        f"💺 Место: <b>{seat}</b>\n"
        f"💰 Сумма: <b>{movie['price']} ₽</b>\n\n"

        "👇 Отправьте пользователю данные карты."
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "💳 Отправить карту",
            callback_data=f"sendcard:{order_id}"
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

        "Ожидайте данные для оплаты.\n"
        "Оператор отправит реквизиты карты в этот чат.",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML"
    )


# ==================================================
# ОПЕРАТОР ОТПРАВЛЯЕТ КАРТУ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("sendcard:")
)
def send_card(call):

    bot.answer_callback_query(call.id)

    order_id = call.data.split(":", 1)[1]

    if order_id not in orders:
        return

    order = orders[order_id]

    user_id = order["user_id"]

    movie = movies[order["movie_id"]]

    # Оператору
    bot.send_message(
        ADMIN_ID,

        "Введите номер карты для этого заказа.\n\n"
        f"Заказ: {order_id}\n"
        f"Сумма: {movie['price']} ₽\n\n"
        "Например:\n"
        "2200 0000 0000 0000"
    )

    # Сохраняем состояние оператора
    orders[order_id]["status"] = "operator_waiting_card"


# ==================================================
# ОПЕРАТОР ВВОДИТ КАРТУ
# ==================================================

@bot.message_handler(
    func=lambda message:
    message.from_user.id == ADMIN_ID
)
def admin_message(message):

    text = message.text.strip()

    # Ищем заказ, который ждёт карту
    target_order = None

    for order_id, order in orders.items():

        if order["status"] == "operator_waiting_card":
            target_order = order_id
            break

    if not target_order:

        bot.send_message(
            ADMIN_ID,
            "Нет заказов, ожидающих данные карты."
        )

        return

    order = orders[target_order]

    user_id = order["user_id"]

    movie = movies[order["movie_id"]]

    # Сохраняем карту
    order["card"] = text
    order["status"] = "waiting_receipt"

    # Отправляем пользователю
    bot.send_message(
        user_id,

        "💳 <b>ДАННЫЕ ДЛЯ ОПЛАТЫ</b>\n\n"

        f"🎬 {movie['name']}\n"
        f"🕐 Сеанс: {order['time']}\n"
        f"💺 Место: {order['seat']}\n"
        f"💰 Сумма: <b>{movie['price']} ₽</b>\n\n"

        f"💳 Карта для оплаты:\n"
        f"<code>{text}</code>\n\n"

        "После оплаты отправьте сюда "
        "<b>фото квитанции об оплате</b>.\n\n"

        "Без квитанции билет не будет подтверждён.",

        parse_mode="HTML"
    )

    bot.send_message(
        ADMIN_ID,

        f"✅ Карта отправлена пользователю.\n"
        f"Заказ: {target_order}\n\n"
        "Ожидаем квитанцию."
    )


# ==================================================
# ПОЛЬЗОВАТЕЛЬ ОТПРАВЛЯЕТ КВИТАНЦИЮ
# ==================================================

@bot.message_handler(
    content_types=["photo"]
)
def receipt_photo(message):

    user_id = message.from_user.id

    target_order = None

    for order_id, order in orders.items():

        if (
            order["user_id"] == user_id
            and order["status"] == "waiting_receipt"
        ):
            target_order = order_id
            break

    if not target_order:

        bot.send_message(
            message.chat.id,
            "❌ Сейчас нет заказа, для которого нужна квитанция."
        )

        return

    order = orders[target_order]

    movie = movies[order["movie_id"]]

    order["receipt_file_id"] = message.photo[-1].file_id
    order["status"] = "checking_receipt"

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Подтвердить оплату",
            callback_data=f"confirm:{target_order}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"reject:{target_order}"
        )
    )

    # Отправляем фото оператору
    bot.send_photo(
        ADMIN_ID,

        message.photo[-1].file_id,

        caption=(
            "🧾 <b>ПОЛУЧЕНА КВИТАНЦИЯ</b>\n\n"

            f"🆔 Заказ: <code>{target_order}</code>\n"
            f"🎬 Фильм: {movie['name']}\n"
            f"🕐 Время: {order['time']}\n"
            f"💺 Место: {order['seat']}\n"
            f"💰 Сумма: {order['price']} ₽\n"
            f"👤 ID: <code>{user_id}</code>\n\n"

            "Проверьте оплату."
        ),

        parse_mode="HTML",
        reply_markup=keyboard
    )

    bot.send_message(
        user_id,

        "🧾 <b>Квитанция получена.</b>\n\n"
        "Оператор проверяет оплату.\n"
        "После подтверждения вы получите билет.",

        parse_mode="HTML"
    )


# ==================================================
# ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("confirm:")
)
def confirm_payment(call):

    bot.answer_callback_query(call.id)

    order_id = call.data.split(":", 1)[1]

    if order_id not in orders:
        return

    order = orders[order_id]

    if order["status"] != "checking_receipt":
        return

    movie = movies[order["movie_id"]]

    key = (
        order["movie_id"],
        order["time"]
    )

    # Проверяем место ещё раз
    if order["seat"] in occupied.get(key, set()):

        bot.send_message(
            ADMIN_ID,
            "❌ Это место уже занято другим заказом."
        )

        return

    # Бронируем место окончательно
    occupied.setdefault(key, set()).add(
        order["seat"]
    )

    # Создаём билет
    ticket = generate_ticket()

    order["ticket"] = ticket
    order["status"] = "paid"

    user = get_user(order["user_id"])

    user["ticket"] = ticket

    # Пользователь получает билет
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

        "Покажите этот билет контролёру при входе.",

        parse_mode="HTML"
    )

    bot.send_message(
        ADMIN_ID,

        f"✅ Заказ {order_id} подтверждён.\n"
        f"Билет: {ticket}"
    )


# ==================================================
# ОТКЛОНЕНИЕ КВИТАНЦИИ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("reject:")
)
def reject_payment(call):

    bot.answer_callback_query(call.id)

    order_id = call.data.split(":", 1)[1]

    if order_id not in orders:
        return

    order = orders[order_id]

    order["status"] = "waiting_receipt"

    bot.send_message(
        order["user_id"],

        "❌ <b>Квитанция отклонена.</b>\n\n"
        "Пожалуйста, отправьте корректную "
        "квитанцию об оплате.",

        parse_mode="HTML"
    )

    bot.send_message(
        ADMIN_ID,
        f"Квитанция по заказу {order_id} отклонена."
    )


# ==================================================
# МОИ БИЛЕТЫ
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎟 Мои билеты"
)
def my_tickets(message):

    user = get_user(message.from_user.id)

    if not user["ticket"]:

        bot.send_message(
            message.chat.id,
            "🎟 У вас пока нет подтверждённых билетов."
        )

        return

    ticket = user["ticket"]

    # Ищем заказ
    order = None

    for item in orders.values():

        if item.get("ticket") == ticket:
            order = item
            break

    if not order:
        bot.send_message(
            message.chat.id,
            "Билет не найден."
        )
        return

    movie = movies[order["movie_id"]]

    bot.send_message(
        message.chat.id,

        "🎟 <b>МОЙ БИЛЕТ</b>\n\n"

        f"🎬 {movie['name']}\n"
        f"🕐 {order['time']}\n"
        f"💺 Место: {order['seat']}\n"
        f"💰 {order['price']} ₽\n\n"

        f"🔑 <code>{ticket}</code>",

        parse_mode="HTML"
    )


# ==================================================
# ИНФОРМАЦИЯ
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "ℹ️ Информация"
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


# ==================================================
# КОМАНДА /CANCEL ДЛЯ ОПЕРАТОРА
# ==================================================

@bot.message_handler(commands=["cancel"])
def admin_cancel(message):

    if message.from_user.id != ADMIN_ID:
        return

    for order_id, order in orders.items():

        if order["status"] in [
            "operator_waiting_card",
            "waiting_receipt",
            "checking_receipt"
        ]:

            order["status"] = "cancelled"

            bot.send_message(
                order["user_id"],
                "❌ Ваш заказ был отменён оператором."
            )

            bot.send_message(
                ADMIN_ID,
                f"Заказ {order_id} отменён."
            )

            return

    bot.send_message(
        ADMIN_ID,
        "Нет активных заказов."
    )


# ==================================================
# ЗАПУСК
# ==================================================

print("🎬 Cinema Bot запущен!")
print("🔄 Подключение к Telegram...")

bot.infinity_polling(
    timeout=30,
    long_polling_timeout=30
    )
