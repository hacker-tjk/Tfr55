import random
import re
import os
import sqlite3
import requests
import urllib.parse
from aiogram import types, Dispatcher
from huggingface_hub import InferenceClient
from bs4 import BeautifulSoup
import config

# Настройки
HF_TOKEN = "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"
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"
TEXT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

client = InferenceClient(token=HF_TOKEN)

# --- РАБОТА С БАЗОЙ ДАННЫХ (ПАМЯТЬ) ---
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
    # Храним только последние 10 сообщений, чтобы бот не тупил
    cursor.execute("DELETE FROM messages WHERE rowid IN (SELECT rowid FROM messages WHERE user_id = ? ORDER BY rowid DESC LIMIT -1 OFFSET 10)", (user_id,))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM messages WHERE user_id = ?", (user_id,))
    history = [{"role": r, "content": c} for r, c in cursor.fetchall()]
    conn.close()
    return history

# --- ФУНКЦИЯ ПОИСКА НОВОСТЕЙ (КАК GOOGLE) ---
def search_news(query):
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}+новости"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Собираем заголовки (упрощенно)
        headlines = [g.text for g in soup.find_all('h3')][:3]
        if headlines:
            return "\n".join([f"🗞 {h}" for h in headlines])
        return "Ничего свежего не найдено."
    except:
        return "Ошибка поиска новостей."

# --- ОБРАБОТЧИКИ ---
async def on_message(message: types.Message):
    if message.is_command(): return
    
    user_id = message.from_user.id
    init_db() # Убедимся, что база создана
    
    # Сохраняем ID пользователя для статистики
    conn = sqlite3.connect('bot_memory.db')
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    user_count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.commit()
    conn.close()

    # Обновляем статус: показываем количество юзеров
    await message.bot.send_chat_action(message.chat.id, action="typing")

    text_lower = message.text.lower()

    # 1. Если просят НОВОСТИ
    if any(word in text_lower for word in ["новости", "news", "хабар", "что нового"]):
        news = search_news(message.text)
        await message.answer(f"🔍 Мой поиск нашел следующее:\n\n{news}\n\n— AI 🧠 IMAGE HD")
        return

    # 2. Если просят КАРТИНКУ
    if any(word in text_lower for word in ["нарисуй", "сурат", "photo", "картинка"]):
        prompt = text_lower.replace("нарисуй", "").replace("сурат", "").strip()
        await message.bot.send_chat_action(message.chat.id, action="upload_photo")
        image = client.text_to_image(prompt, model=IMAGE_MODEL)
        path = f"img_{user_id}.png"
        image.save(path)
        await message.answer_photo(open(path, "rb"), caption="🎨 Готово! [AI 🧠 IMAGE HD]")
        os.remove(path)
        return

    # 3. ПРОСТОЙ РАЗГОВОР С ПАМЯТЬЮ
    is_bad = any(word in text_lower for word in config.BAD_WORDS.keys())
    history = get_history(user_id)
    
    system_prompt = f"Ты — AI 🧠 IMAGE HD. Создатель: ANONYMOUS (Таджикистан). Тон: {'дерзкий' if is_bad else 'серьезный'}. Помни контекст."
    
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message.text}]
    
    try:
        response = client.chat_completion(messages, model=TEXT_MODEL, max_tokens=500).choices[0].message.content
        save_history(user_id, "user", message.text)
        save_history(user_id, "assistant", response)
        await message.answer(f"{response}\n\n— AI 🧠 IMAGE HD")
    except:
        await message.answer("Система занята.")

async def cmd_admin(message: types.Message):
    conn = sqlite3.connect('bot_memory.db')
    count = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    conn.close()
    await message.answer(f"📊 Всего пользователей в базе: {count}")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=["admin"])
    dp.register_message_handler(on_message, content_types=['text'])
