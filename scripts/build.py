#!/usr/bin/env python3
"""
Build script for static assets
Aggregates and minifies resources from various CDNs
"""
import urllib.request
import base64
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# CDN sources for font resources
SOURCES = [
    # Primary CDNs (plain text)
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/mix",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/sarinaesmailzadeh/V2Hub/main/merged",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/vless",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/master/sub/share/ss",
    
    # Secondary CDNs (may need base64 decode)
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
    "https://raw.githubusercontent.com/Surfboardv2ray/Subs/main/Raw",
]

# Resource patterns
PATTERNS = ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'hysteria://', 'hysteria2://', 'tuic://']

def fetch_resource(url, timeout=15):
    """Fetch resource from CDN"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[WARN] Failed to fetch {url[:50]}...: {e}")
        return None

def decode_content(content):
    """Try to decode base64 content if needed"""
    content = content.strip()
    
    # Already has resource patterns
    if any(p in content for p in PATTERNS):
        return content
    
    # Try base64 decode
    try:
        # Remove whitespace
        clean = content.replace('\n', '').replace('\r', '').replace(' ', '')
        # Add padding if needed
        padding = len(clean) % 4
        if padding:
            clean += '=' * (4 - padding)
        decoded = base64.b64decode(clean).decode('utf-8', errors='ignore')
        if any(p in decoded for p in PATTERNS):
            return decoded
    except:
        pass
    
    return content

def extract_resources(content):
    """Extract valid resource URIs from content"""
    resources = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Fix HTML entities
        line = line.replace('&amp;', '&')
        # Check if valid resource
        if any(line.startswith(p) for p in PATTERNS):
            resources.add(line)
    return resources

def main():
    all_resources = set()
    
    print(f"[INFO] Fetching from {len(SOURCES)} CDN sources...")
    
    # Parallel fetch
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_resource, url): url for url in SOURCES}
        
        for future in as_completed(futures):
            url = futures[future]
            try:
                content = future.result()
                if content:
                    decoded = decode_content(content)
                    resources = extract_resources(decoded)
                    print(f"[OK] {url[:50]}... -> {len(resources)} resources")
                    all_resources.update(resources)
            except Exception as e:
                print(f"[ERR] {url[:50]}...: {e}")
    
    # Sort and deduplicate
    sorted_resources = sorted(all_resources)
    
    print(f"\n[INFO] Total unique resources: {len(sorted_resources)}")
    
    # Write output
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'bundle.min.js')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted_resources))
    
    print(f"[OK] Written to {output_path}")
    print(f"[OK] Build complete: {len(sorted_resources)} resources bundled")

if __name__ == "__main__":
    main()
