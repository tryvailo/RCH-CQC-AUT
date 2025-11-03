#!/usr/bin/env python3
"""
ФАЗА 2: Парсинг HTML через OpenAI LLM
================================================================
Цель: Извлечь структурированные данные из HTML с помощью ChatGPT

Использование:
    python phase2_parse_llm.py --prompt-version v2.4 --batch-size 25

Требования:
    - OpenAI API ключ в .env
    - PostgreSQL подключение настроено
    - HTML уже загружен в staging таблицу (Фаза 1)
"""

import os
import sys
import json
import time
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, Optional, List
import logging

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
OPENAI_MODEL = "gpt-4o-2024-08-06"
DEFAULT_BATCH_SIZE = 25
MAX_RETRIES = 3
RETRY_DELAY = 5


def get_db_connection():
    """Получить подключение к PostgreSQL"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'care_homes'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )


def load_prompt_and_schema(prompt_version: str) -> tuple:
    """Загрузить промпт и JSON Schema для указанной версии"""
    prompt_file = f"input/autumna/AUTUMNA_PARSING_PROMPT_v2_4.md"
    schema_file = f"input/autumna/response_format_v2_4.json"
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Промпт не найден: {prompt_file}")
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"JSON Schema не найден: {schema_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        response_format = json.load(f)
    
    return system_prompt, response_format


def parse_html_with_openai(client: OpenAI, html_content: str, system_prompt: str, response_format: dict) -> Dict:
    """Парсинг HTML через OpenAI API"""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this HTML page:\n\n{html_content}"}
            ],
            response_format={"type": "json_schema", "json_schema": response_format['json_schema']},
            temperature=0
        )
        
        parsed_data = json.loads(response.choices[0].message.content)
        return {
            'success': True,
            'data': parsed_data,
            'raw_response': response.model_dump_json()
        }
        
    except Exception as e:
        logger.error(f"Ошибка OpenAI API: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }


def extract_metadata(parsed_data: Dict) -> Dict:
    """Извлечь метаданные из parsed JSON"""
    extraction_meta = parsed_data.get('extraction_metadata', {})
    
    return {
        'extraction_confidence': extraction_meta.get('extraction_confidence', 'medium'),
        'data_quality_score': extraction_meta.get('data_quality_score'),
        'is_dormant': extraction_meta.get('is_dormant', False),
        'critical_fields_missing': extraction_meta.get('critical_fields_missing', []),
        'data_quality_notes': extraction_meta.get('data_quality_notes')
    }


def save_parsing_result(conn, staging_id: int, parsed_data: Dict, metadata: Dict, prompt_version: str):
    """Сохранить результат парсинга в staging таблицу"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE autumna_staging
            SET 
                parsed_json = %(parsed_json)s::jsonb,
                extraction_confidence = %(confidence)s,
                data_quality_score = %(quality_score)s,
                is_dormant = %(is_dormant)s,
                llm_model = %(model)s,
                llm_prompt_version = %(prompt_version)s,
                parsing_errors = %(errors)s::jsonb,
                needs_reparse = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(staging_id)s
        """, {
            'staging_id': staging_id,
            'parsed_json': json.dumps(parsed_data),
            'confidence': metadata['extraction_confidence'],
            'quality_score': metadata['data_quality_score'],
            'is_dormant': metadata['is_dormant'],
            'model': OPENAI_MODEL,
            'prompt_version': prompt_version,
            'errors': json.dumps({
                'critical_fields_missing': metadata['critical_fields_missing'],
                'data_quality_notes': metadata['data_quality_notes']
            })
        })
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении результата для ID {staging_id}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def get_unparsed_records(conn, batch_size: int, needs_reparse: bool = False) -> List[Dict]:
    """Получить записи без parsed_json"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if needs_reparse:
        cursor.execute("""
            SELECT id, html_content, source_url, cqc_location_id
            FROM autumna_staging
            WHERE html_content IS NOT NULL
              AND needs_reparse = TRUE
            ORDER BY created_at ASC
            LIMIT %(batch_size)s
        """, {'batch_size': batch_size})
    else:
        cursor.execute("""
            SELECT id, html_content, source_url, cqc_location_id
            FROM autumna_staging
            WHERE html_content IS NOT NULL
              AND parsed_json IS NULL
            ORDER BY created_at ASC
            LIMIT %(batch_size)s
        """, {'batch_size': batch_size})
    
    records = cursor.fetchall()
    cursor.close()
    return [dict(record) for record in records]


