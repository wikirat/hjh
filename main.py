import asyncio
import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, InlineQueryHandler
from telegram.constants import ChatMemberStatus

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def format_downloads(downloads):
    if downloads >= 1000000000:
        return f"{downloads // 1000000000}B+"
    elif downloads >= 1000000:
        return f"{downloads // 1000000}M+"
    elif downloads >= 1000:
        return f"{downloads // 1000}K+"
    else:
        return str(downloads)

BOT_TOKEN = "8081835724:AAHxBWv8t63BKcA7wc7vQOKLF6DL2sFqwDY"
CHANNEL_ID = "@sinanunciosapkmods"
CHANNEL_URL = "https://t.me/sinanunciosapkmods"

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {"verified": False, "current_results": [], "current_index": 0}
    
    if not user_data[user_id]["verified"]:
        keyboard = [
            [InlineKeyboardButton("✅ Verificar", callback_data="verify")],
            [InlineKeyboardButton("📢 Canal", url=CHANNEL_URL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔒 Necesitas suscribirte a Apk Mods Vip para usar este bot.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "✅ ¡Ya estás verificado! Usa /search <nombre del mod> para buscar APKs.\n\n"
            "📱 También puedes usar el modo inline escribiendo @modsvip_bot <búsqueda> en cualquier chat."
        )

async def verify_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            user_data[user_id] = {"verified": True, "current_results": [], "current_index": 0}
            
            await query.edit_message_text(
                "✅ ¡Verificación exitosa! Ahora puedes usar el bot.\n\n"
                "🔍 Usa /search <nombre del mod> para buscar APKs.\n"
                "📱 También puedes usar el modo inline escribiendo @modsvip_bot <búsqueda> en cualquier chat."
            )
        else:
            keyboard = [
                [InlineKeyboardButton("✅ Verificar", callback_data="verify")],
                [InlineKeyboardButton("📢 Canal", url=CHANNEL_URL)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ No estás suscrito al canal. Por favor, únete primero y luego verifica.",
                reply_markup=reply_markup
            )
    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("✅ Verificar", callback_data="verify")],
            [InlineKeyboardButton("📢 Canal", url=CHANNEL_URL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Error al verificar. Asegúrate de estar suscrito al canal.",
            reply_markup=reply_markup
        )

async def search_apk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data or not user_data[user_id]["verified"]:
        keyboard = [
            [InlineKeyboardButton("✅ Verificar", callback_data="verify")],
            [InlineKeyboardButton("📢 Canal", url=CHANNEL_URL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔒 Necesitas suscribirte a Apk Mods Vip para usar este bot.",
            reply_markup=reply_markup
        )
        return
    
    if not context.args:
        await update.message.reply_text("🔍 Uso: /search <nombre del mod>\n\nEjemplo: /search whatsapp")
        return
    
    query = " ".join(context.args)
    
    await update.message.reply_text("🔍 Buscando APKs...")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://ws75.aptoide.com/api/7/apps/search/query={query}/limit=3"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'datalist' in data and 'list' in data['datalist'] and data['datalist']['list']:
                        user_data[user_id]["current_results"] = data['datalist']['list']
                        user_data[user_id]["current_index"] = 0
                        
                        await send_app_info(update, context, user_id, 0)
                    else:
                        await update.message.reply_text("❌ No se encontraron resultados para tu búsqueda.")
                else:
                    await update.message.reply_text("❌ Error al realizar la búsqueda. Intenta de nuevo.")
    except Exception as e:
        await update.message.reply_text("❌ Error de conexión. Intenta de nuevo más tarde.")

async def send_app_info(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, index: int):
    results = user_data[user_id]["current_results"]
    
    if index >= len(results):
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text("❌ No hay más resultados disponibles.")
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text("❌ No hay más resultados disponibles.")
        return
    
    app = results[index]
    
    name = app.get('name', 'Nombre no disponible')
    graphic = app.get('graphic')
    icon = app.get('icon', '')
    version = app.get('file', {}).get('vername', 'N/A')
    developer = app.get('developer', {}).get('name', 'N/A')
    downloads = format_downloads(app.get('stats', {}).get('downloads', 0))
    rating = app.get('stats', {}).get('rating', {}).get('avg', 0)
    path_alt = app.get('file', {}).get('path_alt', '')
    file_size = app.get('file', {}).get('filesize', 0)
    
    description = f"📦 Versión: {version}\n👨‍💻 Desarrollador: {developer}\n📊 Descargas: {downloads}\n⭐ Calificación: {rating}/5"
    
    max_size = 20 * 1024 * 1024
    
    keyboard = []
    
    if file_size <= max_size and path_alt:
        keyboard.append([InlineKeyboardButton("📥 Descargar APK", url=path_alt)])
        file_size_mb = round(file_size / (1024 * 1024), 1)
        message_text = f"📱 **{name}**\n\n{description}\n\n💾 Tamaño: {file_size_mb} MB\n\n⏳ Espera, en un momento pasaré el APK (máximo 20 MB)"
    else:
        keyboard.append([InlineKeyboardButton("🌐 Descargar desde Aptoide", url=path_alt)])
        file_size_mb = round(file_size / (1024 * 1024), 1) if file_size > 0 else "Desconocido"
        message_text = f"📱 **{name}**\n\n{description}\n\n💾 Tamaño: {file_size_mb} MB\n\n⚠️ Lo siento, el archivo pesa más de 20 MB, puedes descargarlo haciendo clic en el botón de abajo."
    
    if index < len(results) - 1:
        keyboard.append([InlineKeyboardButton("➡️ Siguiente", callback_data=f"next_{user_id}_{index + 1}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    image_url = graphic or icon
    
    if image_url:
        try:
            if hasattr(update, 'message') and update.message:
                await update.message.reply_photo(
                    photo=image_url,
                    caption=message_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_photo(
                    photo=image_url,
                    caption=message_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except:
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    message_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.message.reply_text(
                    message_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
    else:
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.message.reply_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def handle_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data.split('_')
    user_id = int(callback_data[1])
    index = int(callback_data[2])
    
    if query.from_user.id != user_id:
        await query.answer("❌ Este botón no es para ti.", show_alert=True)
        return
    
    await send_app_info(update, context, user_id, index)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    user_id = update.effective_user.id
    
    if user_id not in user_data or not user_data[user_id]["verified"]:
        results = [
            InlineQueryResultPhoto(
                id="verification_required",
                photo_url="https://via.placeholder.com/400x300/FF5722/FFFFFF?text=Verificacion+Requerida",
                thumbnail_url="https://via.placeholder.com/150x150/FF5722/FFFFFF?text=!",
                input_message_content=InputTextMessageContent(
                    message_text="🔒 Necesitas verificarte primero. Inicia el bot en privado."
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
        return
    
    if not query or len(query.strip()) < 2:
        results = [
            InlineQueryResultPhoto(
                id="help",
                photo_url="https://via.placeholder.com/400x300/2196F3/FFFFFF?text=Buscar+APKs",
                thumbnail_url="https://via.placeholder.com/150x150/2196F3/FFFFFF?text=?",
                input_message_content=InputTextMessageContent(
                    message_text="🔍 Escribe el nombre de la app que quieres buscar."
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://ws75.aptoide.com/api/7/apps/search/query={query}/limit=5"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    if 'datalist' in data and 'list' in data['datalist'] and data['datalist']['list']:
                        for i, app in enumerate(data['datalist']['list'][:5]):
                            name = app.get('name', 'Nombre no disponible')
                            graphic = app.get('graphic')
                            icon = app.get('icon', 'https://via.placeholder.com/400x300/4CAF50/FFFFFF?text=APK')
                            version = app.get('file', {}).get('vername', 'N/A')
                            developer = app.get('developer', {}).get('name', 'N/A')
                            downloads = format_downloads(app.get('stats', {}).get('downloads', 0))
                            rating = app.get('stats', {}).get('rating', {}).get('avg', 0)
                            path_alt = app.get('file', {}).get('path_alt', '')
                            
                            description = f"📦 Versión: {version}\n👨‍💻 Desarrollador: {developer}\n📊 Descargas: {downloads}\n⭐ Calificación: {rating}/5"
                            
                            image_url = graphic or icon
                            
                            keyboard = []
                            if path_alt:
                                keyboard.append([InlineKeyboardButton("📥 Descargar", url=path_alt)])
                            
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            
                            results.append(
                                InlineQueryResultPhoto(
                                    id=f"app_{i}",
                                    photo_url=image_url,
                                    thumbnail_url=image_url,
                                    title=f"📱 {name}",
                                    description=f"📦 v{version} | 👨‍💻 {developer} | 📊 {downloads}",
                                    input_message_content=InputTextMessageContent(
                                        message_text=f"📱 **{name}**\n\n{description}",
                                        parse_mode='Markdown'
                                    ),
                                    reply_markup=reply_markup
                                )
                            )
                    else:
                        results = [
                            InlineQueryResultPhoto(
                                id="no_results",
                                photo_url="https://via.placeholder.com/400x300/F44336/FFFFFF?text=Sin+Resultados",
                                thumbnail_url="https://via.placeholder.com/150x150/F44336/FFFFFF?text=X",
                                input_message_content=InputTextMessageContent(
                                    message_text=f"❌ No se encontraron resultados para: {query}"
                                )
                            )
                        ]
                    
                    await update.inline_query.answer(results, cache_time=30)
                else:
                    results = [
                        InlineQueryResultPhoto(
                            id="error",
                            photo_url="https://via.placeholder.com/400x300/FF9800/FFFFFF?text=Error",
                            thumbnail_url="https://via.placeholder.com/150x150/FF9800/FFFFFF?text=!",
                            input_message_content=InputTextMessageContent(
                                message_text="❌ Error al realizar la búsqueda."
                            )
                        )
                    ]
                    await update.inline_query.answer(results, cache_time=0)
    
    except Exception as e:
        results = [
            InlineQueryResultPhoto(
                id="connection_error",
                photo_url="https://via.placeholder.com/400x300/9C27B0/FFFFFF?text=Error+Conexion",
                thumbnail_url="https://via.placeholder.com/150x150/9C27B0/FFFFFF?text=!",
                input_message_content=InputTextMessageContent(
                    message_text="❌ Error de conexión. Intenta de nuevo."
                )
            )
        ]
        await update.inline_query.answer(results, cache_time=0)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search_apk))
    application.add_handler(CallbackQueryHandler(verify_user, pattern="^verify$"))
    application.add_handler(CallbackQueryHandler(handle_next, pattern="^next_"))
    application.add_handler(InlineQueryHandler(inline_query))
    
    print("🤖 Bot iniciado correctamente...")
    application.run_polling()

if __name__ == "__main__":
    main()
