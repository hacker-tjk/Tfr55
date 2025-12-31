from pathlib import Path

TOKEN = "8505740315:AAHF0_gJXf8z_DRWN3TbOg3ofyoIShIJguA"
BOT_NAME = "AI 🧠 IMAGE HD"
COMPANY = "ANONYMOUS from Tajikistan"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

BAD_WORDS = {
    "ты тупой": ["сам тупой", "пашол нафиг", "сам нафиг"],
    "иди нахуй": ["сам иди нахуй", "пошёл вон"],
}

TEXTS = {
    "ru": {
        "start": "<b>Привет!</b>\nЯ - нейросеть AI 🧠 IMAGE HD от ANONYMOUS.\n/help",
        "help": "/image <текст>\n/video <текст>\n/start",
        "bad_response": "Так себя вести некрасиво: {}",
        "no_prompt": "✏️ Пожалуйста, добавьте описание.",
    },
    "tj": {
        "start": "<b>Салом!</b>\nМан AI 🧠 IMAGE HD аз ANONYMOUS.\n/help",
        "help": "/image <матн>\n/video <матн>\n/start",
        "bad_response": "Рафтори шумо бад аст: {}",
        "no_prompt": "✏️ Лутфан матнро нависед.",
    },
    "en": {
        "start": "<b>Hello!</b>\nI am AI 🧠 IMAGE HD by ANONYMOUS.\n/help",
        "help": "/image <text>\n/video <text>\n/start",
        "bad_response": "Unacceptable behavior: {}",
        "no_prompt": "✏️ Please provide text.",
    }
}

# Список провайдеров, которые реально поддерживают текстовые запросы в g4f
WORKING_PROVIDERS = ["Blackbox", "DeepInfra", "ChatGptEs", "Cloudflare"]