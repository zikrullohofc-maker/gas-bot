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
    "gofra": {"name": "🔧 Stago gofra (miya)", "price": 100},
}

def product_keyboard():
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
        "🚗 *Avto Gaz Uskunalari*\n\nMahsulot tanlang:",
        parse_mode="Markdown",
        reply_markup=product_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("p_"):
        key = data[2:]
        product = PRODUCTS[key]
        context.user_data['selected'] = key
        context.user_data['state'] = 'quantity'
        await query.edit_message_text(
            f"*{product['name']}*\n💵 Narx: ${product['price']}\n\nNechta kerak? Raqam yozing:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]])
        )

    elif data == "cart":
        cart = context.user_data.get('cart', [])
        if not cart:
            await query.edit_message_text("🛒 Savatcha bo'sh!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]]))
            return
        text = "🛒 *Savatingiz:*\n\n"
        total = 0
        for item in cart:
            s = item['price'] * item['qty']
            total += s
            text += f"• {item['name']} x{item['qty']} = ${s}\n"
        text += f"\n💰 *Jami: ${total}*"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Buyurtma berish", callback_data="order")],
            [InlineKeyboardButton("🗑 Tozalash", callback_data="clear")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]
        ]))

    elif data == "clear":
        context.user_data['cart'] = []
        await query.edit_message_text("🗑 Savatcha tozalandi!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="back")]]))

    elif data == "order":
        cart = context.user_data.get('cart', [])
        if not cart:
            await query.edit_message_text("❗ Avval mahsulot tanlang!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="back")]]))
            return
        context.user_data['state'] = 'contact'
        await query.edit_message_text("📞 Telefon raqamingizni yozing:\nMasalan: +998901234567")

    elif data == "back":
        context.user_data['state'] = 'menu'
        await query.edit_message_text(
            "🚗 *Avto Gaz Uskunalari*\n\nMahsulot tanlang:",
            parse_mode="Markdown",
            reply_markup=product_keyboard()
        )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state', 'menu')
    text = update.message.text

    if state == 'quantity':
        if not text.isdigit() or int(text) < 1:
            await update.message.reply_text("❗ To'g'ri raqam kiriting:")
            return
        qty = int(text)
        key = context.user_data['selected']
        product = PRODUCTS[key]
        cart = context.user_data.get('cart', [])
        for item in cart:
            if item['key'] == key:
                item['qty'] += qty
                break
        else:
            cart.append({'key': key, 'name': product['name'], 'price': product['price'], 'qty': qty})
        context.user_data['cart'] = cart
        context.user_data['state'] = 'menu'
        total = sum(i['price'] * i['qty'] for i in cart)
        await update.message.reply_text(
            f"✅ Qo'shildi: {product['name']} x{qty}\n💰 Jami: ${total}",
            reply_markup=product_keyboard()
        )

    elif state == 'contact':
        context.user_data['phone'] = text
        context.user_data['state'] = 'address'
        await update.message.reply_text("📍 Manzilingizni yozing:")

    elif state == 'address':
        context.user_data['address'] = text
        cart = context.user_data.get('cart', [])
        phone = context.user_data.get('phone', '-')
        address = text
        user = update.message.from_user
        total = sum(i['price'] * i['qty'] for i in cart)

        await update.message.reply_text(
            "✅ *Buyurtmangiz qabul qilindi!*\nTez orada bog'lanamiz 📲",
            parse_mode="Markdown",
            reply_markup=product_keyboard()
        )

        order_text = f"🛒 *YANGI BUYURTMA!*\n━━━━━━━━━━━━\n👤 {user.full_name}\n📞 {phone}\n📍 {address}\n━━━━━━━━━━━━\n"
        for item in cart:
            order_text += f"• {item['name']} x{item['qty']} = ${item['price']*item['qty']}\n"
        order_text += f"━━━━━━━━━━━━\n💰 *Jami: ${total}*"

        try:
            await context.bot.send_message(ADMIN_CHAT_ID, order_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Admin xabar yuborishda xato: {e}")

        context.user_data['cart'] = []
        context.user_data['state'] = 'menu'

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
