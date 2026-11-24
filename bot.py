import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =====================================================================
# НАСТРОЙКИ БОТА (УЖЕ ЗАПОЛНЕНЫ ВАШИМИ ДАННЫМИ)
# =====================================================================
API_TOKEN = "9014835271:AAHOS9mg1Vmc8M1LuMMZNo5hO9RyUs2MsWM"
PAYMENT_URL = "https://donatepay.ru/don/1499159"
INVITE_LINK = "https://t.me/+iFmTmyT_u-dmYzQy"
ADMIN_USERNAME = "atomprod_13"  # Юзернейм администратора (без @)

# Файл для сохранения ID администратора, чтобы не сбивался при перезапуске
CONFIG_FILE = "admin_config.json"

# Настройка логирования (вывод событий в консоль)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =====================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ID АДМИНИСТРАТОРА
# =====================================================================
def get_admin_id() -> int | None:
    """Читает сохраненный числовой ID администратора из файла."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("admin_id")
        except Exception as e:
            logging.error(f"Ошибка чтения конфига: {e}")
    return None

def save_admin_id(admin_id: int):
    """Сохраняет числовой ID администратора в файл."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"admin_id": admin_id}, f)
    except Exception as e:
        logging.error(f"Ошибка сохранения конфига: {e}")

# =====================================================================
# КЛАВИАТУРЫ
# =====================================================================
def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Кнопка со ссылкой на оплату для зрителя."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Оплатить 119 рублей", url=PAYMENT_URL))
    return builder.as_markup()

def get_admin_decision_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Кнопки принятия решения для администратора под скриншотом чека."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Принять в канал", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(text="❌ Не принимать в канал", callback_data=f"reject_{user_id}")
    )
    return builder.as_markup()

# =====================================================================
# ТЕКСТЫ СООБЩЕНИЙ
# =====================================================================
WELCOME_TEXT = (
    "👋 Привет! Добро пожаловать в <b>Бот Айда!</b>\n\n"
    "💰 Стоимость прохода в закрытый канал составляет ровно <b>119 рублей</b>.\n\n"
    "⚠️ <b>Важные условия оплаты:</b>\n"
    "1. Принимаются <b>только российские рубли (RUB)</b>.\n"
    "2. Сумма перевода должна быть <b>строго 119 рублей</b>.\n"
    "3. После успешной оплаты обязательно <b>сделайте скриншот чека</b> и отправьте его прямо сюда, в этот чат с ботом.\n\n"
    "👇 Нажмите на кнопку ниже, чтобы перейти к оплате:"
)

HELP_TEXT = (
    "ℹ️ <b>Правила оплаты и инструкция:</b>\n\n"
    "1. Перейдите по ссылке для оплаты (кнопка ниже или команда /pay).\n"
    "2. Введите сумму <b>119 рублей</b> (валюта — только российские рубли).\n"
    "3. Завершите платеж и сохраните скриншот квитанции/чека, где четко видна сумма и дата.\n"
    "4. Отправьте это фото в чат с ботом (как обычную картинку).\n"
    "5. Ожидайте проверки администратором. Обычно это занимает несколько минут. После подтверждения бот пришлет вам уникальную ссылку на вход в канал!"
)

