import json
import logging
import os
import random
import sys

from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai
import httpx
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from db import engine
from models import Category, Question

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

COMMANDS = {
    "/start": "Show main menu keyboard",
    "/play": "Get a random trivia question",
    "/quizzes": "Browse available quiz categories",
    "/help": "Show this list of commands",
}

TOPIC, COUNT = range(2)

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["👤 Profile", "🎮 Take Quiz"],
            ["📚 Quizzes", "📝 Create Quiz"],
            ["✨ Generate Quiz"],
        ],
        resize_keyboard=True,
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Welcome to Quiz Bot! Use the keyboard buttons below to navigate:",
        reply_markup=get_main_menu_keyboard(),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = [f"{cmd} - {desc}" for cmd, desc in COMMANDS.items()]
    await update.message.reply_text("Available commands:\n" + "\n".join(lines))

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_message = update.message if update.message else update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/questions/random")
            if response.status_code != 200:
                await target_message.reply_text("❌ Failed to fetch a question. Make sure the API server is running.")
                return
            q = response.json()
    except Exception as e:
        logging.error(f"Error fetching question: {e}")
        await target_message.reply_text("❌ Error connecting to question service.")
        return

    q_id = q["id"]
    text = f"❓ *{q['text']}*\n\n_(Difficulty: {q['difficulty']})_"

    keyboard = []
    for idx, choice in enumerate(q["choices"]):
        callback_data = f"ans:{q_id}:{idx}"
        keyboard.append([InlineKeyboardButton(choice, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await target_message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    uname = f"@{user.username}" if user.username else "N/A"
    text = (
        f"👤 *User Profile*\n\n"
        f"• Name: {user.full_name}\n"
        f"• Username: {uname}\n"
        f"• Telegram ID: `{user.id}`\n"
        f"• Status: Active Player 🎮"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def create_quiz_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📝 *Create a Quiz*\n\n"
        "To add your own quiz questions to the bot database, you can use the seed script or API endpoint.\n"
        "Contact the bot administrator to add new trivia categories and questions!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def quizzes_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with Session(engine) as session:
        categories = session.query(Category).all()

    if not categories:
        await update.message.reply_text("No quiz categories available yet.")
        return

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(f"{cat.emoji} {cat.name}", callback_data=f"cat:{cat.id}")])

    await update.message.reply_text(
        "📚 *Available Quizzes*\n\nSelect a category to play:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat:"):
        cat_id = int(data.split(":")[1])
        with Session(engine) as session:
            q = session.scalars(select(Question).where(Question.category_id == cat_id).order_by(func.random())).first()
            if not q:
                await query.message.reply_text("No questions found in this category.")
                return

            q_id = q.id
            text = f"❓ *{q.text}*\n\n_(Difficulty: {q.difficulty})_"
            keyboard = []
            for idx, choice in enumerate(q.choices):
                keyboard.append([InlineKeyboardButton(choice, callback_data=f"ans:{q_id}:{idx}")])

            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def start_gen_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("✨ What topic would you like the quiz to be about? (e.g., Python, Space, History)")
    return TOPIC

async def receive_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["gen_topic"] = update.message.text
    await update.message.reply_text(f"Great! Topic: *{update.message.text}*.\n\nHow many questions do you need? (e.g., 1 to 5)", parse_mode="Markdown")
    return COUNT

async def receive_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        count = int(update.message.text.strip())
        if count < 1 or count > 10:
            count = 3
    except ValueError:
        count = 3

    topic = context.user_data.get("gen_topic", "General Knowledge")
    await update.message.reply_text(f"⏳ Generating {count} question(s) about *{topic}* using AI...", parse_mode="Markdown")

    questions_list = []
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = (
                f"Generate {count} trivia questions about '{topic}'. "
                "Return ONLY a valid JSON array of objects. Each object must have keys: "
                "\"text\" (string), \"choices\" (array of exactly 4 strings), "
                "\"correct_index\" (integer 0 to 3), \"difficulty\" (string: 'easy', 'medium', or 'hard'). "
                "No markdown formatting, just raw JSON array."
            )
            response = model.generate_content(prompt)
            text_resp = response.text.strip()
            if text_resp.startswith("```"):
                text_resp = text_resp.split("```")[1]
                if text_resp.startswith("json"):
                    text_resp = text_resp[4:]
                text_resp = text_resp.strip()
            questions_list = json.loads(text_resp)
        except Exception as e:
            logging.error(f"AI generation batch error: {e}")

    if not questions_list:
        questions_list = [
            {"text": f"Sample question about {topic}?", "choices": ["Choice A", "Choice B", "Choice C", "Choice D"], "correct_index": 0, "difficulty": "medium"}
            for _ in range(count)
        ]

    try:
        with Session(engine) as session:
            cat = session.query(Category).filter_by(name=f"AI: {topic}").first()
            if not cat:
                cat = Category(name=f"AI: {topic}", emoji="🤖")
                session.add(cat)
                session.commit()

            saved_ids = []
            for q_data in questions_list:
                new_q = Question(
                    category_id=cat.id,
                    text=q_data["text"],
                    choices=q_data["choices"],
                    correct_index=int(q_data["correct_index"]),
                    difficulty=q_data.get("difficulty", "medium")
                )
                session.add(new_q)
                session.commit()
                saved_ids.append(new_q.id)
    except Exception as e:
        logging.error(f"DB save error: {e}")
        saved_ids = [9999]

    await update.message.reply_text(f"✅ Generated {len(questions_list)} questions for *{topic}*! Here is the first one:", parse_mode="Markdown")

    if questions_list:
        q_data = questions_list[0]
        q_id = saved_ids[0] if saved_ids else 1
        text = f"🤖 *{topic} Quiz* (1/{len(questions_list)})\n\n❓ *{q_data['text']}*\n\n_(Difficulty: {q_data.get('difficulty', 'medium')})_"
        keyboard = []
        for idx, choice in enumerate(q_data["choices"]):
            callback_data = f"ans:{q_id}:{idx}"
            keyboard.append([InlineKeyboardButton(choice, callback_data=callback_data)])
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    return ConversationHandler.END

async def cancel_gen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Quiz generation cancelled.")
    return ConversationHandler.END

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "👤 Profile":
        await profile_handler(update, context)
    elif text == "🎮 Take Quiz":
        await play_command(update, context)
    elif text == "📚 Quizzes":
        await quizzes_handler(update, context)
    elif text == "📝 Create Quiz":
        await create_quiz_handler(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "play":
        await play_command(update, context)
    elif data.startswith("cat:"):
        await handle_category_selection(update, context)
    elif data.startswith("ans:"):
        _, q_id_str, idx_str = data.split(":")
        await query.edit_message_text(
            text=f"{query.message.text}\n\n✅ You selected choice {int(idx_str) + 1} for question #{q_id_str}."
        )

def main() -> None:
    token = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    if not token:
        sys.exit("BOT_TOKEN or TELEGRAM_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✨ Generate Quiz$"), start_gen_quiz)],
        states={
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_topic)],
            COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel_gen)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play_command))
    app.add_handler(CommandHandler("quizzes", quizzes_handler))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
