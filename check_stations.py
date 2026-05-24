import requests

r = requests.get('https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json')
data = r.json()

keywords = ['臺大', '台大', '大學']
results = []

for s in data:
    name = s.get('sna', '')
    addr = s.get('ar', '')
    if any(k in name or k in addr for k in keywords):
        results.append(f"{name} | {addr}")

for r in sorted(results):
    print(r)

print(f"\n共 {len(results)} 站")