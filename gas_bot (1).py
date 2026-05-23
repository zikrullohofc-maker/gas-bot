import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)

# === SOZLAMALAR ===
BOT_TOKEN = "8703894037:AAEUJUcDQnJsP1PI6W22diDnSsLW_i6CMgg"
ADMIN_CHAT_ID = 6267432226

# === MAHSULOTLAR ===
PRODUCTS = {
    "metan_60": {"name": "🟢 Metan balon 60L / Метан баллон 60Л", "price": 150},
    "metan_90": {"name": "🟢 Metan balon 90L / Метан баллон 90Л", "price": 150},
    "propan_42": {"name": "🔵 Propan balon 42L / Пропан баллон 42Л", "price": 60},
    "propan_47": {"name": "🔵 Propan balon 47L / Пропан баллон 47Л", "price": 60},
    "reduktor": {"name": "⚙️ Reduktor / Редуктор", "price": 45},
    "injektor": {"name": "🔩 Injektor / Инжектор", "price": 90},
    "shlang": {"name": "🟡 Shlang / Шланг", "price": 15},
    "gofra": {"name": "🔧 Stago gofra (miya) / Штаг гофра", "price": 100},
}

# Conversation states
CHOOSING, QUANTITY, CONTACT, ADDRESS = range(4)

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['cart'] = []

    text = (
        "🚗 *Avto Gaz Uskunalari / Авто Газовое Оборудование*\n\n"
        "Assalomu alaykum! Xush kelibsiz 👋\n"
        "Здравствуйте! Добро пожаловать 👋\n\n"
        "Mahsulot tanlang / Выберите товар:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=product_keyboard())


def product_keyboard():
    buttons = []
    for key, val in PRODUCTS.items():
        buttons.append([InlineKeyboardButton(f"{val['name']} — ${val['price']}", callback_data=f"product_{key}")])
    buttons.append([InlineKeyboardButton("🛒 Savatcha / Корзина", callback_data="cart")])
    buttons.append([InlineKeyboardButton("✅ Buyurtma berish / Оформить заказ", callback_data="order")])
    return InlineKeyboardMarkup(buttons)


# =====================
# Mahsulot tanlash
# =====================
async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data.replace("product_", "")
    product = PRODUCTS[key]
    context.user_data['selected'] = key

    text = (
        f"*{product['name']}*\n"
        f"💵 Narx / Цена: *${product['price']}*\n\n"
        "Nechta kerak? / Сколько штук нужно?\n"
        "Raqam yuboring / Напишите количество:"
    )
    await query.edit_message_text(text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga / Назад", callback_data="back")]]))
    return QUANTITY


async def get_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("❗ Iltimos, to'g'ri raqam kiriting / Пожалуйста, введите правильное число")
        return QUANTITY

    qty = int(text)
    key = context.user_data['selected']
    product = PRODUCTS[key]

    cart = context.user_data.get('cart', [])
    # Agar savatda bor bo'lsa, qo'shib yuboring
    for item in cart:
        if item['key'] == key:
            item['qty'] += qty
            break
    else:
        cart.append({'key': key, 'name': product['name'], 'price': product['price'], 'qty': qty})
    context.user_data['cart'] = cart

    total = sum(i['price'] * i['qty'] for i in cart)
    await update.message.reply_text(
        f"✅ Savatchaga qo'shildi / Добавлено в корзину!\n\n"
        f"*{product['name']}* x{qty} = ${product['price'] * qty}\n"
        f"💰 Jami / Итого: *${total}*\n\n"
        "Davom eting / Продолжайте:",
        parse_mode="Markdown",
        reply_markup=product_keyboard()
    )
    return CHOOSING


# =====================
# Savatcha
# =====================
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cart = context.user_data.get('cart', [])
    if not cart:
        await query.edit_message_text(
            "🛒 Savatcha bo'sh / Корзина пуста",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga / Назад", callback_data="back")]]))
        return

    text = "🛒 *Savatingiz / Ваша корзина:*\n\n"
    total = 0
    for item in cart:
        subtotal = item['price'] * item['qty']
        total += subtotal
        text += f"• {item['name']}\n  {item['qty']} x ${item['price']} = *${subtotal}*\n\n"
    text += f"💰 *Jami / Итого: ${total}*"

    buttons = [
        [InlineKeyboardButton("✅ Buyurtma berish / Оформить заказ", callback_data="order")],
        [InlineKeyboardButton("🗑 Savatchani tozalash / Очистить", callback_data="clear_cart")],
        [InlineKeyboardButton("⬅️ Orqaga / Назад", callback_data="back")],
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['cart'] = []
    await query.edit_message_text(
        "🗑 Savatcha tozalandi / Корзина очищена",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu / Главное меню", callback_data="back")]]))


# =====================
# Buyurtma
# =====================
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cart = context.user_data.get('cart', [])
    if not cart:
        await query.edit_message_text(
            "❗ Savatcha bo'sh! Avval mahsulot tanlang.\n❗ Корзина пуста! Сначала выберите товар.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga / Назад", callback_data="back")]]))
        return CHOOSING

    await query.edit_message_text(
        "📞 *Telefon raqamingizni yuboring / Отправьте номер телефона:*\n\n"
        "Masalan / Например: +998901234567",
        parse_mode="Markdown"
    )
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text(
        "📍 *Manzilingizni yuboring / Напишите ваш адрес:*\n\n"
        "Shahar, ko'cha / Город, улица",
        parse_mode="Markdown"
    )
    return ADDRESS


async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text

    cart = context.user_data.get('cart', [])
    phone = context.user_data.get('phone', '-')
    address = context.user_data.get('address', '-')
    user = update.message.from_user
    total = sum(i['price'] * i['qty'] for i in cart)

    # Mijozga xabar
    await update.message.reply_text(
        "✅ *Buyurtmangiz qabul qilindi! / Ваш заказ принят!*\n\n"
        "Tez orada siz bilan bog'lanamiz 📲\n"
        "Скоро свяжемся с вами 📲",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu / Главное меню", callback_data="back")]])
    )

    # Adminга xabar
    order_text = (
        f"🛒 *YANGI BUYURTMA / НОВЫЙ ЗАКАЗ!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Mijoz: {user.full_name}\n"
        f"🆔 Username: @{user.username or 'yoq'}\n"
        f"📞 Telefon: {phone}\n"
        f"📍 Manzil: {address}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Mahsulotlar:*\n"
    )
    for item in cart:
        order_text += f"• {item['name']} x{item['qty']} = ${item['price'] * item['qty']}\n"
    order_text += f"━━━━━━━━━━━━━━━━━━\n💰 *Jami: ${total}*"

    await context.bot.send_message(ADMIN_CHAT_ID, order_text, parse_mode="Markdown")
    context.user_data['cart'] = []
    return CHOOSING


# =====================
# Orqaga
# =====================
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['cart'] = context.user_data.get('cart', [])
    await query.edit_message_text(
        "🚗 *Avto Gaz Uskunalari*\n\nMahsulot tanlang / Выберите товар:",
        parse_mode="Markdown",
        reply_markup=product_keyboard()
    )
    return CHOOSING


# =====================
# MAIN
# =====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                CallbackQueryHandler(product_selected, pattern="^product_"),
                CallbackQueryHandler(show_cart, pattern="^cart$"),
                CallbackQueryHandler(order, pattern="^order$"),
                CallbackQueryHandler(clear_cart, pattern="^clear_cart$"),
                CallbackQueryHandler(back, pattern="^back$"),
            ],
            QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_quantity),
                CallbackQueryHandler(back, pattern="^back$"),
            ],
            CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact),
            ],
            ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_address),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    print("✅ Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