# =====================================================================
# ОБРАБОТЧИКИ КОМАНД
# =====================================================================

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """
    Секретная команда для привязки аккаунта @atomprod_13 к боту.
    Telegram не позволяет ботам писать первым по @username, поэтому админ
    должен один раз написать боту /admin.
    """
    username = message.from_user.username
    if username and username.lower() == ADMIN_USERNAME.lower():
        save_admin_id(message.from_user.id)
        await message.answer(
            f"✅ Отлично, @{username}! Ваш аккаунт успешно привязан как администратор.\n"
            f"Теперь все скриншоты чеков от зрителей будут приходить сюда."
        )
    else:
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    # Автоматическая привязка админа, если он просто нажал /start
    if message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.lower():
        if get_admin_id() != message.from_user.id:
            save_admin_id(message.from_user.id)
            await message.answer("🔔 <i>Системное уведомление: Вы автоматически авторизованы как администратор для приема чеков.</i>", parse_mode="HTML")

    await message.answer(
        text=WELCOME_TEXT,
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    """Обработчик команды /pay."""
    text = (
        "💳 <b>Ссылка на оплату доступа в канал:</b>\n\n"
        "Напоминаем: сумма строго <b>119 российских рублей</b>.\n"
        "После оплаты отправьте скриншот чека в этот чат."
    )
    await message.answer(
        text=text,
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help."""
    await message.answer(
        text=HELP_TEXT,
        reply_markup=get_payment_keyboard(),
        parse_mode="HTML"
    )

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    """Обработчик команды /reset (сброс и возврат в начало)."""
    await message.answer("🔄 Процесс сброшен. Начинаем заново!\n")
    await cmd_start(message)

# =====================================================================
# ОБРАБОТКА ФОТОГРАФИЙ (СКРИНШОТОВ ЧЕКОВ)
# =====================================================================

@dp.message(F.photo)
async def handle_receipt_photo(message: types.Message):
    """Перехватывает фотографию от зрителя и пересылает администратору."""
    admin_id = get_admin_id()
    
    # Если администратор еще ни разу не запускал бота
    if not admin_id:
        await message.answer(
            "⚠️ Администратор еще не активировал прием заявок в системе. "
            "Пожалуйста, попробуйте отправить чек чуть позже."
        )
        logging.warning(f"Получен чек от {message.from_user.id}, но ADMIN_ID не установлен! Админ должен написать /start или /admin боту.")
        return

    user = message.from_user
    user_info = f"@{user.username}" if user.username else f"ID: {user.id} ({user.full_name})"
    
    # Берем фото в наилучшем качестве (последний элемент массива)
    photo_id = message.photo[-1].file_id

    caption_for_admin = (
        f"🧾 <b>Новый чек на проверку!</b>\n\n"
        f"👤 От пользователя: {user_info}\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"💰 Ожидаемая сумма: <b>119 RUB</b>\n\n"
        f"Выберите действие:"
    )

    try:
        # Отправляем фото администратору с кнопками выбора
        await bot.send_photo(
            chat_id=admin_id,
            photo=photo_id,
            caption=caption_for_admin,
            reply_markup=get_admin_decision_keyboard(user.id),
            parse_mode="HTML"
        )
        # Уведомляем зрителя
        await message.answer(
            "✅ <b>Ваш скриншот получен и отправлен на проверку!</b>\n"
            "Пожалуйста, ожидайте. Как только администратор проверит чек, бот пришлет вам ответ.",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка при отправке фото админу: {e}")
        await message.answer("❌ Произошла техническая ошибка при отправке чека. Попробуйте еще раз позже.")

# =====================================================================
# ОБРАБОТКА НАЖАТИЙ КНОПОК АДМИНИСТРАТОРОМ
# =====================================================================

@dp.callback_query(F.data.startswith("approve_"))
async def process_approve(callback: CallbackQuery):
    """Администратор нажал 'Принять в канал'."""
    user_id = int(callback.data.split("_")[1])
    
    try:
        # Отправляем зрителю пригласительную ссылку
        await bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 <b>Оплата подтверждена!</b>\n\n"
                "Добро пожаловать! Вот ваша пригласительная ссылка для входа в канал:\n"
                f"👉 {INVITE_LINK}"
            ),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        # Обновляем сообщение у администратора, убирая кнопки, чтобы не нажать дважды
        new_caption = callback.message.caption + "\n\n✅ <b>РЕШЕНИЕ: Принят в канал (ссылка отправлена).</b>"
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
        await callback.answer("Ссылка успешно отправлена зрителю!")
        
    except Exception as e:
        logging.error(f"Не удалось отправить ссылку пользователю {user_id}: {e}")
        await callback.answer("Ошибка: возможно, пользователь заблокировал бота.", show_alert=True)

@dp.callback_query(F.data.startswith("reject_"))
async def process_reject(callback: CallbackQuery):
    """Администратор нажал 'Не принимать в канал'."""
    user_id = int(callback.data.split("_")[1])
    
    try:
        # Просим зрителя проверить чек
        await bot.send_message(
            chat_id=user_id,
            text=(
                "❌ <b>Ваш чек не прошел проверку.</b>\n\n"
                "Пожалуйста, проверьте, нет ли ошибки в вашем чеке:\n"
                "— Сумма должна составлять ровно <b>119 рублей</b>.\n"
                "— Валюта перевода — только <b>российские рубли</b>.\n"
                "— На скриншоте должно быть четко видно статус успешной оплаты.\n\n"
                "Если вы отправили не тот скриншот, просто отправьте правильный в этот чат. Для повторной оплаты нажмите /pay."
            ),
            parse_mode="HTML"
        )
        
        # Обновляем сообщение у администратора
        new_caption = callback.message.caption + "\n\n❌ <b>РЕШЕНИЕ: Отклонено (отправлено уведомление об ошибке).</b>"
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
        await callback.answer("Зрителю отправлено уведомление об ошибке в чеке.")
        
    except Exception as e:
        logging.error(f"Не удалось отправить отказ пользователю {user_id}: {e}")
        await callback.answer("Ошибка: возможно, пользователь заблокировал бота.", show_alert=True)

# =====================================================================
# ОБРАБОТКА ОСТАЛЬНЫХ СООБЩЕНИЙ (ТЕКСТ, ДОКУМЕНТЫ И Т.Д.)
# =====================================================================

@dp.message(F.document)
async def handle_document(message: types.Message):
    """Если пользователь отправил чек файлом (PDF или картинкой без сжатия)."""
    await message.answer(
        "⚠️ Пожалуйста, отправьте чек именно как <b>фотографию (скриншот)</b>, а не файлом/документом.\n"
        "Сделайте скриншот экрана с чеком и прикрепите его как обычное фото.",
        parse_mode="HTML"
    )

@dp.message()
async def handle_unknown(message: types.Message):
    """Ответ на любой непонятный текст от пользователя."""
    await message.answer(
        "Я не совсем понял ваше сообщение 🤖\n\n"
        "Если вы уже оплатили 119 рублей, просто <b>отправьте скриншот чека</b> в этот чат.\n"
        "Если вам нужна ссылка на оплату — нажмите /pay.\n"
        "Если нужна помощь — нажмите /help.",
        parse_mode="HTML"
    )

# =====================================================================
# ЗАПУСК БОТА
# =====================================================================
async def main():
    logging.info("Запуск Бот Айда!...")
    # Удаляем вебхуки и пропускаем старые накопившиеся сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную.")
