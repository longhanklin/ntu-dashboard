import requests
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
CWA_KEY = os.getenv("CWA_KEY")

def fetch_weather():
    print("抓取天氣資料中...")
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_KEY}"
    
    try:
        r = requests.get(url, timeout=15)  # 15秒 timeout
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"天氣 API 連線失敗，跳過：{e}")
        return  # 跳過，不讓整個 pipeline 崩潰

    stations = data["records"]["Station"]

    batch = []
    for station in stations:
        county = station.get("GeoInfo", {}).get("CountyName", "")
        if county != "臺北市":
            continue

        town = station.get("GeoInfo", {}).get("TownName", "")
        elements = station["WeatherElement"]
        temp = elements.get("AirTemperature", None)
        humidity = elements.get("RelativeHumidity", None)

        batch.append({
            "location": f"{town} - {station['StationName']}",
            "temperature": float(temp) if temp and float(temp) != -99 else None,
            "humidity": float(humidity) if humidity and float(humidity) != -99 else None,
            "weather_desc": town,
            "recorded_at": station.get("ObsTime", {}).get("DateTime")
        })

    if batch:
        supabase.table("weather_data").insert(batch).execute()
        print(f"完成！共存入 {len(batch)} 個測站")
    else:
        print("沒有資料可存入")