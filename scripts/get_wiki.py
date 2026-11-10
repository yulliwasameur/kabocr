import json, urllib.request, concurrent.futures as cf
def get(off):
    u = f"https://datasets-server.huggingface.co/rows?dataset=wikimedia/wikipedia&config=20231101.kab&split=train&offset={off}&length=100"
    for _ in range(3):
        try:
            return [r["row"]["text"] for r in json.load(urllib.request.urlopen(u, timeout=60))["rows"]]
        except Exception:
            pass
    return []
with cf.ThreadPoolExecutor(6) as ex:
    out = [t for part in ex.map(get, range(0, 5830, 100)) for t in part]
json.dump(out, open("kabwiki.json", "w"), ensure_ascii=False); print(len(out))
