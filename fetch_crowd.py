from livepopulartimes import get_populartimes_by_address
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

places = [
    "台北市中正區羅斯福路四段76號",        # 麥當勞公館
    "台北市中正區羅斯福路四段68號",        # 摩斯漢堡公館
    "台北市大安區羅斯福路三段316巷8弄3號",  # 古拉爵
    "台北市大安區羅斯福路三段283號",       # 星巴克公館
]

place_names = [
    "麥當勞公館店",
    "摩斯漢堡公館店", 
    "古拉爵公館店",
    "星巴克公館店",
]

for i, place in enumerate(places):
    print(f"抓取中：{place_names[i]}")
    try:
        data = get_populartimes_by_address(place)
        print(f"  完整資料：{data}")
        if data and data.get("coordinates", {}).get("lat"):
            popularity = data.get("current_popularity", 0)
            lat = data["coordinates"]["lat"]
            lng = data["coordinates"]["lng"]

            supabase.table("crowd_data").insert({
                "place_name": place_names[i],
                "lat": lat,
                "lng": lng,
                "current_popularity": popularity,
            }).execute()

            print(f"  人潮指數：{popularity}")
    except Exception as e:
        print(f"  錯誤：{e}")

print("完成！")