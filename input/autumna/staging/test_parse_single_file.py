#!/usr/bin/env python3
"""
Упрощенный тестовый скрипт для парсинга одного Markdown файла
================================================================
Цель: Протестировать парсинг test1-md.md (требует OPENAI_API_KEY в переменных окружения)
"""

import os
import sys
import json
import openai
from typing import Dict

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
except ImportError:
    # python-dotenv not installed, will use environment variables directly
    pass

# Конфигурация
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-2024-08-06')

def clean_markdown(markdown_content: str):
    """
    Удалить нерелевантные секции из Markdown для экономии токенов
    
    Удаляет:
    - Cookies секцию
    - Рекомендации других домов
    - Футер Autumna
    
    Returns:
        (cleaned_content, removed_chars_count)
    """
    lines = markdown_content.split('\n')
    cleaned_lines = []
    removed_chars = 0
    
    skip_sections = [
        'Cookies on the Autumna Website',
        'Other Care Homes in the area',
        'The UK\'s largest & most detailed directory',
        'BESbswy'  # Конец страницы
    ]
    
    skip = False
    skip_start_line = None
    
    for i, line in enumerate(lines):
        # Проверить начало секции для пропуска
        should_skip = False
        for section in skip_sections:
            if section in line:
                should_skip = True
                skip_start_line = i
                break
        
        if should_skip:
            skip = True
            continue
        
        # Проверить конец секции пропуска (новый заголовок уровня 1-2 или конец файла)
        if skip:
            # Если это новый заголовок уровня 1-2 (не 3+), прекратить пропуск
            if line.startswith('#') and not line.startswith('###'):
                skip = False
            # Если это конец файла
            elif i == len(lines) - 1:
                skip = False
        
        if not skip:
            cleaned_lines.append(line)
        else:
            removed_chars += len(line) + 1  # +1 для символа новой строки
    
    cleaned_content = '\n'.join(cleaned_lines)
    return cleaned_content, removed_chars

def load_prompt_and_schema():
    """Загрузить промпт и JSON Schema"""
    prompt_file = "input/autumna/autumna_markdown_prompt_v26.md"
    schema_file = "input/autumna/response_format_v26_final.json"
    
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
    print("📚 Загрузка промпта и JSON Schema...")
    system_prompt, response_format = load_prompt_and_schema()
    
    # Прочитать Markdown файл
    print(f"📄 Чтение файла: {markdown_file}")
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    original_size = len(markdown_content)
    print(f"   Исходный размер: {original_size} символов (~{original_size // 4} токенов)")
    
    # Очистить нерелевантные секции
    markdown_content, removed_chars = clean_markdown(markdown_content)
    cleaned_size = len(markdown_content)
    savings_percent = (removed_chars / original_size * 100) if original_size > 0 else 0
    
    print(f"   После очистки: {cleaned_size} символов (~{cleaned_size // 4} токенов)")
    print(f"   Удалено: {removed_chars} символов ({savings_percent:.1f}%)")
    
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
        return {
            'success': False,
            'error': str(e),
            'data': None
        }

def extract_expected_data():
    """Извлечь ожидаемые данные из Markdown файла (ручной анализ)"""
    return {
        'name': 'Ladydale Care Home',
        'cqc_location_id': '1-145996910',  # Из URL в строке 78: https://www.cqc.org.uk/location/1-145996910/reports
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
        'year_registered': 2011  # "26th January 2011"
    }

def compare_results(parsed_data: Dict, expected_data: Dict):
    """Сравнить результаты парсинга с ожидаемыми данными"""
    print("\n" + "="*80)
    print("🔍 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
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
    markdown_file = "input/autumna/Data-MD/html 1 /test1-md.md"
    
    if not os.path.exists(markdown_file):
        print(f"❌ Файл не найден: {markdown_file}")
        sys.exit(1)
    
    # Парсинг
    print("="*80)
    print("🧪 ТЕСТИРОВАНИЕ ПАРСИНГА MARKDOWN ФАЙЛА")
    print("="*80)
    
    result = parse_markdown_file(markdown_file)
    
    if not result['success']:
        print(f"\n❌ Ошибка парсинга: {result.get('error')}")
        sys.exit(1)
    
    parsed_data = result['data']
    
    # Сохранить результат
    output_file = "input/autumna/Data-MD/html 1 /test1-parsed-result.json"
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
    print(f"   📊 Использовано токенов: {result['usage']['total_tokens']}")
    print(f"      - Промпт: {result['usage']['prompt_tokens']}")
    print(f"      - Ответ: {result['usage']['completion_tokens']}")
    
    # Анализ размера данных
    markdown_size = len(open(markdown_file, 'r', encoding='utf-8').read())
    print(f"\n📏 РАЗМЕР ДАННЫХ:")
    print(f"   Markdown файл: {markdown_size} символов (~{markdown_size // 4} токенов)")
    print(f"   Промпт: ~6,400 токенов")
    print(f"   Всего в запросе: ~{result['usage']['prompt_tokens']} токенов")
    print(f"   Использование контекста: {result['usage']['prompt_tokens'] / 128000 * 100:.2f}%")

if __name__ == '__main__':
    main()
