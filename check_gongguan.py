import requests

r = requests.get('https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json')
data = r.json()

# 公館周邊大範圍：先撒網撈出來看看
LAT_MIN = 25.005
LAT_MAX = 25.025
LNG_MIN = 121.525
LNG_MAX = 121.550

results = []
for s in data:
    lat = float(s.get('latitude', 0))
    lng = float(s.get('longitude', 0))
    if LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX:
        results.append(f"{s['sna']} | lat:{lat} lng:{lng}")

results.sort()
for r in results:
    print(r)
print(f"\n共 {len(results)} 站")