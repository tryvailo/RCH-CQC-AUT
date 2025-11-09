#!/usr/bin/env python3
"""
ФАЗА 1: Загрузка Markdown из Firecrawl в staging таблицу
================================================================
Цель: Сохранить Markdown всех страниц Autumna в staging таблицу один раз

Использование:
    python phase1_load_html.py --urls urls.txt --api-key FIRECRAWL_API_KEY
    python phase1_load_html.py --urls urls.txt --api-key FIRECRAWL_API_KEY --api-version v2.5 --use-cache

Требования:
    - Список URL в файле (по одному на строку)
    - Firecrawl API ключ
    - PostgreSQL подключение настроено в .env

Firecrawl API v2.5:
    - 🚀 Использует новый semantic index (40% запросов обслуживаются мгновенно)
    - 🎯 Кастомный browser stack для максимального качества данных
    - 📦 Поддержка "as of now" или "as of last known good copy" через useCache
    - ⚡ Автоматическое определение способа рендеринга страницы
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
FIRECRAWL_BASE_URL = "https://api.firecrawl.dev"
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


def scrape_urls_with_firecrawl(
    urls: List[str], 
    api_key: str, 
    api_version: str = "v2.5",
    use_cache: bool = False
) -> List[Dict]:
    """
    Отправить URLs в Firecrawl API для скрапинга
    
    Args:
        urls: Список URL для скрапинга
        api_key: Firecrawl API ключ
        api_version: Версия API ("v1", "v2", "v2.5"). По умолчанию v2.5
        use_cache: Использовать semantic index cache (v2.5+) для ускорения и экономии
    
    Returns:
        List[Dict] с ключами: url, markdown_content, metadata, status
    """
    results = []
    
    # Определить endpoint в зависимости от версии
    if api_version.startswith("v2"):
        # v2.5 использует новый endpoint с semantic index
        endpoint = f"{FIRECRAWL_BASE_URL}/v2/scrape/batch"
    else:
        # v1 - старая версия для обратной совместимости
        endpoint = f"{FIRECRAWL_BASE_URL}/v1/scrape/batch"
    
    print(f"🌐 Используется Firecrawl API {api_version} (endpoint: {endpoint})")
    if use_cache and api_version.startswith("v2"):
        print("   ✅ Semantic index cache включен (экономия времени и средств)")
    
    # Firecrawl поддерживает batch запросы
    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i+BATCH_SIZE]
        print(f"📥 Обработка батча {i//BATCH_SIZE + 1}/{(len(urls)-1)//BATCH_SIZE + 1} ({len(batch)} URLs)...")
        
        try:
            # Подготовить payload в зависимости от версии API
            payload = {
                "urls": batch,
                "format": "markdown"  # Используем markdown вместо HTML для экономии токенов
            }
            
            # v2.5+ поддерживает дополнительные опции
            if api_version.startswith("v2"):
                payload.update({
                    "useCache": use_cache,  # Использовать semantic index для ускорения
                    # Другие опции v2.5 можно добавить здесь:
                    # "timeout": 60000,  # таймаут в миллисекундах
                    # "waitFor": 0,  # ожидание загрузки страницы
                })
            
            # Отправить запрос в Firecrawl
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=300  # 5 минут на батч
            )
            
            if response.status_code != 200:
                print(f"❌ Ошибка Firecrawl: {response.status_code} - {response.text}")
                # Добавить пустые результаты с ошибкой
                for url in batch:
                    results.append({
                        'url': url,
                        'markdown_content': None,
                        'metadata': {
                            'status': 'error', 
                            'error': response.text,
                            'api_version': api_version
                        },
                        'status': 'error'
                    })
                continue
            
            data = response.json()
            
            # Обработать результаты (структура ответа может отличаться в v2.5)
            results_data = data.get('data', data.get('results', []))
            
            for item in results_data:
                # v2.5 может возвращать данные в разных форматах
                # Приоритет: markdown > content > html (для обратной совместимости)
                content = item.get('markdown') or item.get('content') or item.get('html', '')
                
                results.append({
                    'url': item.get('url', ''),
                    'markdown_content': content,  # Сохраняем как markdown_content
                    'metadata': {
                        'status': item.get('status', 'success'),
                        'scraped_at': item.get('metadata', {}).get('timestamp', time.strftime('%Y-%m-%dT%H:%M:%SZ')),
                        'title': item.get('metadata', {}).get('title', ''),
                        'api_version': api_version,
                        'from_cache': item.get('metadata', {}).get('fromCache', False) if use_cache else None,
                        'source': item.get('metadata', {}).get('source', 'unknown'),  # v2.5 может указывать источник
                    },
                    'status': item.get('status', 'success')
                })
            
            # Задержка между батчами (меньше для v2.5 с cache)
            if i + BATCH_SIZE < len(urls):
                delay = 1 if (use_cache and api_version.startswith("v2")) else 2
                time.sleep(delay)
                
        except Exception as e:
            print(f"❌ Ошибка при обработке батча: {e}")
            # Добавить пустые результаты с ошибкой
            for url in batch:
                results.append({
                    'url': url,
                    'markdown_content': None,
                    'metadata': {
                        'status': 'error', 
                        'error': str(e),
                        'api_version': api_version
                    },
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
        markdown_content = result.get('markdown_content')
        metadata = result.get('metadata', {})
        status = result.get('status', 'unknown')
        
        if not markdown_content:
            print(f"⚠️  Пропущено (нет Markdown): {url}")
            error_count += 1
            continue
        
        try:
            cursor.execute("""
                INSERT INTO autumna_staging (
                    source_url,
                    cqc_location_id,
                    scraped_at,
                    markdown_content,
                    firecrawl_metadata
                ) VALUES (
                    %(url)s,
                    %(cqc_id)s,
                    CURRENT_TIMESTAMP,
                    %(markdown_content)s,
                    %(metadata)s::jsonb
                )
                ON CONFLICT (source_url) DO UPDATE
                SET 
                    markdown_content = EXCLUDED.markdown_content,
                    firecrawl_metadata = EXCLUDED.firecrawl_metadata,
                    scraped_at = EXCLUDED.scraped_at,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, {
                'url': url,
                'cqc_id': cqc_id,
                'markdown_content': markdown_content,
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
    parser = argparse.ArgumentParser(
        description='Фаза 1: Загрузка Markdown из Firecrawl в staging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Использовать v2.5 с semantic index cache (рекомендуется)
  python phase1_load_html.py --urls urls.txt --api-key $FIRECRAWL_API_KEY --api-version v2.5 --use-cache
  
  # Использовать v2.5 без cache (свежие данные)
  python phase1_load_html.py --urls urls.txt --api-key $FIRECRAWL_API_KEY --api-version v2.5
  
  # Использовать старую версию v1 (для обратной совместимости)
  python phase1_load_html.py --urls urls.txt --api-key $FIRECRAWL_API_KEY --api-version v1
        """
    )
    parser.add_argument('--urls', required=True, help='Путь к файлу со списком URL')
    parser.add_argument('--api-key', required=True, help='Firecrawl API ключ')
    parser.add_argument('--api-version', default='v2.5', choices=['v1', 'v2', 'v2.5'], 
                       help='Версия Firecrawl API (по умолчанию: v2.5)')
    parser.add_argument('--use-cache', action='store_true', 
                       help='Использовать semantic index cache (v2.5+). Ускоряет запросы и экономит средства')
    parser.add_argument('--dry-run', action='store_true', help='Тестовый запуск без сохранения')
    
    args = parser.parse_args()
    
    # Загрузить URLs
    print(f"📋 Загрузка URLs из {args.urls}...")
    urls = load_urls_from_file(args.urls)
    print(f"   Найдено {len(urls)} URLs")
    
    if args.dry_run:
        print("🧪 DRY RUN - URLs не будут отправлены в Firecrawl")
        print(f"\nКонфигурация:")
        print(f"  - API версия: {args.api_version}")
        print(f"  - Использовать cache: {args.use_cache}")
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
    results = scrape_urls_with_firecrawl(
        urls, 
        args.api_key, 
        api_version=args.api_version,
        use_cache=args.use_cache
    )
    
    # Сохранить в staging
    print("\n💾 Сохранение в staging таблицу...")
    success, errors = save_to_staging(conn, results)
    
    conn.close()
    
    print(f"\n✅ Завершено! Успешно: {success}, Ошибок: {errors}")
    
    # Показать статистику по cache (если использовался)
    if args.use_cache:
        cache_hits = sum(1 for r in results if r.get('metadata', {}).get('from_cache'))
        if cache_hits > 0:
            print(f"\n💡 Semantic index cache использован для {cache_hits} из {len(results)} запросов")


if __name__ == '__main__':
    main()

