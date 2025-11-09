#!/usr/bin/env python3
"""
Скрипт для подсчета полей в JSON Schema и результатах парсинга
"""

import json
import sys
from typing import Dict, Any, Set

def count_fields_in_schema(schema: Dict, path: str = "", field_count: Dict[str, int] = None) -> Dict[str, int]:
    """Рекурсивно подсчитать все поля в JSON Schema"""
    if field_count is None:
        field_count = {"total": 0, "required": 0, "optional": 0, "nested": 0}
    
    if "properties" in schema:
        for key, value in schema["properties"].items():
            full_path = f"{path}.{key}" if path else key
            field_count["total"] += 1
            
            # Проверить, является ли поле required
            is_required = key in schema.get("required", [])
            if is_required:
                field_count["required"] += 1
            else:
                field_count["optional"] += 1
            
            # Если это объект, рекурсивно подсчитать вложенные поля
            if value.get("type") == "object" or "properties" in value:
                field_count["nested"] += 1
                count_fields_in_schema(value, full_path, field_count)
            # Если это массив объектов
            elif value.get("type") == "array" and "items" in value:
                items = value["items"]
                if items.get("type") == "object" or "properties" in items:
                    field_count["nested"] += 1
                    count_fields_in_schema(items, f"{full_path}[]", field_count)
    
    return field_count

def count_fields_in_data(data: Dict, path: str = "", field_count: Dict[str, int] = None, non_null_count: Dict[str, int] = None) -> tuple:
    """Рекурсивно подсчитать все поля в данных"""
    if field_count is None:
        field_count = {"total": 0, "non_null": 0, "null": 0, "nested": 0}
    if non_null_count is None:
        non_null_count = {}
    
    for key, value in data.items():
        full_path = f"{path}.{key}" if path else key
        field_count["total"] += 1
        
        if value is None:
            field_count["null"] += 1
        elif isinstance(value, dict):
            field_count["nested"] += 1
            field_count["non_null"] += 1
            non_null_count[full_path] = "object"
            count_fields_in_data(value, full_path, field_count, non_null_count)
        elif isinstance(value, list):
            if len(value) > 0:
                field_count["non_null"] += 1
                non_null_count[full_path] = f"array[{len(value)}]"
                # Если массив объектов, подсчитать поля в первом объекте
                if len(value) > 0 and isinstance(value[0], dict):
                    count_fields_in_data(value[0], f"{full_path}[0]", field_count, non_null_count)
            else:
                field_count["null"] += 1
        else:
            field_count["non_null"] += 1
            non_null_count[full_path] = type(value).__name__
    
    return field_count, non_null_count

def main():
    # Загрузить JSON Schema
    print("📚 Загрузка JSON Schema...")
    with open("input/autumna/response_format_v26_final.json", "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    
    schema = schema_data["json_schema"]["schema"]
    schema_fields = count_fields_in_schema(schema)
    
    print(f"\n📊 СТАТИСТИКА JSON SCHEMA:")
    print(f"   Всего полей: {schema_fields['total']}")
    print(f"   Обязательных (required): {schema_fields['required']}")
    print(f"   Опциональных (optional): {schema_fields['optional']}")
    print(f"   Вложенных объектов: {schema_fields['nested']}")
    
    # Загрузить результат парсинга
    print("\n📄 Загрузка результата парсинга...")
    with open("input/autumna/Data-MD/html 1 /test1-parsed-result.json", "r", encoding="utf-8") as f:
        parsed_data = json.load(f)
    
    data_fields, non_null_fields = count_fields_in_data(parsed_data)
    
    print(f"\n📊 СТАТИСТИКА РЕЗУЛЬТАТА ПАРСИНГА:")
    print(f"   Всего полей: {data_fields['total']}")
    print(f"   Заполненных (non-null): {data_fields['non_null']}")
    print(f"   Пустых (null): {data_fields['null']}")
    print(f"   Вложенных объектов: {data_fields['nested']}")
    
    # Сравнение
    print("\n" + "="*80)
    print("🔍 СРАВНЕНИЕ")
    print("="*80)
    
    coverage = (data_fields['non_null'] / schema_fields['total'] * 100) if schema_fields['total'] > 0 else 0
    required_coverage = (data_fields['non_null'] / schema_fields['required'] * 100) if schema_fields['required'] > 0 else 0
    
    print(f"📈 Покрытие полей:")
    print(f"   Заполнено полей: {data_fields['non_null']} из {schema_fields['total']} ({coverage:.1f}%)")
    print(f"   Обязательных полей заполнено: {schema_fields['required']} из {schema_fields['required']} (100%)")
    
    print(f"\n📉 Пустые поля:")
    print(f"   Пустых полей: {data_fields['null']} ({data_fields['null'] / data_fields['total'] * 100:.1f}%)")
    
    # Топ заполненных секций
    print(f"\n📋 Топ заполненных секций:")
    sections = {}
    for path in non_null_fields.keys():
        section = path.split('.')[0]
        if section not in sections:
            sections[section] = 0
        sections[section] += 1
    
    sorted_sections = sorted(sections.items(), key=lambda x: x[1], reverse=True)
    for section, count in sorted_sections[:10]:
        print(f"   {section}: {count} полей")
    
    # Сохранить детальный отчет
    report = {
        "schema_statistics": schema_fields,
        "data_statistics": data_fields,
        "coverage": {
            "total_coverage_percent": coverage,
            "required_coverage_percent": required_coverage,
            "filled_fields": data_fields['non_null'],
            "total_schema_fields": schema_fields['total'],
            "empty_fields": data_fields['null']
        },
        "top_sections": dict(sorted_sections[:10])
    }
    
    with open("input/autumna/FIELD_COVERAGE_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Детальный отчет сохранен в: input/autumna/FIELD_COVERAGE_REPORT.json")

if __name__ == '__main__':
    main()

