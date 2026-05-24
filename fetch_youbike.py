import requests
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# 要的站點關鍵字
INCLUDE = ["臺大", "公館", "師大公館", "師範大學公館"]

# 排除不相關的學校
EXCLUDE = ["世新", "政治大學", "中國科技", "中華科技", "台北科技",
           "陽明交通", "國防大學", "德明", "銘傳", "東吳", "臺北醫學",
           "臺北健康", "臺北市立大學", "臺北教育", "臺北護理",
           "臺灣科技大學", "臺灣師範大學", "中國醫藥", "中華科技",
           "臺大醫院兒童", "臺大醫學院附設癌醫", "捷運臺大醫院"]

def fetch_youbike():
    print("抓取 YouBike 資料中...")
    r = requests.get("https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json")
    data = r.json()

    count = 0
    for station in data:
        name = station.get("sna", "")
        addr = station.get("ar", "")

        include = any(k in name for k in INCLUDE)
        exclude = any(k in name for k in EXCLUDE)

        if include and not exclude:
            supabase.table("youbike_data").insert({
                "station_name": name,
                "lat": float(station.get("latitude", 0)),
                "lng": float(station.get("longitude", 0)),
                "available_bikes": int(station.get("available_rent_bikes", 0)),
                "total_docks": int(station.get("Quantity", 0)),
                "recorded_at": station.get("updateTime")
            }).execute()

            print(f"  {name}: 可借{station.get('available_rent_bikes')}台 / 共{station.get('Quantity')}格")
            count += 1

    print(f"完成！共存入 {count} 個站點")

fetch_youbike()