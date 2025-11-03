#!/usr/bin/env python3
"""
ФАЗА 1: Загрузка HTML из Firecrawl в staging таблицу
================================================================
Цель: Сохранить HTML всех страниц Autumna в staging таблицу один раз

Использование:
    python phase1_load_html.py --urls urls.txt --api-key FIRECRAWL_API_KEY

Требования:
    - Список URL в файле (по одному на строку)
    - Firecrawl API ключ
    - PostgreSQL подключение настроено в .env
"""

import os
import sys
import json
import time
import argparse
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import requests
from typing import List, Dict, Optional
import re

load_dotenv()

# Конфигурация
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"
BATCH_SIZE = 50  # Размер батча для Firecrawl
RETRY_DELAY = 5  # Секунд между попытками


def extract_cqc_id_from_url(url: str) -> Optional[str]:
    """Извлечь CQC Location ID из URL Autumna"""
    match = re.search(r'/1-(\d{10})', url)
    if match:
        return f"1-{match.group(1)}"
    return None


def get_db_connection():
    """Получить подключение к PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'care_homes'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )


def scrape_urls_with_firecrawl(urls: List[str], api_key: str) -> List[Dict]:
    """
    Отправить URLs в Firecrawl API для скрапинга
    
    Returns:
        List[Dict] с ключами: url, html_content, metadata, status
    """
    results = []
    
    # Firecrawl поддерживает batch запросы
    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i+BATCH_SIZE]
        print(f"📥 Обработка батча {i//BATCH_SIZE + 1}/{(len(urls)-1)//BATCH_SIZE + 1} ({len(batch)} URLs)...")
        
        try:
            # Отправить запрос в Firecrawl
            response = requests.post(
                f"{FIRECRAWL_API_URL}/batch",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "urls": batch,
                    "format": "html"
                },
                timeout=300  # 5 минут на батч
            )
            
            if response.status_code != 200:
                print(f"❌ Ошибка Firecrawl: {response.status_code} - {response.text}")
                # Добавить пустые результаты с ошибкой
                for url in batch:
                    results.append({
                        'url': url,
                        'html_content': None,
                        'metadata': {'status': 'error', 'error': response.text},
                        'status': 'error'
                    })
                continue
            
            data = response.json()
            
            # Обработать результаты
            for item in data.get('data', []):
                results.append({
                    'url': item.get('url', ''),
                    'html_content': item.get('content', ''),
                    'metadata': {
                        'status': item.get('status', 'unknown'),
                        'scraped_at': item.get('metadata', {}).get('timestamp', time.strftime('%Y-%m-%dT%H:%M:%SZ')),
                        'title': item.get('metadata', {}).get('title', ''),
                    },
                    'status': item.get('status', 'unknown')
                })
            
            # Задержка между батчами
            if i + BATCH_SIZE < len(urls):
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Ошибка при обработке батча: {e}")
            # Добавить пустые результаты с ошибкой
            for url in batch:
                results.append({
                    'url': url,
                    'html_content': None,
                    'metadata': {'status': 'error', 'error': str(e)},
                    'status': 'error'
                })
    
    return results


def save_to_staging(conn, results: List[Dict]):
    """Сохранить результаты в staging таблицу"""
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for result in results:
        url = result['url']
        cqc_id = extract_cqc_id_from_url(url)
        html_content = result.get('html_content')
        metadata = result.get('metadata', {})
        status = result.get('status', 'unknown')
        
        if not html_content:
            print(f"⚠️  Пропущено (нет HTML): {url}")
            error_count += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO autumna_staging (
                    source_url,
                    cqc_location_id,
                    scraped_at,
                    html_content,
                    firecrawl_metadata
                ) VALUES (
                    %(url)s,
                    %(cqc_id)s,
                    CURRENT_TIMESTAMP,
                    %(html_content)s,
                    %(metadata)s::jsonb
                )
                ON CONFLICT (source_url) DO UPDATE
                SET 
                    html_content = EXCLUDED.html_content,
                    firecrawl_metadata = EXCLUDED.firecrawl_metadata,
                    scraped_at = EXCLUDED.scraped_at,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, {
                'url': url,
                'cqc_id': cqc_id,
                'html_content': html_content,
                'metadata': json.dumps(metadata)
            })
            
            staging_id = cursor.fetchone()[0]
            success_count += 1
            print(f"✅ Сохранено: {url} (ID: {staging_id})")
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении {url}: {e}")
            error_count += 1
    
    conn.commit()
    cursor.close()
    
    print(f"\n📊 Статистика:")
    print(f"   ✅ Успешно: {success_count}")
    print(f"   ❌ Ошибки: {error_count}")
    print(f"   ⏭️  Пропущено: {skipped_count}")
    
    return success_count, error_count


def load_urls_from_file(filepath: str) -> List[str]:
    """Загрузить список URL из файла"""
    urls = []
    with open(filepath, 'r') as f:
        for line in f:
            url = line.strip()
            if url and url.startswith('http'):
                urls.append(url)
    return urls


def main():
    parser = argparse.ArgumentParser(description='Фаза 1: Загрузка HTML из Firecrawl в staging')
    parser.add_argument('--urls', required=True, help='Путь к файлу со списком URL')
    parser.add_argument('--api-key', required=True, help='Firecrawl API ключ')
    parser.add_argument('--dry-run', action='store_true', help='Тестовый запуск без сохранения')
    
    args = parser.parse_args()
    
    # Загрузить URLs
    print(f"📋 Загрузка URLs из {args.urls}...")
    urls = load_urls_from_file(args.urls)
    print(f"   Найдено {len(urls)} URLs")
    
    if args.dry_run:
        print("🧪 DRY RUN - URLs не будут отправлены в Firecrawl")
        print("\nПервые 5 URLs:")
        for url in urls[:5]:
            print(f"  - {url}")
        return
    
    # Подключиться к БД
    print("\n🔌 Подключение к БД...")
    conn = get_db_connection()
    print("   ✅ Подключено")
    
    # Скрапить через Firecrawl
    print("\n🚀 Запуск Firecrawl скрапинга...")
    results = scrape_urls_with_firecrawl(urls, args.api_key)
    
    # Сохранить в staging
    print("\n💾 Сохранение в staging таблицу...")
    success, errors = save_to_staging(conn, results)
    
    conn.close()
    
    print(f"\n✅ Завершено! Успешно: {success}, Ошибок: {errors}")


if __name__ == '__main__':
    main()

