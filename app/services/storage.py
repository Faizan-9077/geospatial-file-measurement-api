import json
from pathlib import Path


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DATABASE_FILE = DATA_DIR / "files.json"


def load_data() -> dict:
    if not DATABASE_FILE.exists():
        return {}

    with DATABASE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data: dict) -> None:
    with DATABASE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def save_file_record(file_id: str, record: dict) -> None:
    data = load_data()

    data[file_id] = record

    save_data(data)


def get_file_record(file_id: str) -> dict | None:
    data = load_data()

    return data.get(file_id)