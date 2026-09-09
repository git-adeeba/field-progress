import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is missing from .env")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "SUPABASE_SERVICE_ROLE_KEY is missing from .env"
    )


print("ENV FILE:", ENV_FILE)
print("SERVICE ROLE KEY LOADED:", bool(SUPABASE_SERVICE_ROLE_KEY))
print(
    "SERVICE KEY SAME AS ANON:",
    SUPABASE_SERVICE_ROLE_KEY == SUPABASE_ANON_KEY,
)