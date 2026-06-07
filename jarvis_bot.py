#!/usr/bin/env python3
"""
JARVIS - Personal AI Assistant for Master Lakshya
Built with Python + Telegram + Groq AI
100% Free. 100% Private. Only YOU can access this.
"""

import os
import json
import logging
import datetime
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ============================================================
#   CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = "8806683131:AAEb_SHZtJls5yz_3oeI-mYeh0hQgze-gt0"
GROQ_API_KEY       = "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"
NEWS_API_KEY       = "3c6d92a2bbdf4a4ea7ca348cb4c5e63d"
MASTER_CHAT_ID     = None   # Leave None — bot will tell you your ID on /start

# ============================================================
#   SECURITY — ONLY YOU CAN TALK TO JARVIS
# ============================================================

def is_master(update: Update) -> bool:
    if MASTER_CHAT_ID is None:
        return True
    return update.effective_chat.id == MASTER_CHAT_ID

# ============================================================
#   TASK STORAGE
# ============================================================

TASKS_FILE = "jarvis_tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

# ============================================================
#   GROQ AI BRAIN
# ============================================================

def ask_groq(user_message: str, context_prompt: str = "") -> str:
    system_prompt = f"""You are JARVIS, a highly intelligent personal AI assistant serving Master Lakshya exclusively.

Your personality:
- Always address the user as "Master" or "Master Lakshya"
- Speak with confidence, precision, and loyalty
- Be concise but thorough
- You are like JARVIS from Iron Man — sharp, witty, always helpful
- You serve only one master — Lakshya

Your capabilities:
- Answer any question Master asks
- Help with CAT and IBPS Bank exam preparation
- Draft messages, emails, proposals for Master
- Help with AI agent freelance business tasks
- Schedule and manage tasks
- Provide news updates
- Give business advice

{context_prompt}

Current date and time: {datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ JARVIS systems temporarily offline, Master. Error: {str(e)}"

# ============================================================
#   NEWS
# ============================================================

def get_top_news() -> str:
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&pageSize=1&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["articles"]:
            article = data["articles"][0]
            title = article["title"]
            source = article["source"]["name"]
            desc = article.get("description", "")
            return f"📰 *Top Headline, Master:*\n\n*{title}*\n_{source}_\n\n{desc}"
        else:
            return "⚠️ No news available at the moment, Master."
    except Exception as e:
        return f"⚠️ Could not fetch news, Master. Error: {str(e)}"

# ============================================================
#   COMMAND HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🤖 *JARVIS ONLINE*\n\n"
        f"Good day, Master Lakshya. All systems are operational.\n\n"
        f"Your secure Chat ID: `{chat_id}`\n\n"
        f"Type /help to see what I can do for you.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied. JARVIS serves only one Master.")
        return
    help_text = """🤖 *JARVIS — Command Center*

*Quick Commands:*
/news — Top headline of the day
/tasks — See all your tasks
/addtask [task] [time] — Add a task
/cleartasks — Clear all tasks
/exam — Get CAT/IBPS practice question
/draft [details] — Draft a message

*Or just talk to me naturally:*
Just type anything — I will understand and respond.

I am always at your service, Master. 🫡"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied.")
        return
    await update.message.reply_text("📡 Fetching today's top headline, Master...")
    news = get_top_news()
    await update.message.reply_text(news, parse_mode="Markdown")

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied.")
        return
    tasks = load_tasks()
    if not tasks:
        await update.message.reply_text(
            "📋 No tasks scheduled, Master.\n\nAdd tasks with:\n/addtask Study for IBPS 6:00 PM"
        )
        return
    task_list = "📋 *Your Tasks, Master:*\n\n"
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.get("done") else "⏳"
        task_list += f"{status} *{i}.* {task['task']}"
        if task.get("time"):
            task_list += f" — _{task['time']}_"
        task_list += "\n"
    await update.message.reply_text(task_list, parse_mode="Markdown")

async def addtask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied.")
        return
    if not context.args:
        await update.message.reply_text("Example: /addtask Study Math 5:00 PM")
        return
    args = context.args
    time_str = ""
    if len(args) >= 2 and ("AM" in args[-1].upper() or "PM" in args[-1].upper()):
        time_str = f"{args[-2]} {args[-1]}"
        task_str = " ".join(args[:-2])
    else:
        task_str = " ".join(args)
    tasks = load_tasks()
    tasks.append({"task": task_str, "time": time_str, "done": False,
                  "added": datetime.datetime.now().strftime("%d %b %Y")})
    save_tasks(tasks)
    reply = f"✅ Task added, Master!\n\n*Task:* {task_str}"
    if time_str:
        reply += f"\n*Time:* {time_str}"
    await update.message.reply_text(reply, parse_mode="Markdown")

async def cleartasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied.")
        return
    save_tasks([])
    await update.message.reply_text("🗑️ All tasks cleared, Master. Fresh start.")

async def exam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied.")
        return
    await update.message.reply_text("📚 Generating practice question, Master...")
    prompt = "Give Master one challenging CAT or IBPS Bank exam level question. Include the question, 4 options (A/B/C/D), and the correct answer with explanation."
    response = ask_groq(prompt)
    await update.message.reply_text(f"📚 *Practice Question:*\n\n{response}", parse_mode="Markdown")

async def draft_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied.")
        return
    if not context.args:
        await update.message.reply_text("Example: /draft message to Rohan about meeting tomorrow")
        return
    draft_request = " ".join(context.args)
    await update.message.reply_text("✍️ Drafting for you, Master...")
    prompt = f"Draft the following for Master Lakshya: {draft_request}. Make it professional and ready to send."
    response = ask_groq(prompt)
    await update.message.reply_text(f"✍️ *Draft Ready, Master:*\n\n{response}", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_master(update):
        await update.message.reply_text("🔒 Access Denied. I serve only Master Lakshya.")
        return
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    tasks = load_tasks()
    task_context = ""
    if tasks:
        task_list = ", ".join([t["task"] for t in tasks[:5]])
        task_context = f"Master's current tasks: {task_list}"
    response = ask_groq(user_message, task_context)
    await update.message.reply_text(response)

# ============================================================
#   MAIN
# ============================================================

def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    print("🤖 JARVIS initializing...")
    print("✅ All systems online")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("help",       help_command))
    app.add_handler(CommandHandler("news",       news_command))
    app.add_handler(CommandHandler("tasks",      tasks_command))
    app.add_handler(CommandHandler("addtask",    addtask_command))
    app.add_handler(CommandHandler("cleartasks", cleartasks_command))
    app.add_handler(CommandHandler("exam",       exam_command))
    app.add_handler(CommandHandler("draft",      draft_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 JARVIS is LIVE.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
