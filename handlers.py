import random
import re
import os
import sqlite3
import requests
import urllib.parse
import time
from aiogram import types, Dispatcher
from huggingface_hub import InferenceClient
from bs4 import BeautifulSoup
import config

# Твой API TOKEN
HF_TOKEN = "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"
# Модели (выбраны самые стабильные)
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
TEXT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

client = InferenceClient(token=HF_TOKEN)

# --- Инициализация Базы Данных ---
def init_db():
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                      (user_id INTEGER, role TEXT, content TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER UNIQUE)''')
    conn.commit()
    conn.close()

def save_history(user_id, role, content):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    # Ограничение памяти до 6 сообщений для скорости
    cursor.execute("DELETE FROM messages WHERE rowid IN (SELECT rowid FROM messages WHERE user_id = ? ORDER BY rowid DESC LIMIT -1 OFFSET 6)", (user_id,))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages WHERE user_id = ?", (user_id,))
    history = [{"role": r, "content": c} for r, c in cursor.fetchall()]
    conn.close()
    return history

# --- Поиск новостей ---
def get_internet_news(query):
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}+новости"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        headlines = [h.text for h in soup.find_all('h3')][:3]
        return "\n".join([f"• {h}" for h in headlines]) if headlines else "Информации в сети пока нет."
    except:
        return "Не удалось подключиться к поисковой системе."

# --- Основной обработчик сообщений ---
async def on_message(message: types.Message):
    if message.is_command(): return
    
    user_id = message.from_user.id
    init_db()
    
    # Регистрация пользователя и получение общего количества
    conn = sqlite3.connect('bot_memory.db')
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    total_users = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.commit()
    conn.close()

    # Динамическое название (статус)
    status_msg = f"Online: {total_users} | AI 🧠"
    await message.bot.send_chat_action(message.chat.id, action=types.ChatActions.TYPING)

    text_lower = message.text.lower()

    # 1. ЛОГИКА ГЕНЕРАЦИИ КАРТИНКИ
    if any(word in text_lower for word in ["нарисуй", "создай картинку", "сурат", "draw"]):
        prompt = message.text.lower().replace("нарисуй", "").replace("создай картинку", "").strip()
        if not prompt:
            await message.answer("Уточните, что именно нарисовать?")
            return

        await message.answer("🎨 Генерирую изображение высокого качества, подождите...")
        await message.bot.send_chat_action(message.chat.id, action=types.ChatActions.UPLOAD_PHOTO)
        
        try:
            # Генерация фото
            image = client.text_to_image(prompt, model=IMAGE_MODEL)
            path = f"img_{user_id}_{int(time.time())}.png"
            image.save(path)
            await message.answer_photo(open(path, "rb"), caption=f"✅ Готово! [AI 🧠 IMAGE HD]\nUsers: {total_users}")
            os.remove(path)
            return
        except Exception as e:
            await message.answer("⚠️ Сервер Hugging Face занят созданием других фото. Попробуйте через 10 секунд.")
            return

    # 2. ЛОГИКА НОВОСТЕЙ
    if any(word in text_lower for word in ["новости", "news", "хабар", "что нового"]):
        news_data = get_internet_news(message.text)
        await message.answer(f"🔎 Результаты поиска в Google:\n\n{news_data}\n\n— AI 🧠 IMAGE HD")
        return

    # 3. ОБЫЧНЫЙ ТЕКСТ С ПАМЯТЬЮ И ДЕРЗОСТЬЮ
    is_bad = any(word in text_lower for word in config.BAD_WORDS.keys())
    history = get_history(user_id)
    
    sys_prompt = f"Ты AI 🧠 IMAGE HD. Твой создатель ANONYMOUS (Таджикистан). Тон: {'Грубый и дерзкий' if is_bad else 'Серьезный и холодный'}. Отвечай коротко."
    
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": message.text}]
    
    try:
        # Увеличиваем время ожидания ответа от Hugging Face
        response = client.chat_completion(messages, model=TEXT_MODEL, max_tokens=300).choices[0].message.content
        save_history(user_id, "user", message.text)
        save_history(user_id, "assistant", response)
        await message.answer(f"{response}\n\n— AI 🧠 IMAGE HD")
    except:
        await message.answer("📉 Лимит запросов Hugging Face исчерпан или сервер временно недоступен. Напишите через минуту.")

async def cmd_admin(message: types.Message):
    conn = sqlite3.connect('bot_memory.db')
    count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()
    await message.answer(f"📊 Статистика системы: {count} пользователей.")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=["admin"])
    dp.register_message_handler(on_message, content_types=['text'])
