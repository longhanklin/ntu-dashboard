import streamlit as st
from supabase import create_client
import os
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import datetime, timezone, timedelta
import requests as req
import time

# ── 環境變數 ──
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TW_TZ = timezone(timedelta(hours=8))

st.set_page_config(
    page_title="台大公館人潮儀表板",
    page_icon="🚲",
    layout="wide"
)

BIKE_ANIMATION = """
<div style="display:flex;align-items:center;gap:14px;padding:12px 16px;
border-radius:12px;border:0.5px solid #e0e0e0;background:#f9f9f9;
width:fit-content;margin:8px 0;">
<svg width="64" height="40" viewBox="0 0 64 40" fill="none">
  <style>
    @keyframes ws{to{transform:rotate(360deg)}}
    @keyframes bb{0%,100%{transform:translateY(0)}50%{transform:translateY(-1.5px)}}
    @keyframes rd{from{stroke-dashoffset:0}to{stroke-dashoffset:-40}}
    @keyframes ps{to{transform:rotate(360deg)}}
    #wr{transform-origin:50px 28px;animation:ws 0.5s linear infinite}
    #wl{transform-origin:14px 28px;animation:ws 0.5s linear infinite}
    #rider-body{animation:bb 0.5s ease-in-out infinite}
    #pedal-group{transform-origin:30px 24px;animation:ps 0.5s linear infinite}
    #road{animation:rd 0.4s linear infinite}
  </style>
  <line id="road" x1="0" y1="36" x2="64" y2="36" stroke="#ccc" stroke-width="1.5" stroke-dasharray="6 4"/>
  <g id="wr">
    <circle cx="50" cy="28" r="9" stroke="#888" stroke-width="1.5" fill="none"/>
    <line x1="50" y1="19" x2="50" y2="37" stroke="#888" stroke-width="1"/>
    <line x1="41" y1="28" x2="59" y2="28" stroke="#888" stroke-width="1"/>
    <line x1="43.6" y1="21.6" x2="56.4" y2="34.4" stroke="#888" stroke-width="1"/>
    <line x1="56.4" y1="21.6" x2="43.6" y2="34.4" stroke="#888" stroke-width="1"/>
  </g>
  <g id="wl">
    <circle cx="14" cy="28" r="9" stroke="#888" stroke-width="1.5" fill="none"/>
    <line x1="14" y1="19" x2="14" y2="37" stroke="#888" stroke-width="1"/>
    <line x1="5" y1="28" x2="23" y2="28" stroke="#888" stroke-width="1"/>
    <line x1="7.6" y1="21.6" x2="20.4" y2="34.4" stroke="#888" stroke-width="1"/>
    <line x1="20.4" y1="21.6" x2="7.6" y2="34.4" stroke="#888" stroke-width="1"/>
  </g>
  <line x1="14" y1="28" x2="28" y2="14" stroke="#888" stroke-width="1.5"/>
  <line x1="28" y1="14" x2="50" y2="28" stroke="#888" stroke-width="1.5"/>
  <line x1="28" y1="14" x2="30" y2="28" stroke="#888" stroke-width="1.5"/>
  <line x1="24" y1="14" x2="34" y2="14" stroke="#888" stroke-width="2" stroke-linecap="round"/>
  <line x1="28" y1="14" x2="24" y2="10" stroke="#888" stroke-width="1.5"/>
  <line x1="22" y1="10" x2="27" y2="10" stroke="#888" stroke-width="2" stroke-linecap="round"/>
  <g id="rider-body">
    <circle cx="30" cy="5" r="3.5" fill="#555"/>
    <line x1="30" y1="8.5" x2="28" y2="16" stroke="#555" stroke-width="1.5"/>
    <line x1="28" y1="16" x2="24" y2="19" stroke="#555" stroke-width="1.5"/>
    <line x1="28" y1="16" x2="34" y2="14" stroke="#555" stroke-width="1.5"/>
    <g id="pedal-group">
      <line x1="30" y1="24" x2="25" y2="30" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
      <line x1="30" y1="24" x2="35" y2="30" stroke="#555" stroke-width="1.5" stroke-linecap="round"/>
      <circle cx="30" cy="24" r="2" fill="#555"/>
    </g>
  </g>
</svg>
<div>
  <div style="font-size:14px;font-weight:500;color:#333;">玩命抓取即時資料中</div>
  <div style="font-size:12px;color:#888;margin-top:2px;">正在更新，請稍後...</div>
</div>
</div>
"""

