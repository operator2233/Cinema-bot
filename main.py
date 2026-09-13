import os
import random
import string
import telebot
from telebot import types

# =========================
# НАСТРОЙКИ
# =========================

TOKEN = os.getenv("8885937936:AAGKbpOWGoiCgp_518spTLhCEW-5_iDDsnY")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

bot = telebot.TeleBot(TOKEN)

# =========================
# ФИЛЬМЫ
# =========================

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
    }
}

# Выбранные данные пользователей
users = {}

# Занятые места
# (фильм, время) -> множество мест
occupied = {}


# =========================
# ФУНКЦИИ
# =========================

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "movie": None,
            "time": None,
            "seat": None,
            "ticket": None
        }

    return users[user_id]


def generate_ticket():
    code = "".join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=8
        )
    )
    return f"CIN-{code}"


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
                f"🎬 {movie['name']}",
                callback_data=f"movie:{movie_id}"
            )
        )

    return keyboard


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        "🎬 <b>КИНОТЕАТР</b>\n\n"
        "Добро пожаловать!\n\n"
        "Выберите фильм, сеанс и место, "
        "после чего получите электронный билет.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )


# =========================
# ФИЛЬМЫ
# =========================

@bot.message_handler(func=lambda m: m.text == "🎬 Фильмы")
def films(message):
    bot.send_message(
        message.chat.id,
        "🎬 <b>Выберите фильм:</b>",
        parse_mode="HTML",
        reply_markup=movie_keyboard()
    )


# =========================
# ВЫБОР ФИЛЬМА
# =========================

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
        f"💰 Билет: {movie['price']} ₽\n\n"
        "🕐 <b>Выберите время:</b>"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================
# ВЫБОР ВРЕМЕНИ
# =========================

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
                    callback_data="already_occupied"
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

    bot.edit_message_text(
        "💺 <b>ВЫБОР МЕСТА</b>\n\n"
        "🔢 — свободно\n"
        "❌ — занято\n\n"
        "Выберите место:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================
# ЗАНЯТОЕ МЕСТО
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "already_occupied"
)
def already_occupied(call):
    bot.answer_callback_query(
        call.id,
        "❌ Это место уже занято!",
        show_alert=True
    )


# =========================
# ВЫБОР МЕСТА
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("seat:")
)
def select_seat(call):
    bot.answer_callback_query(call.id)

    seat = int(call.data.split(":")[1])

    user = get_user(call.from_user.id)

    movie_id = user["movie"]
    time = user["time"]

    key = (movie_id, time)

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
        "Проверьте заказ:"
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================
# НАЗАД К МЕСТАМ
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "back_seats"
)
def back_seats(call):
    user = get_user(call.from_user.id)

    movie_id = user["movie"]
    time = user["time"]

    key = (movie_id, time)

    keyboard = types.InlineKeyboardMarkup(row_width=5)

    buttons = []

    for seat in range(1, 21):

        if seat in occupied.get(key, set()):
            buttons.append(
                types.InlineKeyboardButton(
                    "❌",
                    callback_data="already_occupied"
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

    bot.edit_message_text(
        "💺 <b>Выберите место:</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    bot.answer_callback_query(call.id)


# =========================
# ТЕСТОВАЯ ОПЛАТА
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "payment"
)
def payment(call):
    bot.answer_callback_query(call.id)

    user = get_user(call.from_user.id)

    movie_id = user["movie"]
    time = user["time"]
    seat = user["seat"]

    movie = movies[movie_id]

    key = (movie_id, time)

    # Проверяем, не заняли ли место
    if seat in occupied.get(key, set()):
        bot.send_message(
            call.message.chat.id,
            "❌ Это место уже заняли. Выберите другое."
        )
        return

    # Занимаем место
    occupied.setdefault(key, set()).add(seat)

    # Создаём билет
    ticket = generate_ticket()
    user["ticket"] = ticket

    text = (
        "✅ <b>ОПЛАТА УСПЕШНА</b>\n\n"
        "🎟 <b>ЭЛЕКТРОННЫЙ БИЛЕТ</b>\n\n"
        f"🎬 {movie['name']}\n"
        f"🕐 Сеанс: {time}\n"
        f"💺 Место: {seat}\n"
        f"💰 Стоимость: {movie['price']} ₽\n\n"
        "🔑 Номер билета:\n"
        f"<code>{ticket}</code>\n\n"
        "Предъявите этот код контролёру."
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🎬 Купить ещё билет",
            callback_data="movies"
        )
    )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# =========================
# ОТМЕНА
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "cancel"
)
def cancel(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        "❌ <b>Заказ отменён.</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML"
    )


# =========================
# СПИСОК ФИЛЬМОВ
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "movies"
)
def movies_callback(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        "🎬 <b>Выберите фильм:</b>",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="HTML",
        reply_markup=movie_keyboard()
    )


# =========================
# НАЗАД К ФИЛЬМАМ
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "movies"
)
def movies_callback_second(call):
    pass


# =========================
# МОИ БИЛЕТЫ
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🎟 Мои билеты"
)
def my_tickets(message):
    user = get_user(message.from_user.id)

    if not user["ticket"]:
        bot.send_message(
            message.chat.id,
            "🎟 У вас пока нет купленных билетов."
        )
        return

    movie = movies[user["movie"]]

    text = (
        "🎟 <b>МОЙ БИЛЕТ</b>\n\n"
        f"🎬 Фильм: {movie['name']}\n"
        f"🕐 Сеанс: {user['time']}\n"
        f"💺 Место: {user['seat']}\n"
        f"💰 Цена: {movie['price']} ₽\n\n"
        f"🔑 <code>{user['ticket']}</code>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )


# =========================
# ИНФОРМАЦИЯ
# =========================

@bot.message_handler(
    func=lambda m: m.text == "ℹ️ Информация"
)
def information(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ <b>КИНОТЕАТР</b>\n\n"
        "📍 Адрес: ул. Центральная, 15\n"
        "☎️ Телефон: +7 900 000-00-00\n\n"
        "🎟 Электронный билет приходит в Telegram.",
        parse_mode="HTML"
    )


# =========================
# НЕИЗВЕСТНЫЕ КОМАНДЫ
# =========================

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "Выберите действие из меню:",
        reply_markup=main_menu()
    )


# =========================
# ЗАПУСК
# =========================

print("🎬 Cinema Bot запущен!")
print("🔄 Подключение к Telegram...")

bot.infinity_polling(
    timeout=30,
    long_polling_timeout=30
                     )
