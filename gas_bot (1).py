import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8703894037:AAEUJUcDQnJsP1PI6W22diDnSsLW_i6CMgg"
ADMIN_CHAT_ID = 6267432226

PRODUCTS = {
    "metan_60": {"name": "🟢 Metan balon 60L", "price": 150},
    "metan_90": {"name": "🟢 Metan balon 90L", "price": 150},
    "propan_42": {"name": "🔵 Propan balon 42L", "price": 60},
    "propan_47": {"name": "🔵 Propan balon 47L", "price": 60},
    "reduktor": {"name": "⚙️ Reduktor", "price": 45},
    "injektor": {"name": "🔩 Injektor", "price": 90},
    "shlang": {"name": "🟡 Shlang", "price": 15},
    "gofra": {"name": "🔧 Stago gofra", "price": 100},
}

def menu_keyboard():
    buttons = []
    for key, val in PRODUCTS.items():
        buttons.append([InlineKeyboardButton(f"{val['name']} — ${val['price']}", callback_data=f"p_{key}")])
    buttons.append([InlineKeyboardButton("🛒 Savatcha", callback_data="cart")])
    buttons.append([InlineKeyboardButton("✅ Buyurtma berish", callback_data="order")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['cart'] = []
    context.user_data['state'] = 'menu'
    await update.message.reply_text(
        "🚗 Avto Gaz Uskunalari\n\nMahsulot tanlang:",
        reply_markup=menu_keyboard()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    cart = context.user_data.get('cart', [])

    if data.startswith("p_"):
        key = data[2:]
        product = PRODUCTS.get(key)
        if not product:
            return
        context.user_data['selected'] = key
        context.user_data['state'] = 'quantity'
        await query.message.reply_text(
            f"{product['name']} — ${product['price']}\n\nNechta kerak? Raqam yozing:"
        )

    elif data == "cart":
        if not cart:
            await query.message.reply_text("Savatcha bo'sh! Mahsulot tanlang:", reply_markup=menu_keyboard())
            return
        text = "Savatingiz:\n\n"
        total = 0
        for item in cart:
            s = item['price'] * item['qty']
            total += s
            text += f"• {item['name']} x{item['qty']} = ${s}\n"
        text += f"\nJami: ${total}"
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Buyurtma berish", callback_data="order")],
            [InlineKeyboardButton("🗑 Savatchani tozalash", callback_data="clear")],
            [InlineKeyboardButton("⬅️ Menyu", callback_data="menu")],
        ]))

    elif data == "clear":
        context.user_data['cart'] = []
        await query.message.reply_text("Savatcha tozalandi!", reply_markup=menu_keyboard())

    elif data == "order":
        if not cart:
            await query.message.reply_text("Avval mahsulot tanlang!", reply_markup=menu_keyboard())
            return
        context.user_data['state'] = 'contact'
        await query.message.reply_text("Telefon raqamingizni yozing:\nMasalan: +998901234567")

    elif data == "menu":
        context.user_data['state'] = 'menu'
        await query.message.reply_text("Mahsulot tanlang:", reply_markup=menu_keyboard())

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state', 'menu')
    text = update.message.text

    if state == 'quantity':
        if not text.isdigit() or int(text) < 1:
            await update.message.reply_text("Iltimos to'g'ri raqam kiriting:")
            return
        qty = int(text)
        key = context.user_data.get('selected')
        if not key:
            return
        product = PRODUCTS[key]
        cart = context.user_data.get('cart', [])
        found = False
        for item in cart:
            if item['key'] == key:
                item['qty'] += qty
                found = True
                break
        if not found:
            cart.append({'key': key, 'name': product['name'], 'price': product['price'], 'qty': qty})
        context.user_data['cart'] = cart
        context.user_data['state'] = 'menu'
        total = sum(i['price'] * i['qty'] for i in cart)
        await update.message.reply_text(
            f"✅ Qo'shildi!\n{product['name']} x{qty}\nJami: ${total}",
            reply_markup=menu_keyboard()
        )

    elif state == 'contact':
        context.user_data['phone'] = text
        context.user_data['state'] = 'address'
        await update.message.reply_text("Manzilingizni yozing:")

    elif state == 'address':
        cart = context.user_data.get('cart', [])
        phone = context.user_data.get('phone', '-')
        user = update.message.from_user
        total = sum(i['price'] * i['qty'] for i in cart)

        await update.message.reply_text(
            "✅ Buyurtmangiz qabul qilindi!\nTez orada bog'lanamiz 📲",
            reply_markup=menu_keyboard()
        )

        order_text = f"🛒 YANGI BUYURTMA!\n\n👤 {user.full_name}\n📞 {phone}\n📍 {text}\n\n"
        for item in cart:
            order_text += f"• {item['name']} x{item['qty']} = ${item['price']*item['qty']}\n"
        order_text += f"\n💰 Jami: ${total}"

        try:
            await context.bot.send_message(ADMIN_CHAT_ID, order_text)
        except Exception as e:
            logging.error(f"Xato: {e}")

        context.user_data['cart'] = []
        context.user_data['state'] = 'menu'

    else:
        await update.message.reply_text("Mahsulot tanlang:", reply_markup=menu_keyboard())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    print("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
