#!/usr/bin/env python3
"""
Сравнение результатов парсинга v2.5 vs v2.6
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
                for i, item in enumerate(v):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
            else:
                items.append((new_key, v))
        else:
            items.append((new_key, v))
    return dict(items)

def count_non_null_fields(data: Dict) -> Dict[str, int]:
    """Подсчитать заполненные поля"""
    flat = flatten_dict(data)
    total = len(flat)
    non_null = sum(1 for v in flat.values() if v is not None and v != [] and v != {})
    null = total - non_null
    
    return {
        'total': total,
        'non_null': non_null,
        'null': null,
        'coverage_percent': (non_null / total * 100) if total > 0 else 0
    }

def compare_results(v25_file: str, v26_file: str):
    """Сравнить результаты v2.5 и v2.6"""
    print("="*80)
    print("🔍 СРАВНЕНИЕ v2.5 vs v2.6")
    print("="*80)
    
    # Загрузить файлы
    print("\n📚 Загрузка результатов...")
    with open(v25_file, 'r', encoding='utf-8') as f:
        v25_data = json.load(f)
    
    with open(v26_file, 'r', encoding='utf-8') as f:
        v26_data = json.load(f)
    
    # Подсчитать поля
    v25_stats = count_non_null_fields(v25_data)
    v26_stats = count_non_null_fields(v26_data)
    
    print(f"\n📊 СТАТИСТИКА ПОЛЕЙ:")
    print(f"   v2.5: {v25_stats['non_null']}/{v25_stats['total']} заполнено ({v25_stats['coverage_percent']:.1f}%)")
    print(f"   v2.6: {v26_stats['non_null']}/{v26_stats['total']} заполнено ({v26_stats['coverage_percent']:.1f}%)")
    
    if v26_stats['non_null'] > v25_stats['non_null']:
        diff = v26_stats['non_null'] - v25_stats['non_null']
        print(f"   ✅ v2.6 извлек на {diff} полей больше (+{diff/v25_stats['non_null']*100:.1f}%)")
    elif v26_stats['non_null'] < v25_stats['non_null']:
        diff = v25_stats['non_null'] - v26_stats['non_null']
        print(f"   ⚠️  v2.6 извлек на {diff} полей меньше (-{diff/v25_stats['non_null']*100:.1f}%)")
    else:
        print(f"   ✅ Количество заполненных полей одинаково")
    
    # Сравнить значения
    v25_flat = flatten_dict(v25_data)
    v26_flat = flatten_dict(v26_data)
    
    all_keys = set(v25_flat.keys()) | set(v26_flat.keys())
    
    identical = []
    different = []
    v25_only = []
    v26_only = []
    
    for key in sorted(all_keys):
        v25_val = v25_flat.get(key)
        v26_val = v26_flat.get(key)
        
        if key not in v25_flat:
            v26_only.append((key, v26_val))
        elif key not in v26_flat:
            v25_only.append((key, v25_val))
        elif v25_val == v26_val:
            identical.append((key, v25_val))
        else:
            different.append((key, v25_val, v26_val))
    
    print(f"\n📈 СРАВНЕНИЕ ЗНАЧЕНИЙ:")
    print(f"   ✅ Идентичных: {len(identical)} ({len(identical)/len(all_keys)*100:.1f}%)")
    print(f"   ⚠️  Различающихся: {len(different)} ({len(different)/len(all_keys)*100:.1f}%)")
    print(f"   📄 Только в v2.5: {len(v25_only)}")
    print(f"   📄 Только в v2.6: {len(v26_only)}")
    
    # Ключевые поля
    print(f"\n🎯 КЛЮЧЕВЫЕ ПОЛЯ:")
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
        v25_val = v25_flat.get(field, 'N/A')
        v26_val = v26_flat.get(field, 'N/A')
        status = "✅" if v25_val == v26_val else "⚠️"
        print(f"   {status} {field}:")
        print(f"      v2.5: {v25_val}")
        print(f"      v2.6: {v26_val}")
    
    # Различия
    if different:
        print(f"\n⚠️  РАЗЛИЧАЮЩИЕСЯ ПОЛЯ (первые 10):")
        for key, v25_val, v26_val in different[:10]:
            print(f"\n   {key}:")
            print(f"      v2.5: {v25_val}")
            print(f"      v2.6: {v26_val}")
        if len(different) > 10:
            print(f"\n   ... и еще {len(different) - 10} полей")
    
    # Новые поля в v2.6
    if v26_only:
        print(f"\n🆕 НОВЫЕ ПОЛЯ В v2.6 (первые 10):")
        for key, val in v26_only[:10]:
            print(f"   {key}: {val}")
        if len(v26_only) > 10:
            print(f"   ... и еще {len(v26_only) - 10} полей")
    
    return {
        'v25_stats': v25_stats,
        'v26_stats': v26_stats,
        'identical': len(identical),
        'different': len(different),
        'v25_only': len(v25_only),
        'v26_only': len(v26_only)
    }

def compare_token_usage():
    """Сравнить использование токенов"""
    print("\n" + "="*80)
    print("📊 СРАВНЕНИЕ ИСПОЛЬЗОВАНИЯ ТОКЕНОВ")
    print("="*80)
    
    # Загрузить результаты парсинга для получения токенов
    try:
        with open("input/autumna/Data-MD/html 1 /test1-parsed-result.json", 'r', encoding='utf-8') as f:
            v25_data = json.load(f)
        
        # v2.5 использовало ~20,258 токенов (из предыдущего парсинга)
        v25_tokens = 20258  # Из предыдущего парсинга
        
        print(f"\n📈 v2.5 (из предыдущего парсинга):")
        print(f"   Всего токенов: {v25_tokens:,}")
        print(f"   Промпт: ~18,639")
        print(f"   Ответ: ~1,619")
        
        # Загрузить новый результат
        with open("input/autumna/Data-MD/html 1 /test1-v26-parsed-result.json", 'r', encoding='utf-8') as f:
            v26_result = json.load(f)
        
        # Если есть информация о токенах в метаданных
        if 'usage' in v26_result:
            v26_tokens = v26_result['usage']['total_tokens']
            v26_prompt = v26_result['usage']['prompt_tokens']
            v26_completion = v26_result['usage']['completion_tokens']
            
            print(f"\n📈 v2.6 (новый парсинг):")
            print(f"   Всего токенов: {v26_tokens:,}")
            print(f"   Промпт: {v26_prompt:,}")
            print(f"   Ответ: {v26_completion:,}")
            
            savings = v25_tokens - v26_tokens
            savings_percent = (savings / v25_tokens * 100) if v25_tokens > 0 else 0
            
            print(f"\n💰 ЭКОНОМИЯ:")
            print(f"   Токенов: {savings:,} ({savings_percent:.1f}%)")
            print(f"   Промпт: {18639 - v26_prompt:,} ({((18639 - v26_prompt) / 18639 * 100):.1f}%)")
            
            # Стоимость
            cost_v25 = v25_tokens * 2.50 / 1000000 + 1619 * 10 / 1000000
            cost_v26 = v26_tokens * 2.50 / 1000000 + v26_completion * 10 / 1000000
            cost_savings = cost_v25 - cost_v26
            cost_savings_percent = (cost_savings / cost_v25 * 100) if cost_v25 > 0 else 0
            
            print(f"\n💵 СТОИМОСТЬ (примерно):")
            print(f"   v2.5: ${cost_v25:.4f}")
            print(f"   v2.6: ${cost_v26:.4f}")
            print(f"   Экономия: ${cost_savings:.4f} ({cost_savings_percent:.1f}%)")
            
            return {
                'v25_tokens': v25_tokens,
                'v26_tokens': v26_tokens,
                'savings': savings,
                'savings_percent': savings_percent,
                'cost_savings': cost_savings,
                'cost_savings_percent': cost_savings_percent
            }
        else:
            print("\n⚠️  Информация о токенах не найдена в новом результате")
            return None
            
    except FileNotFoundError as e:
        print(f"\n⚠️  Файл не найден: {e}")
        return None

if __name__ == '__main__':
    v25_file = "input/autumna/Data-MD/html 1 /test1-parsed-result.json"
    v26_file = "input/autumna/Data-MD/html 1 /test1-v26-parsed-result.json"
    
    # Сравнить результаты
    comparison = compare_results(v25_file, v26_file)
    
    # Сравнить токены
    token_comparison = compare_token_usage()
    
    # Сохранить отчет
    report = {
        'field_comparison': comparison,
        'token_comparison': token_comparison
    }
    
    with open("input/autumna/V25_VS_V26_COMPARISON.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Отчет сохранен в: input/autumna/V25_VS_V26_COMPARISON.json")

