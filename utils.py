import json
import asyncio
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")

async def save_user_message(user_id: int, message: str) -> None:
    user_file = DATA_DIR / f"{user_id}.json"
    data = []
    if user_file.exists():
        try:
            data = json.loads(user_file.read_text(encoding="utf-8"))
        except:
            data = []
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "message": message
    }
    data.append(entry)
    user_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
