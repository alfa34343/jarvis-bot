import os
import json
import logging
import datetime
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TELEGRAM_BOT_TOKEN = "8806683131:AAEb_SHZtJls5yz_3oeI-mYeh0hQgze-gt0"
GROQ_API_KEY = "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"
NEWS_API_KEY = "3c6d92a2bbdf4a4ea7ca348cb4c5e63d"
MASTER_CHAT_ID = None

class KeepAlive(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"JARVIS ONLINE")
    def log_message(self, format, *args):
        pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), KeepAlive)
    server.serve_forever()

def is_master(update):
    if MASTER_CHAT_ID is None:
        return True
    return update.effective_chat.id == MASTER_CHAT_ID

TASKS_FILE = "tasks.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f)

def ask_groq(message, extra=""):
    system = f"""You are JARVIS, personal AI of Master Lakshya only.
Always call user Master or Master Lakshya.
Be sharp, loyal, helpful like JARVIS from Iron Man.
Help with CAT exam, IBPS exam, business, freelancing, drafting messages.
{extra}
Today: {datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")}"""
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama3-70b-8192", "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ], "max_tokens": 1024}, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"System error Master: {e}"

def get_news():
    try:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&pageSize=1&apiKey={NEWS_API_KEY}", timeout=10)
        a = r.json()["articles"][0]
        return f"Top News Master:\n\n{a['title']}\n{a['source']['name']}\n\n{a.get('description','')}"
    except Exception as e:
        return f"Could not fetch news Master: {e}"

def start(update, context):
    update.message.reply_text(f"JARVIS ONLINE\n\nGood day Master Lakshya. All systems operational.\n\nYour Chat ID: {update.effective_chat.id}\n\nType /help for commands.")

def help_cmd(update, context):
    if not is_master(update): return
    update.message.reply_text("JARVIS Commands\n\n/news - Top news\n/tasks - Your tasks\n/addtask - Add task\n/cleartasks - Clear tasks\n/exam - Practice question\n/draft - Draft message\n\nOr just talk to me!")

def news_cmd(update, context):
    if not is_master(update): return
    update.message.reply_text(get_news())

def tasks_cmd(update, context):
    if not is_master(update): return
    tasks = load_tasks()
    if not tasks:
        update.message.reply_text("No tasks Master. Use /addtask Study Math 5PM")
        return
    msg = "Your Tasks Master:\n\n"
    for i, t in enumerate(tasks, 1):
        msg += f"{i}. {t['task']}"
        if t.get("time"): msg += f" — {t['time']}"
        msg += "\n"
    update.message.reply_text(msg)

def addtask_cmd(update, context):
    if not is_master(update): return
    if not context.args:
        update.message.reply_text("Example: /addtask Study Math 5:00 PM")
        return
    args = context.args
    time_str = ""
    if len(args) >= 2 and ("AM" in args[-1].upper() or "PM" in args[-1].upper()):
        time_str = f"{args[-2]} {args[-1]}"
        task_str = " ".join(args[:-2])
    else:
        task_str = " ".join(args)
    tasks = load_tasks()
    tasks.append({"task": task_str, "time": time_str})
    save_tasks(tasks)
    update.message.reply_text(f"Task added Master!\n{task_str}" + (f"\nTime: {time_str}" if time_str else ""))

def cleartasks_cmd(update, context):
    if not is_master(update): return
    save_tasks([])
    update.message.reply_text("All tasks cleared Master.")

def exam_cmd(update, context):
    if not is_master(update): return
    update.message.reply_text("Generating question Master...")
    r = ask_groq("Give one hard CAT or IBPS exam question with 4 options A B C D and answer with explanation.")
    update.message.reply_text(r)

def draft_cmd(update, context):
    if not is_master(update): return
    if not context.args:
        update.message.reply_text("Example: /draft message to Rohan about meeting tomorrow")
        return
    req = " ".join(context.args)
    update.message.reply_text("Drafting Master...")
    r = ask_groq(f"Draft this for Master Lakshya: {req}. Make it professional and ready to send.")
    update.message.reply_text(r)

def handle_msg(update, context):
    if not is_master(update):
        update.message.reply_text("Access Denied. I serve only Master Lakshya.")
        return
    r = ask_groq(update.message.text)
    update.message.reply_text(r)

def main():
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_server, daemon=True).start()
    print("JARVIS ONLINE")
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("news", news_cmd))
    dp.add_handler(CommandHandler("tasks", tasks_cmd))
    dp.add_handler(CommandHandler("addtask", addtask_cmd))
    dp.add_handler(CommandHandler("cleartasks", cleartasks_cmd))
    dp.add_handler(CommandHandler("exam", exam_cmd))
    dp.add_handler(CommandHandler("draft", draft_cmd))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
