import os
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT.parent / ".env", override=False)
MODEL_NAME = "gpt-6-luna"
# Project comparison rates worked out from observed PydanticAI provider costs.
PRICE_INPUT_PER_M = 0.10
PRICE_CACHED_INPUT_PER_M = 0.025
PRICE_OUTPUT_PER_M = 0.50
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
KEY_FOUND = bool(PORTKEY_API_KEY)
ACCESS_CODE = os.getenv("ACCESS_CODE", "").strip()
INVITE_CODE = os.getenv("INVITE_CODE", "").strip()
ADMIN_CODE = os.getenv("ADMIN_CODE", "").strip()
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "saathi-demo")
TEACHER_DAILY_BUDGET_USD = float(os.getenv("TEACHER_DAILY_BUDGET_USD", "0.50"))
APP_URL = os.getenv("APP_URL", "").rstrip('/')
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "")
ADMIN_CODE = os.getenv("ADMIN_CODE", "").strip()
DAILY_BUDGET_USD = float(os.getenv("DAILY_BUDGET_USD", "1.00"))
DEMO_MODE = os.getenv("DEMO_MODE", "").strip().lower() not in {"false", "0", "no", "off"} and not os.getenv("RENDER")
DB_PATH = Path(os.getenv("SAATHI_DB_PATH", str(ROOT / "saathi.db")))


def find_portkey_key(repo_root: Path = ROOT) -> str | None:
    """Find a key in the repository first, then its parent, without printing it."""
    local = dotenv_values(repo_root / ".env").get("PORTKEY_API_KEY")
    parent = dotenv_values(repo_root.parent / ".env").get("PORTKEY_API_KEY")
    return local or parent or os.getenv("PORTKEY_API_KEY")