# ── fragment：輪詢 Actions 狀態，每5秒更新一次 ──
@st.fragment(run_every=5)
def pipeline_status_watcher():
    if not st.session_state.get("pipeline_running"):
        return

    try:
        runs_res = req.get(
            "https://api.github.com/repos/longhanklin/ntu-dashboard/actions/runs?per_page=1",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            },
            timeout=5
        )
        if runs_res.status_code == 200:
            runs = runs_res.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                status = latest.get("status")
                if status == "completed":
                    st.session_state.pipeline_running = False
                    st.cache_data.clear()
                    st.success("✅ 資料已是最新狀態！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.markdown(BIKE_ANIMATION, unsafe_allow_html=True)
    except Exception:
        pass

# ── 頂部標題 + 更新按鈕 ──
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("🚲 台大公館人潮儀表板")
with col_btn:
    st.write("")
    if st.button("⟳ 立即更新", use_container_width=True,
                 disabled=st.session_state.get("pipeline_running", False)):
        trigger_res = req.post(
            "https://api.github.com/repos/longhanklin/ntu-dashboard/actions/workflows/pipeline.yml/dispatches",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            },
            json={"ref": "master"},
            timeout=10
        )
        if trigger_res.status_code == 204:
            st.session_state.pipeline_running = True
            st.rerun()
        else:
            st.error(f"觸發失敗：{trigger_res.status_code}")

pipeline_status_watcher()

# ── 讀取資料（不快取，永遠抓最新）──
def load_youbike():
    res = supabase.table("youbike_data")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(200)\
        .execute()
    return pd.DataFrame(res.data)

def load_weather():
    res = supabase.table("weather_data")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(19)\
        .execute()
    return pd.DataFrame(res.data)

def load_youbike_history():
    res = supabase.table("youbike_data")\
        .select("*")\
        .order("recorded_at", desc=True)\
        .limit(10000)\
        .execute()
    return pd.DataFrame(res.data)

df_youbike = load_youbike()
df_weather = load_weather()
df_history = load_youbike_history()

if df_youbike.empty:
    st.warning("資料庫目前沒有資料，請稍後再試")
    st.stop()

latest_time = None
if not df_youbike.empty and "recorded_at" in df_youbike.columns:
    latest_raw = df_youbike["recorded_at"].max()
    try:
        latest_dt = datetime.fromisoformat(latest_raw)
        latest_time = latest_dt.strftime('%Y-%m-%d %H:%M')
    except:
        latest_time = str(latest_raw)[:16]

st.caption(f"資料每30分鐘自動更新｜資料時間：{latest_time or '讀取中...'}")

# ── 台大校內判斷 ──
NTU_BOUNDS = {
    "lat_min": 25.0130,
    "lat_max": 25.0225,
    "lng_min": 121.5285,
    "lng_max": 121.5480,
}

def classify_station(row):
    lat, lng = row["lat"], row["lng"]
    if (NTU_BOUNDS["lat_min"] <= lat <= NTU_BOUNDS["lat_max"] and
            NTU_BOUNDS["lng_min"] <= lng <= NTU_BOUNDS["lng_max"]):
        return "台大校內"
    else:
        return "公館周邊"

df_youbike["區域"] = df_youbike.apply(classify_station, axis=1)

