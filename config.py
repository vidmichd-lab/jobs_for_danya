import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROFILE_PATH = BASE_DIR / "profile.txt"
INSTRUCTION_PATH = BASE_DIR / "cover_letter_instruction.txt"
URLS_JSON = DATA_DIR / "urls.json"
SEEN_JOBS_JSON = DATA_DIR / "seen_jobs.json"
RESUME_PDF_URL = "https://danyavidmich.com/cv_vidmich_designer.pdf"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY", "")
YANDEX_IAM_TOKEN = os.environ.get("YANDEX_IAM_TOKEN", "")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID", "b1g6rst3sps7hhu8tqla")
YANDEX_MODEL_URI = os.environ.get("YANDEX_MODEL_URI", "gpt://b1g6rst3sps7hhu8tqla/aliceai-llm/latest")

DESIGN_KEYWORDS = [
    "design", "product design", "graphic design", "ux", "ui", "brand",
    "creative", "art director", "visual design", "design lead", "designer",
]

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)
