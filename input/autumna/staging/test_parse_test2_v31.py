#!/usr/bin/env python3
"""
Парсинг test2.md с использованием версии 3.1 (NON-CQC fields only)
"""

import os
import sys
import json
import openai
from typing import Dict

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Конфигурация
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-2024-08-06')

def load_prompt_and_schema():
    """Загрузить промпт и JSON Schema версии 3.1"""
    prompt_file = "input/autumna/AUTUMNA_PARSING_PROMPT_v3_1_OPTIMIZED_NON_CQC.md"
    schema_file = "input/autumna/response_format_v3_1_optimized_non_cqc.json"
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Промпт не найден: {prompt_file}")
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"JSON Schema не найден: {schema_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        response_format = json.load(f)
    
    return system_prompt, response_format

def parse_markdown_file(markdown_file: str):
    """Парсинг Markdown файла через OpenAI API"""
    # Проверить API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения. Установите: export OPENAI_API_KEY=sk-...")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Загрузить промпт и schema
    print("📚 Загрузка промпта и JSON Schema v3.1...")
    system_prompt, response_format = load_prompt_and_schema()
    
    # Прочитать Markdown файл
    print(f"📄 Чтение файла: {markdown_file}")
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    original_size = len(markdown_content)
    print(f"   Исходный размер: {original_size} символов (~{original_size // 4} токенов)")
    
    # Парсинг через OpenAI
    print("\n🤖 Отправка запроса в OpenAI API...")
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this markdown page:\n\n{markdown_content}"}
            ],
            response_format={"type": "json_schema", "json_schema": response_format['json_schema']},
            temperature=0
        )
        
        parsed_data = json.loads(response.choices[0].message.content)
        
        # Информация об использовании токенов
        usage = response.usage
        print(f"\n📊 Использование токенов:")
        print(f"   Промпт: {usage.prompt_tokens}")
        print(f"   Ответ: {usage.completion_tokens}")
        print(f"   Всего: {usage.total_tokens}")
        
        return {
            'success': True,
            'data': parsed_data,
            'usage': {
                'prompt_tokens': usage.prompt_tokens,
                'completion_tokens': usage.completion_tokens,
                'total_tokens': usage.total_tokens
            },
            'raw_response': response.model_dump_json()
        }
        
    except Exception as e:
        print(f"❌ Ошибка OpenAI API: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'data': None
        }

