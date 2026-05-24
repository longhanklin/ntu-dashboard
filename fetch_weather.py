import requests
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
CWA_KEY = os.getenv("CWA_KEY")

# 我們要的區域
TARGET_STATIONS = ["臺北", "大安", "中正", "文山", "古亭", "公館", "新店"]

def fetch_weather():
    print("抓取天氣資料中...")

    # 自動氣象站（密度更高）
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={CWA_KEY}"
    r = requests.get(url)
    data = r.json()

    stations = data["records"]["Station"]
    count = 0

    for station in stations:
        name = station["StationName"]
        county = station.get("GeoInfo", {}).get("CountyName", "")
        town = station.get("GeoInfo", {}).get("TownName", "")

        # 只要台北市的站
        if county != "臺北市":
            continue

        elements = station["WeatherElement"]
        temp = elements.get("AirTemperature", None)
        humidity = elements.get("RelativeHumidity", None)
        rain = elements.get("Now", {}).get("Precipitation", None)

        supabase.table("weather_data").insert({
            "location": f"{town} - {name}",
            "temperature": float(temp) if temp and float(temp) != -99 else None,
            "humidity": float(humidity) if humidity and float(humidity) != -99 else None,
            "weather_desc": town,
            "recorded_at": station.get("ObsTime", {}).get("DateTime")
        }).execute()

        print(f"  {town} {name}：{temp}°C，濕度{humidity}%")
        count += 1

    print(f"完成！共存入 {count} 個測站")