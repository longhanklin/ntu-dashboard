import requests
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# 公館台大附近的站點關鍵字
TARGET_AREAS = ["公館", "台大", "羅斯福", "新生南路", "辛亥"]

def fetch_youbike():
    print("抓取 YouBike 資料中...")
    r = requests.get("https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json")
    data = r.json()

    count = 0
    for station in data:
        name = station.get("sna", "")
        area = station.get("sarea", "")
        address = station.get("ar", "")

        # 篩選公館台大附近站點
        is_target = any(keyword in name or keyword in address 
                       for keyword in TARGET_AREAS)
        
        if is_target:
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