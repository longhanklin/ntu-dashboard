import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import datetime

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(
    page_title="台大公館人潮儀表板",
    page_icon="🚲",
    layout="wide"
)

st.title("🚲 台大公館人潮儀表板")
st.caption(f"資料每30分鐘自動更新｜最後載入：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── 讀取資料 ──
@st.cache_data(ttl=300)
def load_youbike():
    res = supabase.table("youbike_data")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(82)\
        .execute()
    return pd.DataFrame(res.data)

@st.cache_data(ttl=300)
def load_weather():
    res = supabase.table("weather_data")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(19)\
        .execute()
    return pd.DataFrame(res.data)

@st.cache_data(ttl=300)
def load_youbike_history():
    res = supabase.table("youbike_data")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(2000)\
        .execute()
    return pd.DataFrame(res.data)

df_youbike = load_youbike()
df_weather = load_weather()
df_history = load_youbike_history()

# ── 天氣區塊 ──
st.subheader("🌤 目前天氣")
df_nearby = df_weather[df_weather["location"].str.contains("臺北|大安|文山|中正")]
cols = st.columns(len(df_nearby))
for i, (_, row) in enumerate(df_nearby.iterrows()):
    with cols[i]:
        temp = f"{row['temperature']}°C" if row['temperature'] else "無資料"
        hum = f"{row['humidity']}%" if row['humidity'] else "無資料"
        st.metric(label=row['location'], value=temp, delta=f"濕度 {hum}")

st.divider()

# ── 地圖 ──
st.subheader("🗺 YouBike 即時地圖")

m = folium.Map(location=[25.017, 121.537], zoom_start=15)

for _, row in df_youbike.iterrows():
    if row['lat'] and row['lng']:
        ratio = row['available_bikes'] / row['total_docks'] if row['total_docks'] > 0 else 0
        color = "green" if ratio > 0.5 else "orange" if ratio > 0.2 else "red"
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=f"{row['station_name']}<br>可借：{row['available_bikes']}台 / 共{row['total_docks']}格"
        ).add_to(m)

st_folium(m, width=None, height=500)
st.caption("🟢 充足（>50%）　🟠 偏少（20-50%）　🔴 快沒了（<20%）")

st.divider()

# ── 趨勢圖 ──
st.subheader("📈 YouBike 歷史趨勢")

default_stations = stations[:3] if len(stations) >= 3 else stations

selected = st.multiselect(
    "選擇站點",
    options=stations,
    default=default_stations
)

if selected:
    df_selected = df_history[df_history["station_name"].isin(selected)]
    fig = px.line(
        df_selected,
        x="recorded_at",
        y="available_bikes",
        color="station_name",
        title="各站可借車數量趨勢",
        labels={"recorded_at": "時間", "available_bikes": "可借車數", "station_name": "站點"}
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── 即時排行 ──
st.subheader("🏆 目前可借車排行")
df_rank = df_youbike[["station_name", "available_bikes", "total_docks"]].copy()
df_rank["使用率"] = ((df_rank["total_docks"] - df_rank["available_bikes"]) / df_rank["total_docks"] * 100).round(1)
df_rank = df_rank.sort_values("available_bikes", ascending=False).head(10)
df_rank.columns = ["站點", "可借車數", "總車格", "使用率(%)"]
st.dataframe(df_rank, use_container_width=True, hide_index=True)