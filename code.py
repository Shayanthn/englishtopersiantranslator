from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from gtts import gTTS
import os
import requests

TOKEN = "you bot api"
DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en/"
TRANSLATE_API = "https://api.mymemory.translated.net/get?q={}&langpair=en|fa"

# Function to fetch word data
async def get_word_data(word):
    response = requests.get(DICTIONARY_API + word)
    if response.status_code == 200:
        data = response.json()
        meanings = data[0].get("meanings", [])
        phonetics = data[0].get("phonetics", [])
        synonyms = data[0].get("meanings", [{}])[0].get("synonyms", [])
        collocations = data[0].get("meanings", [{}])[0].get("collocations", [])
        return meanings, phonetics, synonyms, collocations
    return None, None, None, None

# Function to translate text to Persian
async def translate_to_persian(text):
    response = requests.get(TRANSLATE_API.format(text))
    if response.status_code == 200:
        data = response.json()
        return data["responseData"]["translatedText"]
    return "ترجمه در دسترس نیست."

# Function to process word info
async def process_word(word):
    meanings, phonetics, synonyms, collocations = await get_word_data(word)
    if not meanings:
        return "❌ **کلمه یافت نشد!** لطفاً یک کلمه معتبر وارد کنید."
    
    message = f"📖 **{word.upper()}**\n\n"
    
    for meaning in meanings:
        part_of_speech = meaning.get("partOfSpeech", "نامشخص").capitalize()
        definition = meaning.get("definitions", [{}])[0].get("definition", "تعریفی موجود نیست.")
        translated_def = await translate_to_persian(definition)
        
        example = meaning.get("definitions", [{}])[0].get("example", "مثالی موجود نیست.")
        translated_example = await translate_to_persian(example)
        
        message += f"✨ **نوع کلمه:** {part_of_speech}\n📝 **معنی:** {definition} ({translated_def})\n📌 **مثال:** {example} ({translated_example})\n\n"

    if collocations:
        message += f"🔑 **Collocations:** {', '.join(collocations)}\n\n"
    
    if synonyms:
        message += f"🔗 **هم‌نشین‌ها:** {', '.join(synonyms)}\n\n"

    if phonetics:
        phonetic_text = phonetics[0].get('text', 'تلفظ موجود نیست')
        message += f"🔊 **تلفظ:** /{phonetic_text}/\n\n"

    return message

# Function to send pronunciation
async def send_pronunciation(update: Update, context: CallbackContext, word):
    tts = gTTS(word, lang='en')
    tts.save("word.mp3")
    chat_id = update.effective_chat.id
    await context.bot.send_voice(chat_id, voice=open("word.mp3", "rb"))
    os.remove("word.mp3")

# Function to handle messages
async def handle_message(update: Update, context: CallbackContext):
    word = update.message.text.strip()
    response = await process_word(word)
    keyboard = [
        [InlineKeyboardButton("🔊 تلفظ", callback_data=f'pronounce_{word}')],
        [InlineKeyboardButton("🔗 هم‌نشین‌ها", callback_data=f'synonyms_{word}')],
        [InlineKeyboardButton("📝 کلمه جدید", callback_data='new_word')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)

# Function to handle button clicks
async def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("pronounce_"):
        word = query.data.split("_")[1]
        await send_pronunciation(update, context, word)
    elif query.data.startswith("synonyms_"):
        word = query.data.split("_")[1]
        meanings, _, synonyms, _ = await get_word_data(word)
        if synonyms:
            synonyms_message = "🔗 **هم‌نشین‌ها:** " + ", ".join(synonyms)
        else:
            synonyms_message = "❌ **هیچ هم‌نشینی یافت نشد.**"
        await query.edit_message_text(synonyms_message)
    elif query.data == "new_word":
        await query.edit_message_text("🔍 **لطفاً یک کلمه جدید ارسال کنید.**")

# Function to start bot
async def start(update: Update, context: CallbackContext):
    message = (
        "👋 **سلام! من لغت یارم!**\n\n"
        "هر کلمه انگلیسی که بهم بدی، من معنیشو بهت میگم! 😎\n"
        "از هم‌نشین‌ها (Collocations) گرفته تا تلفظ و مثال‌های آکادمیک و جنرال.\n"
        "🔎 کافیست یک کلمه بفرستی، و من همه چیز رو در موردش بهت میگم!\n\n"
        "یادت باشه که میتونی تلفظ رو هم بشنوی و از هم‌نشین‌ها هم با خبر بشی. 🌟""powerd by : Shayan Taherkhani"
    )
    await update.message.reply_text(message, parse_mode="Markdown")

# Main function
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()
