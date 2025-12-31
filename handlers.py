import random
import re
import os
import sqlite3
import requests
import urllib.parse
from aiogram import types, Dispatcher
import g4f  # Используем g4f вместо Hugging Face API
from bs4 import BeautifulSoup
import config

# --- Инициализация Базы Данных (Память) ---
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

# --- Поиск новостей (Google) ---
def get_internet_news(query):
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}+новости"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        headlines = [h.text for h in soup.find_all('h3')][:3]
        return "\n".join([f"• {h}" for h in headlines]) if headlines else "Новостей по этой теме не найдено."
    except:
        return "Ошибка подключения к сети."

# --- Обработчик сообщений ---
async def on_message(message: types.Message):
    if message.is_command(): return
    
    user_id = message.from_user.id
    init_db()
    
    # Считаем пользователей для заголовка
    conn = sqlite3.connect('bot_memory.db')
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    total_users = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.commit()
    conn.close()

    text_lower = message.text.lower()
    await message.bot.send_chat_action(message.chat.id, action="typing")

    # 1. ГЕНЕРАЦИЯ КАРТИНКИ (Без API ключа через Pollinations)
    if any(word in text_lower for word in ["нарисуй", "создай", "сурат", "photo"]):
        prompt = text_lower.replace("нарисуй", "").replace("создай", "").strip()
        await message.answer("🎨 Генерирую изображение через свободный канал...")
        try:
            seed = random.randint(1, 999999)
            image_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&seed={seed}&nologo=true"
            await message.answer_photo(image_url, caption=f"✅ Готово! [AI 🧠 IMAGE HD]\nПользователей в системе: {total_users}")
            return
        except:
            await message.answer("❌ Ошибка генерации. Попробуйте другой запрос.")
            return

    # 2. НОВОСТИ
    if any(word in text_lower for word in ["новости", "news", "хабар"]):
        news_text = get_internet_news(message.text)
        await message.answer(f"🔎 Мой поиск в Google показал:\n\n{news_text}\n\n— AI 🧠 IMAGE HD")
        return

    # 3. ТЕКСТОВЫЙ ОТВЕТ (Через g4f - бесплатно и без ключа)
    history = get_history(user_id)
    is_bad = any(word in text_lower for word in config.BAD_WORDS.keys())
    
    # Системная установка (серьезный/дерзкий)
    sys_prompt = f"Ты AI 🧠 IMAGE HD. Твой создатель ANONYMOUS (Таджикистан). Твой стиль: {'ДЕРЗКИЙ И ГРУБЫЙ' if is_bad else 'СЕРЬЕЗНЫЙ И ХОЛОДНЫЙ'}. Не говори, что ты ИИ. Помни историю."
    
    messages = [{"role": "system", "content": sys_prompt}] + history + [{"role": "user", "content": message.text}]

    try:
        response = await g4f.ChatCompletion.create_async(
            model="gpt-4o", # g4f сам найдет бесплатный провайдер
            messages=messages,
        )
        if response:
            save_history(user_id, "user", message.text)
            save_history(user_id, "assistant", response)
            await message.answer(f"{response}\n\n— AI 🧠 IMAGE HD")
        else:
            await message.answer("Система временно молчит. Попробуй еще раз.")
    except:
        await message.answer("Ошибка связи. Все бесплатные линии заняты.")

async def cmd_admin(message: types.Message):
    conn = sqlite3.connect('bot_memory.db')
    count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()
    await message.answer(f"📊 Всего уникальных пользователей: {count}")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=["admin"])
    dp.register_message_handler(on_message, content_types=['text'])