def process_batch(conn, client: OpenAI, records: List[Dict], system_prompt: str, response_format: dict, prompt_version: str):
    """Обработать батч записей"""
    success_count = 0
    error_count = 0
    
    for record in records:
        staging_id = record['id']
        url = record['source_url']
        html_content = record['html_content']
        
        logger.info(f"📄 Парсинг: {url} (ID: {staging_id})")
        
        # Парсинг через OpenAI
        result = parse_html_with_openai(client, html_content, system_prompt, response_format)
        
        if not result['success']:
            logger.error(f"❌ Ошибка парсинга {url}: {result.get('error')}")
            error_count += 1
            continue
        
        parsed_data = result['data']
        
        # Извлечь метаданные
        metadata = extract_metadata(parsed_data)
        
        # Сохранить результат
        if save_parsing_result(conn, staging_id, parsed_data, metadata, prompt_version):
            logger.info(f"✅ Успешно: {url} (quality: {metadata['data_quality_score']})")
            success_count += 1
        else:
            error_count += 1
        
        # Задержка между запросами (rate limiting)
        time.sleep(0.5)
    
    return success_count, error_count


def main():
    parser = argparse.ArgumentParser(description='Фаза 2: Парсинг HTML через OpenAI LLM')
    parser.add_argument('--prompt-version', default='v2.4', help='Версия промпта (например, v2.4)')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE, help='Размер батча')
    parser.add_argument('--reparse', action='store_true', help='Переобработать записи с needs_reparse=TRUE')
    parser.add_argument('--dry-run', action='store_true', help='Тестовый запуск без сохранения')
    
    args = parser.parse_args()
    
    # Проверить OpenAI API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("❌ OPENAI_API_KEY не найден в .env")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    # Загрузить промпт и schema
    logger.info(f"📚 Загрузка промпта и JSON Schema (версия: {args.prompt_version})...")
    try:
        system_prompt, response_format = load_prompt_and_schema(args.prompt_version)
        logger.info("   ✅ Загружено")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        sys.exit(1)
    
    # Подключиться к БД
    logger.info("🔌 Подключение к БД...")
    conn = get_db_connection()
    logger.info("   ✅ Подключено")
    
    total_success = 0
    total_errors = 0
    
    # Обработка батчами
    while True:
        # Получить следующий батч
        records = get_unparsed_records(conn, args.batch_size, needs_reparse=args.reparse)
        
        if not records:
            logger.info("✅ Все записи обработаны!")
            break
        
        logger.info(f"\n📦 Обработка батча из {len(records)} записей...")
        
        if args.dry_run:
            logger.info("🧪 DRY RUN - результаты не будут сохранены")
            for record in records:
                logger.info(f"  - {record['source_url']}")
            break
        
        # Обработать батч
        success, errors = process_batch(
            conn, client, records, system_prompt, response_format, args.prompt_version
        )
        
        total_success += success
        total_errors += errors
        
        logger.info(f"📊 Батч завершен: ✅ {success}, ❌ {errors}")
        
        # Если обработаны не все записи, продолжить
        if len(records) < args.batch_size:
            break
    
    conn.close()
    
    logger.info(f"\n✅ Завершено! Всего: ✅ {total_success}, ❌ {total_errors}")


if __name__ == '__main__':
    main()

