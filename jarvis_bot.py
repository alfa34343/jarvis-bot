import os
import json
import logging
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TELEGRAM_BOT_TOKEN = "8806683131:AAEb_SHZtJls5yz_3oeI-mYeh0hQgze-gt0"
GEMINI_API_KEY = "AQ.Ab8RN6JrsM27Wo8SqNsCQ3MDyvR6Jilk-TI8iXpHr7fAbphslg"
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

def ask_gemini(message):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"You are JARVIS, personal AI assistant of Master Lakshya. Always call him Master or Master Lakshya. Be sharp, helpful and loyal like JARVIS from Iron Man. Help with CAT exam, IBPS exam, business ideas, freelancing and drafting messages.\n\nUser message: {message}"
                        }
                    ]
                }
            ]
        }
        r = requests.post(url, json=payload, timeout=30)
        result = r.json()
        if "candidates" in result:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in result:
            return f"Error Master: {result['error']['message']}"
        else:
            return str(result)
    except Exception as e:
        return f"Connection error Master: {str(e)}"

def start(update, context):
    update.message.reply_text(f"JARVIS ONLINE\n\nGood day Master Lakshya. All systems operational.\n\nChat ID: {update.effective_chat.id}\n\nType /help for commands.")

def help_cmd(update, context):
    if not is_master(update): return
    update.message.reply_text("JARVIS Commands\n\n/tasks - Your tasks\n/addtask - Add task\n/cleartasks - Clear tasks\n/exam - Practice question\n/draft - Draft message\n\nOr just talk naturally!")

def tasks_cmd(update, context):
    if not is_master(update): return
    tasks = load_tasks()
    if not tasks:
        update.message.reply_text("No tasks Master.")
        return
    msg = "Tasks Master:\n\n"
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
    update.message.reply_text(f"Task added Master: {task_str}" + (f" at {time_str}" if time_str else ""))

def cleartasks_cmd(update, context):
    if not is_master(update): return
    save_tasks([])
    update.message.reply_text("Tasks cleared Master.")

def exam_cmd(update, context):
    if not is_master(update): return
    update.message.reply_text("Generating question Master...")
    r = ask_gemini("Give one hard CAT or IBPS exam question with 4 options A B C D and correct answer with explanation.")
    update.message.reply_text(r)

def draft_cmd(update, context):
    if not is_master(update): return
    if not context.args:
        update.message.reply_text("Example: /draft message to Rohan about meeting")
        return
    req = " ".join(context.args)
    update.message.reply_text("Drafting Master...")
    r = ask_gemini(f"Draft this message professionally: {req}")
    update.message.reply_text(r)

def handle_msg(update, context):
    if not is_master(update):
        update.message.reply_text("Access Denied.")
        return
    r = ask_gemini(update.message.text)
    update.message.reply_text(r)

def main():
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_server, daemon=True).start()
    print("JARVIS ONLINE - Powered by Gemini")
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
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
