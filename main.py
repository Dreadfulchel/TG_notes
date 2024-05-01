import os
import psycopg2
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

# Загрузка переменных из файла .env
load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Проверка наличия токена бота в .env
if TOKEN is None:
    raise Exception("Токен бота не найден в файле .env")

# Подключение к базе данных PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# Определение констант для состояний
SELECTING_TASK = 1

# Переменная для хранения порядкового номера задачи
task_counter = 1

# Функция для начала добавления задачи
def start_add_task(update, context):
    update.message.reply_text("Какую заметку записать?")
    return SELECTING_TASK

# Функция для добавления задачи
def add_task(update, context):
    global task_counter
    task_text = update.message.text
    cursor.execute("INSERT INTO tasks (\"task\") VALUES (%s)", (task_text,))
    conn.commit()
    update.message.reply_text(f"Задача {task_counter} добавлена!")
    task_counter += 1
    return ConversationHandler.END

# Функция для отмены операции добавления задачи
def cancel(update, context):
    update.message.reply_text("Добавление заметки отменено.")
    return ConversationHandler.END

# Функция обработки команды /tsk
def list_tasks(update, context):
    cursor.execute("SELECT task FROM tasks")
    tasks = cursor.fetchall()
    if tasks:
        task_list = "\n".join([f"{index+1}. {task[0]}" for index, task in enumerate(tasks)])
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Список задач:\n{task_list}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Список задач пуст.")

# Функция для удаления всех задач
def clean_tasks(update, context):
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    update.message.reply_text("Все задачи удалены.")

# Функция для обработки команды /start
def start(update, context):
    update.message.reply_text("Привет! Я бот задач. Используйте команду /help, чтобы узнать доступные команды.")

# Функция для обработки команды /help
def help(update, context):
    update.message.reply_text("Доступные команды:\n"
                              "/start - начать диалог\n"
                              "/help - получить справку\n"
                              "/add - добавить задачу\n"
                              "/tsk - вывести список задач\n"
                              "/clean - удалить все задачи")

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Добавление обработчика команды /tsk
    dispatcher.add_handler(CommandHandler("tsk", list_tasks))

    # Добавление обработчика команды /clean
    dispatcher.add_handler(CommandHandler("clean", clean_tasks))

    # Добавление обработчиков команд /start и /help
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))

    # Добавление ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', start_add_task)],
        states={
            SELECTING_TASK: [MessageHandler(Filters.text & ~Filters.command, add_task)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
