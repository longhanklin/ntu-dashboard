from fetch_youbike import fetch_youbike
from fetch_weather import fetch_weather
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def cleanup_old_data():
    print("清理舊資料中...")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    supabase.table("youbike_data").delete().lt("recorded_at", cutoff).execute()
    supabase.table("weather_data").delete().lt("recorded_at", cutoff).execute()
    print("清理完成！")

print("=== 開始執行 Pipeline ===")
cleanup_old_data()
fetch_youbike()
fetch_weather()
print("=== Pipeline 完成 ===")