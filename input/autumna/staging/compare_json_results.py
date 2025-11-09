#!/usr/bin/env python3
"""
Скрипт для детального сравнения JSON результатов HTML и Markdown парсинга
"""

import json
import sys
from typing import Dict, Any, Set

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Рекурсивно развернуть вложенный словарь"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], dict):
                # Для списков объектов, добавить индекс
                for i, item in enumerate(v):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
            else:
                items.append((new_key, v))
        else:
            items.append((new_key, v))
    return dict(items)

def compare_json_files(html_file: str, md_file: str):
    """Сравнить два JSON файла"""
    print("="*80)
    print("🔍 ДЕТАЛЬНОЕ СРАВНЕНИЕ JSON РЕЗУЛЬТАТОВ")
    print("="*80)
    
    # Загрузить файлы
    print("\n📚 Загрузка файлов...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_data = json.load(f)
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_data = json.load(f)
    
    # Развернуть в плоские структуры
    html_flat = flatten_dict(html_data)
    md_flat = flatten_dict(md_data)
    
    # Найти все ключи
    all_keys = set(html_flat.keys()) | set(md_flat.keys())
    
    print(f"   HTML полей: {len(html_flat)}")
    print(f"   Markdown полей: {len(md_flat)}")
    print(f"   Всего уникальных полей: {len(all_keys)}")
    
    # Сравнить значения
    identical = []
    different = []
    html_only = []
    md_only = []
    
    for key in sorted(all_keys):
        html_val = html_flat.get(key)
        md_val = md_flat.get(key)
        
        if key not in html_flat:
            md_only.append((key, md_val))
        elif key not in md_flat:
            html_only.append((key, html_val))
        elif html_val == md_val:
            identical.append((key, html_val))
        else:
            different.append((key, html_val, md_val))
    
    # Вывести результаты
    print("\n" + "="*80)
    print("📊 СТАТИСТИКА СРАВНЕНИЯ")
    print("="*80)
    print(f"   ✅ Идентичных полей: {len(identical)} ({len(identical)/len(all_keys)*100:.1f}%)")
    print(f"   ⚠️  Различающихся полей: {len(different)} ({len(different)/len(all_keys)*100:.1f}%)")
    print(f"   📄 Только в HTML: {len(html_only)}")
    print(f"   📄 Только в Markdown: {len(md_only)}")
    
    # Показать различия
    if different:
        print("\n" + "="*80)
        print("⚠️  РАЗЛИЧАЮЩИЕСЯ ПОЛЯ")
        print("="*80)
        for key, html_val, md_val in different[:20]:  # Показать первые 20
            print(f"\n   Поле: {key}")
            print(f"   HTML:    {html_val}")
            print(f"   Markdown: {md_val}")
        
        if len(different) > 20:
            print(f"\n   ... и еще {len(different) - 20} полей")
    
    # Показать поля только в HTML
    if html_only:
        print("\n" + "="*80)
        print("📄 ПОЛЯ ТОЛЬКО В HTML")
        print("="*80)
        for key, val in html_only[:10]:
            print(f"   {key}: {val}")
        if len(html_only) > 10:
            print(f"   ... и еще {len(html_only) - 10} полей")
    
    # Показать поля только в Markdown
    if md_only:
        print("\n" + "="*80)
        print("📄 ПОЛЯ ТОЛЬКО В MARKDOWN")
        print("="*80)
        for key, val in md_only[:10]:
            print(f"   {key}: {val}")
        if len(md_only) > 10:
            print(f"   ... и еще {len(md_only) - 10} полей")
    
    # Ключевые поля для сравнения
    print("\n" + "="*80)
    print("🎯 КЛЮЧЕВЫЕ ПОЛЯ")
    print("="*80)
    
    key_fields = [
        'identity.name',
        'identity.cqc_location_id',
        'identity.provider_name',
        'location.city',
        'location.postcode',
        'care_services.care_residential',
        'care_services.care_respite',
        'capacity.beds_total',
        'cqc_ratings.cqc_rating_overall',
        'extraction_metadata.data_quality_score'
    ]
    
    for field in key_fields:
        html_val = html_flat.get(field, 'N/A')
        md_val = md_flat.get(field, 'N/A')
        status = "✅" if html_val == md_val else "⚠️"
        print(f"   {status} {field}:")
        print(f"      HTML: {html_val}")
        print(f"      MD:   {md_val}")
    
    # Сохранить детальный отчет
    report = {
        "statistics": {
            "total_fields": len(all_keys),
            "identical": len(identical),
            "different": len(different),
            "html_only": len(html_only),
            "md_only": len(md_only),
            "identical_percent": len(identical)/len(all_keys)*100 if all_keys else 0
        },
        "different_fields": [
            {"field": k, "html": str(v1), "markdown": str(v2)}
            for k, v1, v2 in different
        ],
        "html_only_fields": [
            {"field": k, "value": str(v)}
            for k, v in html_only
        ],
        "md_only_fields": [
            {"field": k, "value": str(v)}
            for k, v in md_only
        ]
    }
    
    with open("input/autumna/JSON_COMPARISON_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Детальный отчет сохранен в: input/autumna/JSON_COMPARISON_REPORT.json")
    
    return report

if __name__ == '__main__':
    html_file = "input/autumna/Data-MD/html 1 /test1-html-parsed-result.json"
    md_file = "input/autumna/Data-MD/html 1 /test1-parsed-result.json"
    
    compare_json_files(html_file, md_file)

