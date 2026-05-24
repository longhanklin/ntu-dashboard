import streamlit as st
from supabase import create_client
import os
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import datetime

# 讀取環境變數
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        .limit(5000)\
        .execute()
    return pd.DataFrame(res.data)

df_youbike = load_youbike()
df_weather = load_weather()
df_history = load_youbike_history()

if df_youbike.empty:
    st.warning("資料庫目前沒有資料，請稍後再試")
    st.stop()

# ── 用座標判斷台大校內 ──
# 台大校園邊界（新生南路、辛亥路、基隆路、羅斯福路所圍）
NTU_BOUNDS = {
    "lat_min": 25.007,
    "lat_max": 25.021,
    "lng_min": 121.532,
    "lng_max": 121.543,
}

# 師大公館校區座標範圍
SHIDA_BOUNDS = {
    "lat_min": 25.007,
    "lat_max": 25.013,
    "lng_min": 121.528,
    "lng_max": 121.533,
}

def classify_station(row):
    lat, lng = row["lat"], row["lng"]
    if (NTU_BOUNDS["lat_min"] <= lat <= NTU_BOUNDS["lat_max"] and
            NTU_BOUNDS["lng_min"] <= lng <= NTU_BOUNDS["lng_max"]):
        return "台大校內"
    elif (SHIDA_BOUNDS["lat_min"] <= lat <= SHIDA_BOUNDS["lat_max"] and
            SHIDA_BOUNDS["lng_min"] <= lng <= SHIDA_BOUNDS["lng_max"]):
        return "師大公館校區"
    else:
        return "公館周邊"

df_youbike["區域"] = df_youbike.apply(classify_station, axis=1)

# ── 天氣區塊 ──
st.subheader("🌤 目前天氣")
if not df_weather.empty:
    df_nearby = df_weather[df_weather["location"].str.contains("臺北|大安|文山|中正", na=False)]
    if not df_nearby.empty:
        cols = st.columns(len(df_nearby))
        for i, (_, row) in enumerate(df_nearby.iterrows()):
            with cols[i]:
                temp = f"{row['temperature']}°C" if row['temperature'] else "無資料"
                hum = f"{row['humidity']}%" if row['humidity'] else "無資料"
                st.metric(label=row['location'], value=temp, delta=f"濕度 {hum}")

st.divider()

# ── 地圖 ──
st.subheader("🗺 YouBike 即時地圖")

# 區域篩選按鈕
col1, col2, col3, col4 = st.columns(4)
with col1:
    show_all = st.button("📍 全部顯示", use_container_width=True)
with col2:
    show_ntu = st.button("🏫 台大校內", use_container_width=True)
with col3:
    show_shida = st.button("🏛 師大公館", use_container_width=True)
with col4:
    show_public = st.button("🏙 公館周邊", use_container_width=True)

if "map_filter" not in st.session_state:
    st.session_state.map_filter = "全部"

if show_all:
    st.session_state.map_filter = "全部"
elif show_ntu:
    st.session_state.map_filter = "台大校內"
elif show_shida:
    st.session_state.map_filter = "師大公館校區"
elif show_public:
    st.session_state.map_filter = "公館周邊"

current_filter = st.session_state.map_filter
st.caption(f"目前顯示：**{current_filter}**")

df_map = df_youbike if current_filter == "全部" else df_youbike[df_youbike["區域"] == current_filter]

# 統計
total_bikes = int(df_map["available_bikes"].sum())
total_docks = int(df_map["total_docks"].sum())
overall_ratio = total_bikes / total_docks * 100 if total_docks > 0 else 0

stat1, stat2, stat3 = st.columns(3)
stat1.metric("範圍內站點數", f"{len(df_map)} 站")
stat2.metric("可借車總數", f"{total_bikes} 台")
stat3.metric("整體可借率", f"{overall_ratio:.1f}%")

# 地圖中心根據篩選自動調整
map_centers = {
    "全部": [25.014, 121.537],
    "台大校內": [25.014, 121.537],
    "師大公館校區": [25.010, 121.530],
    "公館周邊": [25.012, 121.533],
}
zoom_levels = {"全部": 15, "台大校內": 16, "師大公館校區": 16, "公館周邊": 15}

m = folium.Map(
    location=map_centers[current_filter],
    zoom_start=zoom_levels[current_filter]
)

for _, row in df_map.iterrows():
    if row['lat'] and row['lng']:
        ratio = row['available_bikes'] / row['total_docks'] if row['total_docks'] > 0 else 0
        color = "#2ecc71" if ratio > 0.5 else "#f39c12" if ratio > 0.2 else "#e74c3c"

        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(
                f"<b>{row['station_name'].replace('YouBike2.0_', '')}</b><br>"
                f"區域：{row['區域']}<br>"
                f"可借：{row['available_bikes']} 台<br>"
                f"總格：{row['total_docks']} 格<br>"
                f"可借率：{ratio*100:.0f}%",
                max_width=200
            )
        ).add_to(m)

st_folium(m, width=None, height=520)
st.caption("🟢 充足（>50%）　🟠 偏少（20-50%）　🔴 快沒了（<20%）")

st.divider()

# ── 趨勢圖 ──
st.subheader("📈 YouBike 歷史趨勢")

stations = df_history["station_name"].unique().tolist() if not df_history.empty else []

if stations:
    region_col1, region_col2, region_col3 = st.columns(3)
    with region_col1:
        if st.button("⭐ 台大熱門站", use_container_width=True):
            st.session_state.selected_stations = [s for s in stations if any(k in s for k in ["椰林", "小福", "總圖", "第二學生"])]
    with region_col2:
        if st.button("🚉 公館捷運站", use_container_width=True):
            st.session_state.selected_stations = [s for s in stations if "公館站" in s]
    with region_col3:
        if st.button("🔄 清除選擇", use_container_width=True):
            st.session_state.selected_stations = stations[:3]

    if "selected_stations" not in st.session_state:
        st.session_state.selected_stations = stations[:3]

    selected = st.multiselect(
        "選擇站點（可多選）",
        options=stations,
        default=[s for s in st.session_state.selected_stations if s in stations]
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
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("歷史資料累積中，請稍後再查看趨勢圖")

st.divider()

# ── 即時排行 ──
st.subheader("🏆 目前可借車排行")

rank_filter = st.radio(
    "篩選區域",
    ["全部", "台大校內", "師大公館校區", "公館周邊"],
    horizontal=True
)

df_rank = df_youbike.copy() if rank_filter == "全部" else df_youbike[df_youbike["區域"] == rank_filter].copy()
df_rank["使用率(%)"] = ((df_rank["total_docks"] - df_rank["available_bikes"]) / df_rank["total_docks"] * 100).round(1)
df_rank = df_rank.sort_values("available_bikes", ascending=False).head(10)
df_rank = df_rank[["station_name", "區域", "available_bikes", "total_docks", "使用率(%)"]]
df_rank.columns = ["站點", "區域", "可借車數", "總車格", "使用率(%)"]
st.dataframe(df_rank, use_container_width=True, hide_index=True)