# ── 天氣區塊 ──
st.subheader("🌤 目前天氣")
if not df_weather.empty:
    priority = ["大安區 - 臺灣大學", "中正區 - 臺北", "文山區 - 文山", "大安區 - 大安森林"]
    df_weather_show = df_weather[df_weather["location"].isin(priority)].copy()
    df_weather_show["sort"] = df_weather_show["location"].apply(
        lambda x: priority.index(x) if x in priority else 99
    )
    df_weather_show = df_weather_show.sort_values("sort")

    if not df_weather_show.empty:
        cols = st.columns(len(df_weather_show))
        for i, (_, row) in enumerate(df_weather_show.iterrows()):
            with cols[i]:
                temp = row['temperature']
                hum = row['humidity']
                temp_str = f"{temp}°C" if temp and float(temp) > 0 else "無資料"
                hum_str = f"{hum}%" if hum and float(hum) > 0 else "無資料"
                st.metric(label=row['location'], value=temp_str, delta=f"濕度 {hum_str}")

st.divider()

# ── 地圖 ──
st.subheader("🗺 YouBike 即時地圖")

col1, col2, col3 = st.columns(3)
with col1:
    show_all = st.button("📍 全部顯示", use_container_width=True)
with col2:
    show_ntu = st.button("🏫 台大校內", use_container_width=True)
with col3:
    show_public = st.button("🏙 公館周邊", use_container_width=True)

if "map_filter" not in st.session_state:
    st.session_state.map_filter = "全部"

if show_all:
    st.session_state.map_filter = "全部"
elif show_ntu:
    st.session_state.map_filter = "台大校內"
elif show_public:
    st.session_state.map_filter = "公館周邊"

current_filter = st.session_state.map_filter
st.caption(f"目前顯示：**{current_filter}**")

df_map = df_youbike if current_filter == "全部" else df_youbike[df_youbike["區域"] == current_filter]

total_bikes = int(df_map["available_bikes"].sum())
total_docks = int(df_map["total_docks"].sum())
overall_ratio = total_bikes / total_docks * 100 if total_docks > 0 else 0

stat1, stat2, stat3 = st.columns(3)
stat1.metric("站點數", f"{len(df_map)} 站")
stat2.metric("可借車總數", f"{total_bikes} 台")
stat3.metric("整體可借率", f"{overall_ratio:.1f}%")

map_centers = {
    "全部": [25.016, 121.537],
    "台大校內": [25.017, 121.537],
    "公館周邊": [25.014, 121.533],
}
zoom_levels = {"全部": 15, "台大校內": 16, "公館周邊": 15}

m = folium.Map(location=map_centers[current_filter], zoom_start=zoom_levels[current_filter])

for _, row in df_map.iterrows():
    if row['lat'] and row['lng']:
        ratio = row['available_bikes'] / row['total_docks'] if row['total_docks'] > 0 else 0
        color = "#2ecc71" if ratio > 0.5 else "#f39c12" if ratio > 0.2 else "#e74c3c"
        name = row['station_name'].replace('YouBike2.0_', '')

        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(
                f"<b>{name}</b><br>"
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
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        if st.button("⭐ 台大熱門站", use_container_width=True):
            st.session_state.selected_stations = [
                s for s in stations if any(k in s for k in ["椰林", "小福", "總圖", "第二學生"])
            ]
    with rc2:
        if st.button("🚉 公館捷運站", use_container_width=True):
            st.session_state.selected_stations = [s for s in stations if "公館站" in s]
    with rc3:
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
    ["全部", "台大校內", "公館周邊"],
    horizontal=True
)

df_rank = df_youbike.copy() if rank_filter == "全部" else df_youbike[df_youbike["區域"] == rank_filter].copy()
df_rank["使用率(%)"] = ((df_rank["total_docks"] - df_rank["available_bikes"]) / df_rank["total_docks"] * 100).round(1)
df_rank = df_rank.sort_values("available_bikes", ascending=False).head(10)
df_rank["station_name"] = df_rank["station_name"].str.replace("YouBike2.0_", "", regex=False)
df_rank = df_rank[["station_name", "區域", "available_bikes", "total_docks", "使用率(%)"]]
df_rank.columns = ["站點", "區域", "可借車數", "總車格", "使用率(%)"]
st.dataframe(df_rank, use_container_width=True, hide_index=True)