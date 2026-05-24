import requests
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

LAT_MIN = 24.998
LAT_MAX = 25.028
LNG_MIN = 121.518
LNG_MAX = 121.550

EXCLUDE = [
    "世新", "政治大學", "中國科技", "中華科技", "台北科技",
    "陽明交通", "國防大學", "德明", "東吳", "臺北醫學",
    "臺北市立大學", "臺北教育", "臺北護理", "中國醫藥",
    "臺大醫院兒童", "捷運臺大醫院", "敦化", "科技大樓站",
    "臺灣師範大學(浦城街)", "臺靜農",
    "臺灣師範大學(圖書館)", "臺北遠企", "癌醫中心"
]

def fetch_youbike():
    print("抓取 YouBike 資料中...")
    r = requests.get("https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json")
    data = r.json()

    count = 0
    for station in data:
        lat = float(station.get("latitude", 0))
        lng = float(station.get("longitude", 0))
        name = station.get("sna", "")

        in_range = LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX
        excluded = any(k in name for k in EXCLUDE)

        if in_range and not excluded:
            supabase.table("youbike_data").insert({
                "station_name": name,
                "lat": lat,
                "lng": lng,
                "available_bikes": int(station.get("available_rent_bikes", 0)),
                "total_docks": int(station.get("Quantity", 0)),
                "recorded_at": station.get("updateTime")
            }).execute()
            print(f"  {name}: 可借{station.get('available_rent_bikes')}台")
            count += 1

    print(f"完成！共存入 {count} 個站點")

fetch_youbike()