def print_summary(parsed_data: Dict):
    """Вывести краткую сводку результатов парсинга"""
    print("\n" + "="*80)
    print("📋 КРАТКАЯ СВОДКА РЕЗУЛЬТАТОВ")
    print("="*80)
    
    # Identity
    identity = parsed_data.get('identity', {})
    print(f"\n🏠 ИДЕНТИФИКАЦИЯ:")
    print(f"   Название: {identity.get('name', 'N/A')}")
    print(f"   CQC Location ID: {identity.get('cqc_location_id', 'N/A')}")
    print(f"   Provider: {identity.get('provider_name', 'N/A')}")
    print(f"   Brand: {identity.get('brand_name', 'N/A')}")
    
    # Location
    location = parsed_data.get('location', {})
    print(f"\n📍 ЛОКАЦИЯ:")
    print(f"   Город: {location.get('city', 'N/A')}")
    print(f"   Почтовый индекс: {location.get('postcode', 'N/A')}")
    print(f"   Регион: {location.get('region', 'N/A')}")
    print(f"   Local Authority: {location.get('local_authority', 'N/A')}")
    
    # Pricing
    pricing = parsed_data.get('pricing', {})
    print(f"\n💰 ЦЕНООБРАЗОВАНИЕ:")
    if pricing.get('fee_residential_from'):
        print(f"   Residential: £{pricing.get('fee_residential_from')} - £{pricing.get('fee_residential_to', 'N/A')}")
    if pricing.get('fee_nursing_from'):
        print(f"   Nursing: £{pricing.get('fee_nursing_from')} - £{pricing.get('fee_nursing_to', 'N/A')}")
    if pricing.get('fee_dementia_from'):
        print(f"   Dementia: £{pricing.get('fee_dementia_from')} - £{pricing.get('fee_dementia_to', 'N/A')}")
    
    # Funding
    funding = parsed_data.get('funding', {})
    print(f"\n💳 ФИНАНСИРОВАНИЕ:")
    print(f"   Self-funding: {funding.get('accepts_self_funding', 'N/A')}")
    print(f"   Local Authority: {funding.get('accepts_local_authority', 'N/A')}")
    print(f"   NHS CHC: {funding.get('accepts_nhs_chc', 'N/A')}")
    
    # Availability
    capacity = parsed_data.get('capacity', {})
    print(f"\n🛏️  ДОСТУПНОСТЬ:")
    print(f"   Всего кроватей: {capacity.get('beds_total', 'N/A')}")
    print(f"   Доступно: {capacity.get('beds_available', 'N/A')}")
    print(f"   Есть доступность: {capacity.get('has_availability', 'N/A')}")
    print(f"   Статус: {capacity.get('availability_status', 'N/A')}")
    
    # Medical Specialisms
    medical = parsed_data.get('medical_specialisms', {})
    conditions = medical.get('conditions_list', [])
    print(f"\n🏥 МЕДИЦИНСКИЕ СПЕЦИАЛИЗАЦИИ:")
    print(f"   Всего условий: {len(conditions)}")
    if conditions:
        print(f"   Примеры: {', '.join(conditions[:5])}")
        if len(conditions) > 5:
            print(f"   ... и еще {len(conditions) - 5}")
    
    # Dietary Options
    dietary = parsed_data.get('dietary_options', {})
    special_diets = dietary.get('special_diets', {})
    print(f"\n🍽️  ДИЕТИЧЕСКИЕ ОПЦИИ:")
    available_diets = [k for k, v in special_diets.items() if v and k != 'other']
    print(f"   Доступно диет: {len(available_diets)}")
    if available_diets:
        print(f"   Примеры: {', '.join(available_diets[:5])}")
    
    # Extraction Metadata
    extraction_meta = parsed_data.get('extraction_metadata', {})
    print(f"\n📊 МЕТАДАННЫЕ ИЗВЛЕЧЕНИЯ:")
    print(f"   Уверенность: {extraction_meta.get('extraction_confidence', 'N/A')}")
    print(f"   Качество данных: {extraction_meta.get('data_quality_score', 'N/A')}/100")
    print(f"   Дом закрыт: {extraction_meta.get('is_dormant', False)}")
    
    # Schema version
    source_meta = parsed_data.get('source_metadata', {})
    print(f"\n📌 ВЕРСИЯ СХЕМЫ:")
    print(f"   Schema version: {source_meta.get('schema_version', 'N/A')}")
    print(f"   Source: {source_meta.get('source', 'N/A')}")

def main():
    markdown_file = "input/autumna/Data-MD/html 2/test2.md"
    
    if not os.path.exists(markdown_file):
        print(f"❌ Файл не найден: {markdown_file}")
        sys.exit(1)
    
    # Парсинг
    print("="*80)
    print("🧪 ПАРСИНГ TEST2.MD С ВЕРСИЕЙ 3.1 (NON-CQC FIELDS ONLY)")
    print("="*80)
    
    result = parse_markdown_file(markdown_file)
    
    if not result['success']:
        print(f"\n❌ Ошибка парсинга: {result.get('error')}")
        sys.exit(1)
    
    parsed_data = result['data']
    
    # Сохранить результат
    output_file = "input/autumna/Data-MD/html 2/test2-v31-parsed-result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результат сохранен в: {output_file}")
    
    # Вывести сводку
    print_summary(parsed_data)
    
    # Итоговая статистика
    print("\n" + "="*80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("="*80)
    print(f"   ✅ Успешный парсинг: Да")
    print(f"   📊 Использовано токенов: {result['usage']['total_tokens']}")
    print(f"      - Промпт: {result['usage']['prompt_tokens']}")
    print(f"      - Ответ: {result['usage']['completion_tokens']}")
    print(f"   💰 Примерная стоимость: ${result['usage']['total_tokens'] * 0.00001:.4f}")

if __name__ == '__main__':
    main()

