import requests

r = requests.get('https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json')
data = r.json()

ntu = [s for s in data if '臺大' in s.get('sna','') 
       and '臺大醫院' not in s.get('sna','') 
       and '癌醫' not in s.get('sna','')]

lats = [float(s['latitude']) for s in ntu]
lngs = [float(s['longitude']) for s in ntu]

print('lat min:', min(lats), 'max:', max(lats))
print('lng min:', min(lngs), 'max:', max(lngs))
print('共', len(ntu), '站')

print('\n各站座標：')
for s in ntu:
    print(f"{s['sna']} | lat:{s['latitude']} lng:{s['longitude']}")