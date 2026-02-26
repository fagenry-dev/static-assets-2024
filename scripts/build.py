#!/usr/bin/env python3
import urllib.request, urllib.parse, base64, os, re
from concurrent.futures import ThreadPoolExecutor, as_completed

SOURCES = [
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vless",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/ss",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
]
PATTERNS = ["vmess://", "vless://", "trojan://", "ss://", "ssr://", "hysteria://", "hysteria2://", "tuic://"]
CMAP = {"US":"🇺🇸","USA":"🇺🇸","DE":"🇩🇪","Germany":"🇩🇪","NL":"🇳🇱","FR":"🇫🇷","GB":"🇬🇧","UK":"🇬🇧","JP":"🇯🇵","SG":"🇸🇬","HK":"🇭🇰","KR":"🇰🇷","TW":"🇹🇼","CA":"🇨🇦","AU":"🇦🇺","RU":"🇷🇺","IN":"🇮🇳","TR":"🇹🇷","IR":"🇮🇷","FI":"🇫🇮","SE":"🇸🇪","PL":"🇵🇱","IT":"🇮🇹","ES":"🇪🇸","CH":"🇨🇭","CN":"🇨🇳"}
FLAG_RE = re.compile(r"[\U0001F1E0-\U0001F1FF]{2}")

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r: return r.read().decode("utf-8", errors="ignore")
    except: return None

def decode_b64(c):
    if any(p in c for p in PATTERNS): return c
    try:
        cl = c.strip().replace("\\n","").replace("\\r","")
        if len(cl)%4: cl += "="*(4-len(cl)%4)
        d = base64.b64decode(cl).decode("utf-8",errors="ignore")
        if any(p in d for p in PATTERNS): return d
    except: pass
    return c

def get_flag(uri):
    fl = FLAG_RE.findall(uri)
    if fl: return fl[0]
    for k,v in CMAP.items():
        if k.upper() in uri.upper(): return v
    return "🌐"

def rename(uri, i):
    flag = get_flag(uri)
    name = urllib.parse.quote(f"Underground Bro {flag} #{i}")
    base = uri.split("#")[0] if "#" in uri else uri
    return f"{base}#{name}"

def main():
    keys = []
    with ThreadPoolExecutor(10) as ex:
        for f in as_completed({ex.submit(fetch,u):u for u in SOURCES}):
            c = f.result()
            if c:
                for l in decode_b64(c).splitlines():
                    l = l.strip().replace("&amp;","&")
                    if any(l.startswith(p) for p in PATTERNS): keys.append(l)
    seen, unique = set(), []
    for k in keys:
        b = k.split("#")[0]
        if b not in seen: seen.add(b); unique.append(k)
    renamed = [rename(k,i) for i,k in enumerate(unique,1)]
    renamed.sort(key=lambda x: x.split("#")[-1])
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)),"assets","bundle.min.js")
    os.makedirs(os.path.dirname(out),exist_ok=True)
    with open(out,"w") as f: f.write("\\n".join(renamed))
    print(f"Done: {len(renamed)} keys")

if __name__=="__main__": main()

