#!/usr/bin/env python3
"""
Underground Bro Key Aggregator
Собирает ключи с 12+ источников, переименовывает и сортирует по странам
"""
import urllib.request
import urllib.parse
import base64
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Источники ключей (подписки и прямые списки)
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

# Паттерны VPN ключей
PATTERNS = ['vmess://', 'vless://', 'trojan://', 'ss://', 'ssr://', 'hysteria://', 'hysteria2://', 'tuic://']

# Маппинг стран на флаги
COUNTRY_FLAGS = {
    'US': '🇺🇸', 'USA': '🇺🇸', 'America': '🇺🇸', 'United': '🇺🇸',
    'DE': '🇩🇪', 'Germany': '🇩🇪', 'Deutschland': '🇩🇪',
    'NL': '🇳🇱', 'Netherlands': '🇳🇱', 'Holland': '🇳🇱',
    'FR': '🇫🇷', 'France': '🇫🇷',
    'GB': '🇬🇧', 'UK': '🇬🇧', 'Britain': '🇬🇧', 'England': '🇬🇧',
    'JP': '🇯🇵', 'Japan': '🇯🇵',
    'SG': '🇸🇬', 'Singapore': '🇸🇬',
    'HK': '🇭🇰', 'Hong': '🇭🇰',
    'KR': '🇰🇷', 'Korea': '🇰🇷',
    'TW': '🇹🇼', 'Taiwan': '🇹🇼',
    'CA': '🇨🇦', 'Canada': '🇨🇦',
    'AU': '🇦🇺', 'Australia': '🇦🇺',
    'RU': '🇷🇺', 'Russia': '🇷🇺',
    'IN': '🇮🇳', 'India': '🇮🇳',
    'TR': '🇹🇷', 'Turkey': '🇹🇷',
    'IR': '🇮🇷', 'Iran': '🇮🇷',
    'FI': '🇫🇮', 'Finland': '🇫🇮',
    'SE': '🇸🇪', 'Sweden': '🇸🇪',
    'NO': '🇳🇴', 'Norway': '🇳🇴',
    'PL': '🇵🇱', 'Poland': '🇵🇱',
    'IT': '🇮🇹', 'Italy': '🇮🇹',
    'ES': '🇪🇸', 'Spain': '🇪🇸',
    'CH': '🇨🇭', 'Switzerland': '🇨🇭',
    'AT': '🇦🇹', 'Austria': '🇦🇹',
    'IE': '🇮🇪', 'Ireland': '🇮🇪',
    'CN': '🇨🇳', 'China': '🇨🇳',
    'AE': '🇦🇪', 'UAE': '🇦🇪', 'Dubai': '🇦🇪',
    'BR': '🇧🇷', 'Brazil': '🇧🇷',
}

# Регулярка для поиска эмоджи флагов
FLAG_EMOJI_RE = re.compile(r'[\U0001F1E0-\U0001F1FF]{2}')


def fetch_url(url, timeout=20):
    """Скачивает контент по URL"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[WARN] {url[:50]}...: {e}")
        return None


def decode_subscription(content):
    """
    Декодирует base64 подписку если нужно.
    Многие источники дают base64-закодированный список ключей.
    """
    content = content.strip()
    
    # Если уже есть ключи - не декодируем
    if any(p in content for p in PATTERNS):
        return content
    
    # Пробуем декодировать base64
    try:
        # Убираем переносы строк для base64
        clean = content.replace('\n', '').replace('\r', '').replace(' ', '')
        # Добавляем padding если нужно
        padding = len(clean) % 4
        if padding:
            clean += '=' * (4 - padding)
        decoded = base64.b64decode(clean).decode('utf-8', errors='ignore')
        # Проверяем что получились ключи
        if any(p in decoded for p in PATTERNS):
            return decoded
    except:
        pass
    
    return content


def extract_country_flag(uri):
    """
    Извлекает флаг страны из URI.
    Сначала ищет эмоджи флага, потом код страны в названии/адресе.
    """
    # Ищем существующий эмоджи флага
    flags = FLAG_EMOJI_RE.findall(uri)
    if flags:
        return flags[0]
    
    # Ищем код страны в URI
    uri_upper = uri.upper()
    for code, flag in COUNTRY_FLAGS.items():
        if code.upper() in uri_upper:
            return flag
    
    return '🌐'  # Глобус по умолчанию


def rename_key(uri, index):
    """
    Переименовывает ключ в формат: Underground Bro 🇺🇸 #123
    Удаляет старое название, добавляет наше.
    """
    flag = extract_country_flag(uri)
    new_name = f"Underground Bro {flag} #{index}"
    # URL-кодируем название
    encoded_name = urllib.parse.quote(new_name)
    # Отрезаем старое название (всё после #)
    base = uri.split('#')[0] if '#' in uri else uri
    return f"{base}#{encoded_name}"


def main():
    print(f"[INFO] Fetching from {len(SOURCES)} sources...")
    all_keys = []
    
    # Параллельно качаем все источники
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in SOURCES}
        
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                content = future.result()
                if content:
                    # Декодируем если это base64 подписка
                    decoded = decode_subscription(content)
                    # Извлекаем ключи
                    count = 0
                    for line in decoded.splitlines():
                        line = line.strip()
                        # Фиксим HTML entities
                        line = line.replace('&amp;', '&')
                        # Проверяем что это ключ
                        if line and any(line.startswith(p) for p in PATTERNS):
                            all_keys.append(line)
                            count += 1
                    print(f"[OK] {url[:50]}... -> {count} keys")
            except Exception as e:
                print(f"[ERR] {url[:50]}...: {e}")
    
    print(f"[INFO] Total keys collected: {len(all_keys)}")
    
    # Дедупликация по базовому URI (без названия)
    seen_bases = set()
    unique_keys = []
    for key in all_keys:
        base = key.split('#')[0]
        if base not in seen_bases:
            seen_bases.add(base)
            unique_keys.append(key)
    
    print(f"[INFO] Unique keys: {len(unique_keys)}")
    
    # Переименовываем все ключи в Underground Bro
    renamed_keys = []
    for i, key in enumerate(unique_keys, 1):
        renamed_keys.append(rename_key(key, i))
    
    # Сортируем по названию (по странам)
    renamed_keys.sort(key=lambda x: x.split('#')[-1] if '#' in x else '')
    
    # Записываем в файл
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'assets',
        'bundle.min.js'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for key in renamed_keys:
            f.write(key + '\n')
    
    print(f"[OK] Written {len(renamed_keys)} keys to {output_path}")
    print(f"[OK] Build complete!")


if __name__ == "__main__":
    main()
