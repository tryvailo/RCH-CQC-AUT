#!/usr/bin/env python3
"""
Экспериментальный скрипт для парсинга HTML файла
================================================================
Цель: Сравнить парсинг HTML vs Markdown для одного и того же контента
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
    """Загрузить промпт и JSON Schema"""
    # Для HTML используем HTML промпт, если есть, иначе Markdown
    html_prompt_file = "input/autumna/autumna_html_prompt_v26.md"
    markdown_prompt_file = "input/autumna/autumna_markdown_prompt_v26.md"
    schema_file = "input/autumna/response_format_v26_final.json"
    
    # Использовать HTML промпт если есть, иначе Markdown
    if os.path.exists(html_prompt_file):
        prompt_file = html_prompt_file
    else:
        prompt_file = markdown_prompt_file
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Промпт не найден: {prompt_file}")
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"JSON Schema не найден: {schema_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        response_format = json.load(f)
    
    return system_prompt, response_format

def parse_html_file(html_file: str):
    """Парсинг HTML файла через OpenAI API"""
    # Проверить API ключ
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения. Установите: export OPENAI_API_KEY=sk-...")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Загрузить промпт и schema
    print("📚 Загрузка промпта и JSON Schema...")
    prompt_file, schema_file = load_prompt_and_schema()
    
    # Загрузить файлы
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        response_format = json.load(f)
    
    # Прочитать HTML файл
    print(f"📄 Чтение файла: {html_file}")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    original_size = len(html_content)
    print(f"   Исходный размер: {original_size} символов (~{original_size // 4} токенов)")
    
    # Адаптировать промпт для HTML (заменить упоминания Markdown на HTML)
    # Но промпт уже должен работать с любым форматом, так что просто добавим инструкцию
    html_system_prompt = system_prompt.replace(
        "Markdown→JSON extractor",
        "HTML→JSON extractor (experimental)"
    ).replace(
        "markdown-formatted page content",
        "HTML-formatted page content"
    )
    
    # Парсинг через OpenAI
    print("\n🤖 Отправка запроса в OpenAI API...")
    print("   ⚠️  ВНИМАНИЕ: HTML файл намного больше Markdown!")
    print(f"   Размер HTML: {original_size:,} символов (~{original_size // 4:,} токенов)")
    
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": html_system_prompt},
                {"role": "user", "content": f"Parse this HTML page:\n\n{html_content}"}
            ],
            response_format={"type": "json_schema", "json_schema": response_format['json_schema']},
            temperature=0
        )
        
        parsed_data = json.loads(response.choices[0].message.content)
        
        # Информация об использовании токенов
        usage = response.usage
        print(f"\n📊 Использование токенов:")
        print(f"   Промпт: {usage.prompt_tokens:,}")
        print(f"   Ответ: {usage.completion_tokens:,}")
        print(f"   Всего: {usage.total_tokens:,}")
        
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
        return {
            'success': False,
            'error': str(e),
            'data': None
        }

def extract_expected_data():
    """Извлечь ожидаемые данные (те же, что для Markdown)"""
    return {
        'name': 'Ladydale Care Home',
        'cqc_location_id': '1-145996910',
        'city': 'Leek',
        'postcode': 'ST13 5LF',
        'address': '9 Fynney Street, Leek, Staffordshire',
        'care_residential': True,
        'care_respite': True,
        'care_dementia': False,
        'care_nursing': False,
        'provider_name': 'Pearlcare',
        'local_authority': 'Staffordshire',
        'cqc_rating_overall': 'Good',
        'beds_total': 54,
        'year_registered': 2011
    }

def compare_results(parsed_data: Dict, expected_data: Dict):
    """Сравнить результаты парсинга с ожидаемыми данными"""
    print("\n" + "="*80)
    print("🔍 СРАВНЕНИЕ РЕЗУЛЬТАТОВ (HTML vs Ожидаемые)")
    print("="*80)
    
    errors = []
    warnings = []
    
    # Проверка обязательных полей
    identity = parsed_data.get('identity', {})
    location = parsed_data.get('location', {})
    
    # 1. name
    parsed_name = identity.get('name')
    expected_name = expected_data.get('name')
    if parsed_name != expected_name:
        errors.append(f"name: ожидалось '{expected_name}', получено '{parsed_name}'")
    else:
        print(f"✅ name: {parsed_name}")
    
    # 2. cqc_location_id
    parsed_cqc_id = identity.get('cqc_location_id')
    expected_cqc_id = expected_data.get('cqc_location_id')
    if parsed_cqc_id != expected_cqc_id:
        errors.append(f"cqc_location_id: ожидалось '{expected_cqc_id}', получено '{parsed_cqc_id}'")
    else:
        print(f"✅ cqc_location_id: {parsed_cqc_id}")
    
    # 3. city
    parsed_city = location.get('city')
    expected_city = expected_data.get('city')
    if parsed_city != expected_city:
        errors.append(f"city: ожидалось '{expected_city}', получено '{parsed_city}'")
    else:
        print(f"✅ city: {parsed_city}")
    
    # 4. postcode
    parsed_postcode = location.get('postcode')
    expected_postcode = expected_data.get('postcode')
    if parsed_postcode != expected_postcode:
        errors.append(f"postcode: ожидалось '{expected_postcode}', получено '{parsed_postcode}'")
    else:
        print(f"✅ postcode: {parsed_postcode}")
    
    # Проверка других полей
    care_services = parsed_data.get('care_services', {})
    
    # care_residential
    parsed_residential = care_services.get('care_residential')
    expected_residential = expected_data.get('care_residential')
    if parsed_residential != expected_residential:
        warnings.append(f"care_residential: ожидалось {expected_residential}, получено {parsed_residential}")
    else:
        print(f"✅ care_residential: {parsed_residential}")
    
    # care_respite
    parsed_respite = care_services.get('care_respite')
    expected_respite = expected_data.get('care_respite')
    if parsed_respite != expected_respite:
        warnings.append(f"care_respite: ожидалось {expected_respite}, получено {parsed_respite}")
    else:
        print(f"✅ care_respite: {parsed_respite}")
    
    # care_dementia
    parsed_dementia = care_services.get('care_dementia')
    expected_dementia = expected_data.get('care_dementia')
    if parsed_dementia != expected_dementia:
        warnings.append(f"care_dementia: ожидалось {expected_dementia}, получено {parsed_dementia}")
    else:
        print(f"✅ care_dementia: {parsed_dementia}")
    
    # provider_name
    parsed_provider = identity.get('provider_name')
    expected_provider = expected_data.get('provider_name')
    if parsed_provider != expected_provider:
        warnings.append(f"provider_name: ожидалось '{expected_provider}', получено '{parsed_provider}'")
    else:
        print(f"✅ provider_name: {parsed_provider}")
    
    # local_authority
    parsed_la = location.get('local_authority')
    expected_la = expected_data.get('local_authority')
    if parsed_la != expected_la:
        warnings.append(f"local_authority: ожидалось '{expected_la}', получено '{parsed_la}'")
    else:
        print(f"✅ local_authority: {parsed_la}")
    
    # beds_total
    capacity = parsed_data.get('capacity', {})
    parsed_beds = capacity.get('beds_total')
    expected_beds = expected_data.get('beds_total')
    if parsed_beds != expected_beds:
        warnings.append(f"beds_total: ожидалось {expected_beds}, получено {parsed_beds}")
    else:
        print(f"✅ beds_total: {parsed_beds}")
    
    # year_registered
    parsed_year_reg = capacity.get('year_registered')
    expected_year_reg = expected_data.get('year_registered')
    if parsed_year_reg != expected_year_reg:
        warnings.append(f"year_registered: ожидалось {expected_year_reg}, получено {parsed_year_reg}")
    else:
        print(f"✅ year_registered: {parsed_year_reg}")
    
    # CQC rating
    cqc_ratings = parsed_data.get('cqc_ratings', {})
    parsed_rating = cqc_ratings.get('cqc_rating_overall') or cqc_ratings.get('overall_rating')
    expected_rating = expected_data.get('cqc_rating_overall')
    if parsed_rating != expected_rating:
        warnings.append(f"cqc_rating_overall: ожидалось '{expected_rating}', получено '{parsed_rating}'")
    else:
        print(f"✅ cqc_rating_overall: {parsed_rating}")
    
    print("\n" + "="*80)
    if errors:
        print(f"❌ ОШИБКИ ({len(errors)}):")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Все обязательные поля извлечены правильно!")
    
    if warnings:
        print(f"\n⚠️  ПРЕДУПРЕЖДЕНИЯ ({len(warnings)}):")
        for warning in warnings:
            print(f"   - {warning}")
    else:
        print("\n✅ Все проверяемые поля извлечены правильно!")
    
    return {
        'errors': errors,
        'warnings': warnings,
        'total_errors': len(errors),
        'total_warnings': len(warnings)
    }

def main():
    html_file = "input/autumna/Data-MD/html 1 /test1-html.html"
    
    if not os.path.exists(html_file):
        print(f"❌ Файл не найден: {html_file}")
        sys.exit(1)
    
    # Парсинг
    print("="*80)
    print("🧪 ЭКСПЕРИМЕНТ: ПАРСИНГ HTML ФАЙЛА")
    print("="*80)
    print("Цель: Сравнить парсинг HTML vs Markdown")
    print()
    
    result = parse_html_file(html_file)
    
    if not result['success']:
        print(f"\n❌ Ошибка парсинга: {result.get('error')}")
        sys.exit(1)
    
    parsed_data = result['data']
    
    # Сохранить результат
    output_file = "input/autumna/Data-MD/html 1 /test1-html-parsed-result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Результат сохранен в: {output_file}")
    
    # Извлечь ожидаемые данные
    expected_data = extract_expected_data()
    
    # Сравнить результаты
    comparison = compare_results(parsed_data, expected_data)
    
    # Вывести метаданные извлечения
    extraction_meta = parsed_data.get('extraction_metadata', {})
    print("\n" + "="*80)
    print("📊 МЕТАДАННЫЕ ИЗВЛЕЧЕНИЯ")
    print("="*80)
    print(f"   extraction_confidence: {extraction_meta.get('extraction_confidence', 'N/A')}")
    print(f"   data_quality_score: {extraction_meta.get('data_quality_score', 'N/A')}")
    print(f"   is_dormant: {extraction_meta.get('is_dormant', False)}")
    
    # Итоговая статистика
    print("\n" + "="*80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("="*80)
    print(f"   ✅ Успешный парсинг: Да")
    print(f"   ❌ Ошибки: {comparison['total_errors']}")
    print(f"   ⚠️  Предупреждения: {comparison['total_warnings']}")
    print(f"   📊 Использовано токенов: {result['usage']['total_tokens']:,}")
    print(f"      - Промпт: {result['usage']['prompt_tokens']:,}")
    print(f"      - Ответ: {result['usage']['completion_tokens']:,}")
    
    # Анализ размера данных
    html_size = len(open(html_file, 'r', encoding='utf-8').read())
    print(f"\n📏 РАЗМЕР ДАННЫХ:")
    print(f"   HTML файл: {html_size:,} символов (~{html_size // 4:,} токенов)")
    print(f"   Промпт: ~6,400 токенов")
    print(f"   Всего в запросе: ~{result['usage']['prompt_tokens']:,} токенов")
    print(f"   Использование контекста: {result['usage']['prompt_tokens'] / 128000 * 100:.2f}%")
    
    print("\n" + "="*80)
    print("💡 СРАВНЕНИЕ HTML vs MARKDOWN:")
    print("="*80)
    print("   Markdown: ~10,062 символов (~2,515 токенов)")
    print(f"   HTML: {html_size:,} символов (~{html_size // 4:,} токенов)")
    print(f"   Разница: {html_size / 10062:.1f}x больше")
    print(f"   Токены HTML: ~{html_size // 4:,} vs Markdown: ~2,515")
    print(f"   Экономия Markdown: ~{(html_size // 4 - 2515) / (html_size // 4) * 100:.1f}%")

if __name__ == '__main__':
    main()

